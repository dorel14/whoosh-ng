"""SQLAlchemy model registration for Whoosh indexing.

Provides a convenience wrapper that registers a SQLAlchemy declarative model
with the Whoosh-NG indexing machinery, introspecting columns via
``sqlalchemy.inspect`` and mapping their Python types to Whoosh field types.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any

from .base import ModelIndex, TypeMapper
from .types import SearchOptions


def register_model(model: type) -> ModelIndex:
    """Register a SQLAlchemy model and return a ModelIndex.

    Inspects the model's SQLAlchemy mapper to enumerate columns, extracts
    primary-key information and any per-column ``search`` metadata stored
    in ``column.info``, and constructs a
    :class:`~whoosh_modern.models.base.ModelIndex` with a corresponding
    Whoosh :class:`~whoosh.fields.Schema`.

    Args:
        model: A SQLAlchemy mapped class (must be inspectable via
            :func:`sqlalchemy.inspect` and yield a :class:`sqlalchemy.orm.Mapper`).

    Returns:
        A :class:`~whoosh_modern.models.base.ModelIndex` wrapping the model
        with its auto-generated Whoosh schema.

    Raises:
        ImportError: If the ``sqlalchemy`` package is not installed.
        ValueError: If ``model`` is not a SQLAlchemy mapped class.
    """
    try:
        from sqlalchemy import inspect as sa_inspect  # pyright: ignore[reportMissingImports]
        from sqlalchemy.orm import Mapper  # pyright: ignore[reportMissingImports]
    except ImportError as exc:
        raise ImportError("sqlalchemy is required for SQLAlchemy integration") from exc

    mapper: Any = sa_inspect(model)
    if not isinstance(mapper, Mapper):
        raise ValueError(f"{model} is not a SQLAlchemy mapped class")

    fields = {}
    pk_columns = {c.name for c in mapper.primary_key}
    for column in mapper.columns:
        options = SearchOptions()
        info = getattr(column, "info", {}) or {}
        if isinstance(info, dict):
            search_meta = info.get("search", {})
            if isinstance(search_meta, dict):
                options = SearchOptions(**search_meta)
            elif isinstance(search_meta, SearchOptions):
                options = search_meta
        if column.name in pk_columns:
            options.id = True
            options.stored = True
            options.unique = True
        py_type = getattr(column.type, "python_type", str)
        fields[column.name] = TypeMapper.map(py_type, options)

    from whoosh.fields import Schema

    return ModelIndex(model, schema=Schema(**fields))
