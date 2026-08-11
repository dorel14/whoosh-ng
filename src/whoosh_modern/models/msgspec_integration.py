"""msgspec Struct model registration for Whoosh indexing.

Provides a convenience wrapper that registers a ``msgspec.Struct`` subclass
with the Whoosh-NG indexing machinery, introspecting msgspec struct fields
and their metadata to build a Whoosh :class:`~whoosh.fields.Schema`.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

import contextlib
from typing import Any

from .base import ModelIndex, TypeMapper
from .types import SearchOptions


def register_model(model: type) -> ModelIndex:
    """Register a msgspec Struct model and return a ModelIndex.

    Uses :func:`msgspec.structs.fields` to enumerate the struct's fields,
    extracts any per-field ``search`` metadata from the field's ``metadata``
    dictionary, maps each field's Python type to a Whoosh field type, and
    constructs a :class:`~whoosh_modern.models.base.ModelIndex` with a
    corresponding Whoosh :class:`~whoosh.fields.Schema`.

    Args:
        model: A ``msgspec.Struct`` subclass to register.

    Returns:
        A :class:`~whoosh_modern.models.base.ModelIndex` wrapping the model
        with its auto-generated Whoosh schema.

    Raises:
        ImportError: If the ``msgspec`` package is not installed.
        TypeError: If ``model`` is not a subclass of
            :class:`msgspec.Struct`.
    """
    try:
        import msgspec  # pyright: ignore[reportMissingImports]
    except ImportError as exc:
        raise ImportError("msgspec is required for Msgspec integration") from exc

    if not issubclass(model, msgspec.Struct):
        raise TypeError(f"{model} is not a msgspec.Struct subclass")

    fields: dict[str, Any] = {}
    struct_fields: tuple[Any, ...] = ()
    with contextlib.suppress(Exception):
        struct_fields = msgspec.structs.fields(model)

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
