"""Base module for Python model-to-Whoosh field mapping.

Provides TypeMapper (central registry mapping Python types to Whoosh field
types) and ModelIndex (automatic Schema construction from a Python model).

Author: dorel14
Version: 2.0.0
"""

from __future__ import annotations

import dataclasses
import datetime
import decimal
import enum
import inspect
from collections.abc import Callable, Sequence
from typing import Any, TypeVar, get_args, get_origin

from whoosh.fields import BOOLEAN, DATETIME, ID, KEYWORD, NUMERIC, STORED, TEXT, Schema

from ._protocols import HasFields
from .types import SearchField, SearchOptions

T = TypeVar("T")


def _unwrap_annotated(annotation: Any) -> tuple[Any, list[Any]]:
    """Return (base_type, metadata) from an Annotated type.

    Args:
        annotation: A type annotation, possibly wrapped in ``Annotated``.

    Returns:
        A tuple of (base_type, metadata_list).
    """
    origin = get_origin(annotation)
    if origin is not None:
        try:
            import typing

            if origin is typing.Annotated:
                annotated_args = get_args(annotation)
                return annotated_args[0], list(annotated_args[1:])
        except Exception:
            pass
    return annotation, []


def _is_list_like(annotation: Any) -> bool:
    """Check whether the annotation represents a list-like type.

    Args:
        annotation: A type annotation.

    Returns:
        True if the annotation is ``list``, ``tuple``, or ``Sequence``.
    """
    origin = get_origin(annotation)
    return origin is list or origin is tuple or origin is Sequence


def _extract_search_options(annotation: Any, default: SearchOptions) -> SearchOptions:
    """Extract SearchOptions from an Annotated type's metadata.

    Args:
        annotation: A type annotation, possibly wrapped in ``Annotated``.
        default: Default SearchOptions to return if no SearchField is found.

    Returns:
        SearchOptions extracted from metadata or the default.
    """
    _, metadata = _unwrap_annotated(annotation)
    for item in metadata:
        if isinstance(item, SearchField):
            return item.options
    return default


class TypeMapper:
    """Central registry mapping Python types to Whoosh field types."""

    _registry: dict[Any, Callable[[SearchOptions], Any]] = {}

    @classmethod
    def register(cls, py_type: Any, factory: Callable[[SearchOptions], Any]) -> None:
        """Register a Python type -> Whoosh field factory mapping.

        Args:
            py_type: Python type to map.
            factory: Function that takes SearchOptions and returns a Whoosh field type.
        """
        cls._registry[py_type] = factory

    @classmethod
    def map(cls, py_type: Any, options: SearchOptions) -> Any:
        """Map a Python type to a Whoosh field type.

        Args:
            py_type: Python type to map.
            options: SearchOptions associated with the field.

        Returns:
            A Whoosh field type instance (TEXT, NUMERIC, etc.).
        """
        if py_type in cls._registry:
            return cls._registry[py_type](options)
        origin = get_origin(py_type)
        if origin is not None:
            if _is_list_like(py_type):
                return KEYWORD(
                    stored=options.stored,
                    sortable=options.sortable,
                )
            if origin is dict:
                return STORED
        if isinstance(py_type, type) and issubclass(py_type, enum.Enum):
            return KEYWORD(stored=options.stored, sortable=options.sortable)
        if isinstance(py_type, type) and issubclass(py_type, datetime.datetime):
            return DATETIME(stored=options.stored, sortable=options.sortable)
        if isinstance(py_type, type) and issubclass(py_type, datetime.date):
            return DATETIME(stored=options.stored, sortable=options.sortable)
        if isinstance(py_type, type) and issubclass(py_type, decimal.Decimal):
            return NUMERIC(
                int,
                stored=options.stored,
                sortable=options.sortable,
                decimal_places=2,
            )
        if isinstance(py_type, type) and py_type is bytes:
            return KEYWORD(stored=options.stored, sortable=options.sortable)
        return STORED


def _default_mappings() -> None:
    """Register default Python-to-Whoosh type mappings."""
    TypeMapper.register(str, lambda opt: TEXT(stored=opt.stored, analyzer=opt.analyzer or None))
    TypeMapper.register(
        SearchField, lambda opt: TEXT(stored=opt.stored, analyzer=opt.analyzer or None)
    )
    TypeMapper.register(int, lambda opt: NUMERIC(int, stored=opt.stored, sortable=opt.sortable))
    TypeMapper.register(
        float,
        lambda opt: NUMERIC(float, stored=opt.stored, sortable=opt.sortable),  # pyright: ignore[reportArgumentType]
    )
    TypeMapper.register(bool, lambda opt: BOOLEAN(stored=opt.stored))
    TypeMapper.register(type(None), lambda opt: STORED)


_default_mappings()


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
