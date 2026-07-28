from __future__ import annotations

from .base import ModelIndex


def register_model(model: type) -> ModelIndex:
    """Register a dataclass model and return a ModelIndex."""
    return ModelIndex(model)
