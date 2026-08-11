"""SQLModel model registration for Whoosh indexing.

Provides a convenience wrapper that registers a SQLModel (which is also a
Pydantic ``BaseModel``) with the Whoosh-NG indexing machinery, mapping
field annotations and primary-key flags to Whoosh field types.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from .base import ModelIndex, TypeMapper
from .types import SearchOptions


def register_model(model: type) -> ModelIndex:
    """Register a SQLModel model and return a ModelIndex.

    Iterates over the model's fields (as exposed by SQLModel's
    ``model_fields``), extracts any embedded search metadata from
    ``json_schema_extra``, marks primary-key fields appropriately, and
    constructs a :class:`~whoosh_modern.models.base.ModelIndex` with a
    corresponding Whoosh :class:`~whoosh.fields.Schema`.

    Args:
        model: A :class:`sqlmodel.SQLModel` subclass to register.

    Returns:
        A :class:`~whoosh_modern.models.base.ModelIndex` wrapping the model
        with its auto-generated Whoosh schema.

    Raises:
        ImportError: If the ``sqlmodel`` package is not installed.
        TypeError: If ``model`` is not a subclass of
            :class:`sqlmodel.SQLModel`.
    """
    try:
        from sqlmodel import SQLModel  # pyright: ignore[reportMissingImports]
    except ImportError as exc:
        raise ImportError("sqlmodel is required for SQLModel integration") from exc

    if not issubclass(model, SQLModel):
        raise TypeError(f"{model} is not a SQLModel subclass")

    fields = {}
    for name, field_info in model.model_fields.items():
        options = SearchOptions()
        extra = getattr(field_info, "json_schema_extra", {}) or {}
        if isinstance(extra, dict):
            search_meta = extra.get("search", {})
            if isinstance(search_meta, dict):
                options = SearchOptions(**search_meta)
            elif isinstance(search_meta, SearchOptions):
                options = search_meta
        if getattr(field_info, "primary_key", False):
            options.id = True
            options.stored = True
            options.unique = True
        annotation = getattr(field_info, "annotation", None) or str
        fields[name] = TypeMapper.map(annotation, options)

    from whoosh.fields import Schema

    return ModelIndex(model, schema=Schema(**fields))
