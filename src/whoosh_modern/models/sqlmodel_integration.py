from __future__ import annotations

from .base import ModelIndex


def register_model(model: type) -> ModelIndex:
    """Register a SQLModel model and return a ModelIndex."""
    try:
        from sqlmodel import \
            SQLModel  # pyright: ignore[reportMissingImports,reportUnusedImport]; pyright: ignore[reportUnusedImport]
    except ImportError as exc:
        raise ImportError("sqlmodel is required for SQLModel integration") from exc
    return ModelIndex(model)
