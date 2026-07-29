from __future__ import annotations

from .base import ModelIndex, TypeMapper
from .types import SearchOptions


def register_model(model: type) -> ModelIndex:
    """Register a Pydantic model and return a ModelIndex."""
    try:
        from pydantic import BaseModel
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
