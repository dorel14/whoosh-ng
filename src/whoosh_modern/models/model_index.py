"""Automatic Whoosh Schema construction from Python models.

This module provides :class:`ModelIndex`, which automatically maps a Python
model (dataclass, Pydantic, SQLAlchemy, or plain annotated class) to a
Whoosh Schema by inspecting its type annotations.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

import dataclasses
import enum
import inspect
from typing import Any

from whoosh.fields import ID, Schema

from ._protocols import HasFields
from .type_mapper import TypeMapper, _extract_search_options
from .types import SearchField, SearchOptions


def _get_annotations(model: type) -> dict[str, Any]:
    """Retrieve type annotations from a model class.

    Args:
        model: The model class to inspect.

    Returns:
        Dictionary of {field_name: type_annotation}.
    """
    try:
        return inspect.get_annotations(model, eval_str=True)
    except Exception:
        return {}


def _get_type_hints(model: type) -> dict[str, Any]:
    """Retrieve full type hints (including Annotated) from a model class.

    Args:
        model: The model class to inspect.

    Returns:
        Dictionary of {field_name: full_type_hint}.
    """
    try:
        import typing

        return typing.get_type_hints(model, include_extras=True)
    except Exception:
        return {}


class ModelIndex:
    """Automatically maps a Python model to a Whoosh Schema."""

    def __init__(self, model: type, schema: Schema | None = None) -> None:
        self.model = model
        self.schema = schema or self._build_schema()

    def _build_schema(self) -> Schema:
        """Build the Whoosh schema from the model's annotations.

        Supports dataclasses, Pydantic models (HasFields), SQLAlchemy models
        (with __mapper__), and plain classes with annotations.

        Returns:
            A Whoosh Schema with fields mapped from the model.
        """
        fields: dict[str, Any] = {}
        annotations: dict[str, Any] = {}
        model = self.model

        if dataclasses.is_dataclass(model):
            resolved = _get_type_hints(model)
            for f in dataclasses.fields(model):
                name = f.name
                py_type = resolved.get(name, f.type)
                if isinstance(py_type, str):
                    py_type = f.type
                options = _extract_search_options(py_type, SearchOptions())
                field_options = f.metadata.get("search", options)
                if not isinstance(field_options, SearchOptions):
                    field_options = options
                fields[name] = TypeMapper.map(py_type, field_options)
        elif isinstance(model, type) and isinstance(model, HasFields):
            for name, field_info in model.model_fields.items():
                options = getattr(field_info, "search", SearchOptions())
                if callable(options):
                    options = options()
                annotation = getattr(field_info, "annotation", None) or str
                fields[name] = TypeMapper.map(annotation, options)  # pyright: ignore[reportArgumentType]
        elif hasattr(model, "__mapper__"):
            mapper = model.__mapper__
            pk_columns = [c for c in mapper.primary_key]
            for column in mapper.columns:
                options = SearchOptions()
                if hasattr(column, "info") and isinstance(column.info, dict):
                    search_meta = column.info.get("search", {})
                    if isinstance(search_meta, dict):
                        options = SearchOptions(**search_meta)
                    elif isinstance(search_meta, SearchOptions):
                        options = search_meta
                if column in pk_columns:
                    options.id = True
                    options.stored = True
                    options.unique = True
                py_type = getattr(column.type, "python_type", str)
                fields[column.name] = TypeMapper.map(py_type, options)
        else:
            annotations = _get_annotations(model)
            for name, annotation in annotations.items():
                options = _extract_search_options(annotation, SearchOptions())
                attr = getattr(model, name, None)
                if isinstance(attr, SearchField):
                    options = attr.options
                fields[name] = TypeMapper.map(annotation, options)

        id_field = self._detect_id_field(
            fields,
            annotations
            if not dataclasses.is_dataclass(model)
            and not hasattr(model, "__mapper__")
            and not (isinstance(model, type) and isinstance(model, HasFields))
            else {},
        )
        if id_field:
            fields[id_field] = ID(stored=True, unique=True)

        return Schema(**fields)

    def _detect_id_field(self, fields: dict[str, Any], annotations: dict[str, Any]) -> str | None:
        """Detect the ID field in the model automatically.

        Looks for fields named ``id``, ``ID``, or ``_id``, then Whoosh ID
        fields, then any remaining string field.

        Args:
            fields: Dictionary of Whoosh fields built from the model.
            annotations: Dictionary of model annotations.

        Returns:
            The name of the ID field if found, otherwise None.
        """
        for name in annotations:
            if name in ("id", "ID", "_id"):
                return name
        for name, field in fields.items():
            whoosh_field = field
            if isinstance(whoosh_field, ID):
                return name
        for name in annotations:
            if annotations.get(name) is str and name not in fields:
                return name
        return None

    def to_whoosh_document(self, instance: Any) -> dict[str, Any]:
        """Convert a model instance to a Whoosh document dictionary.

        Handles dataclasses, Pydantic models, SQLAlchemy models, and plain
        objects with annotations.

        Args:
            instance: A model instance to convert.

        Returns:
            A dictionary suitable for ``writer.add_document(**doc)``.
        """
        if dataclasses.is_dataclass(instance):
            doc = {}
            for f in dataclasses.fields(instance):
                val = getattr(instance, f.name)
                if isinstance(val, enum.Enum):
                    val = val.value
                if isinstance(val, bytes):
                    val = val.hex()
                doc[f.name] = val
            return doc
        if isinstance(instance, HasFields):
            return {k: getattr(instance, k) for k in instance.model_fields}
        if hasattr(instance, "__mapper__"):
            doc = {}
            for column in instance.__mapper__.columns:
                val = getattr(instance, column.name, None)
                if val is not None:
                    doc[column.name] = val
            return doc
        return {k: getattr(instance, k) for k in _get_annotations(instance.__class__)}
