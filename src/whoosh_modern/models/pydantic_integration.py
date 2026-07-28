from __future__ import annotations

from .base import ModelIndex


def register_model(model: type) -> ModelIndex:
    """Register a Pydantic model and return a ModelIndex."""
    try:
        from pydantic import \
            BaseModel  # pyright: ignore[reportMissingImports,reportUnusedImport]; pyright: ignore[reportUnusedImport]
    except ImportError as exc:
        raise ImportError("pydantic is required for Pydantic integration") from exc
    return ModelIndex(model)
