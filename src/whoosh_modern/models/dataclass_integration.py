"""Dataclass model registration for Whoosh indexing.

Provides a thin convenience wrapper that registers a Python ``dataclass``
model with the Whoosh-NG indexing machinery.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from .base import ModelIndex


def register_model(model: type) -> ModelIndex:
    """Register a dataclass model and return a ModelIndex.

    Validates that the given class is a ``dataclass`` and constructs a
    :class:`~whoosh_modern.models.base.ModelIndex` from it, which builds
    the corresponding Whoosh :class:`~whoosh.fields.Schema`.

    Args:
        model: A Python dataclass type to register for indexing.

    Returns:
        A :class:`~whoosh_modern.models.base.ModelIndex` wrapping the model
        with its auto-generated Whoosh schema.

    Raises:
        TypeError: If ``model`` is not a dataclass.
    """
    if not __import__("dataclasses").is_dataclass(model):
        raise TypeError(f"{model} is not a dataclass")
    return ModelIndex(model)
