from __future__ import annotations

from .base import ModelIndex


def register_model(model: type) -> ModelIndex:
    """Register a dataclass model and return a ModelIndex."""
    if not __import__("dataclasses").is_dataclass(model):
        raise TypeError(f"{model} is not a dataclass")
    return ModelIndex(model)
