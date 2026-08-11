"""Pydantic model registration for Whoosh indexing.

Provides a convenience wrapper that registers a Pydantic ``BaseModel``
subclass with the Whoosh-NG indexing machinery, mapping Pydantic field
annotations to Whoosh field types.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from .base import ModelIndex, TypeMapper
from .types import SearchOptions


def register_model(model: type) -> ModelIndex:
    """Register a Pydantic model and return a ModelIndex.

    Inspects each field declared on the Pydantic model, extracts any
    embedded search metadata (via a ``search`` attribute or within
    ``json_schema_extra``), and constructs a
    :class:`~whoosh_modern.models.base.ModelIndex` with a corresponding
    Whoosh :class:`~whoosh.fields.Schema`.

    Args:
        model: A Pydantic ``BaseModel`` subclass to register.

    Returns:
        A :class:`~whoosh_modern.models.base.ModelIndex` wrapping the model
        with its auto-generated Whoosh schema.

    Raises:
        ImportError: If the ``pydantic`` package is not installed.
        TypeError: If ``model`` is not a subclass of
            :class:`pydantic.BaseModel`.
    """
    try:
        from pydantic import BaseModel  # pyright: ignore[reportMissingImports]
    except ImportError as exc:
        raise ImportError("pydantic is required for Pydantic integration") from exc

    if not issubclass(model, BaseModel):
        raise TypeError(f"{model} is not a Pydantic BaseModel subclass")

    fields = {}
    for name, field_info in model.model_fields.items():
        options = SearchOptions()
        search_meta = getattr(field_info, "search", None)
        if search_meta is None:
            extra = getattr(field_info, "json_schema_extra", {}) or {}
            if isinstance(extra, dict):
                search_meta = extra.get("search", {})
        if isinstance(search_meta, dict):
            options = SearchOptions(**search_meta)
        elif isinstance(search_meta, SearchOptions):
            options = search_meta
        annotation = getattr(field_info, "annotation", None) or str
        fields[name] = TypeMapper.map(annotation, options)

    from whoosh.fields import Schema

    return ModelIndex(model, schema=Schema(**fields))
