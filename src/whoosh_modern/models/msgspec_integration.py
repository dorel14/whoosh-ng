from __future__ import annotations

from typing import Any

from .base import ModelIndex, TypeMapper
from .types import SearchOptions


def register_model(model: type) -> ModelIndex:
    """Register a msgspec Struct model and return a ModelIndex."""
    try:
        import msgspec
    except ImportError as exc:
        raise ImportError("msgspec is required for Msgspec integration") from exc

    if not issubclass(model, msgspec.Struct):
        raise TypeError(f"{model} is not a msgspec.Struct subclass")

    fields: dict[str, Any] = {}
    struct_fields: tuple[Any, ...] = ()
    try:
        struct_fields = msgspec.structs.fields(model)
    except Exception:
        pass

    for field in struct_fields:
        options = SearchOptions()
        metadata = getattr(field, "metadata", {}) or {}
        if isinstance(metadata, dict):
            search_meta = metadata.get("search", {})
            if isinstance(search_meta, dict):
                options = SearchOptions(**search_meta)
            elif isinstance(search_meta, SearchOptions):
                options = search_meta
        fields[field.name] = TypeMapper.map(field.type, options)

    from whoosh.fields import Schema

    return ModelIndex(model, schema=Schema(**fields))
