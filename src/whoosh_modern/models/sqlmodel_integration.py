from __future__ import annotations

from .base import ModelIndex, TypeMapper
from .types import SearchOptions


def register_model(model: type) -> ModelIndex:
    """Register a SQLModel model and return a ModelIndex."""
    try:
        from sqlmodel import SQLModel
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
