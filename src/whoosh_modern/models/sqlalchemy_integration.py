from __future__ import annotations

from typing import Any

from .base import ModelIndex, TypeMapper
from .types import SearchOptions


def register_model(model: type) -> ModelIndex:
    """Register a SQLAlchemy model and return a ModelIndex."""
    try:
        from sqlalchemy import inspect as sa_inspect
        from sqlalchemy.orm import Mapper
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
