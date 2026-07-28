from __future__ import annotations

from .base import ModelIndex


def register_model(model: type) -> ModelIndex:
    """Register a msgspec Struct model and return a ModelIndex."""
    try:
        import msgspec  # noqa: F401 # pyright: ignore[reportMissingImports,reportUnusedImport]
    except ImportError as exc:
        raise ImportError("msgspec is required for Msgspec integration") from exc
    return ModelIndex(model)
