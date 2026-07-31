from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class HasFields(Protocol):
    """Protocol for models that expose field definitions."""

    model_fields: dict[str, Any]


@runtime_checkable
class HasInfo(Protocol):
    """Protocol for columns/fields that carry search metadata in .info."""

    info: dict[str, Any]
