from __future__ import annotations

from .base import ModelIndex


def register_model(model: type) -> ModelIndex:
    """Register a SQLAlchemy model and return a ModelIndex."""
    try:
        from sqlalchemy.orm import \
            DeclarativeBase  # pyright: ignore[reportMissingImports,reportUnusedImport]; pyright: ignore[reportUnusedImport]
    except ImportError as exc:
        raise ImportError("sqlalchemy is required for SQLAlchemy integration") from exc
    return ModelIndex(model)
