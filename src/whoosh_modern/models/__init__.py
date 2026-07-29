from __future__ import annotations

from typing import Any

from .auto import AutoIndexer
from .base import ModelIndex, TypeMapper
from .dataclass_integration import register_model as register_dataclass_model
from .msgspec_integration import register_model as register_msgspec_model
from .pydantic_integration import register_model as register_pydantic_model
from .sqlalchemy_integration import register_model as register_sqlalchemy_model
from .sqlmodel_integration import register_model as register_sqlmodel_model
from .types import SearchField, SearchOptions

__all__ = [
    "AutoIndexer",
    "ModelIndex",
    "SearchField",
    "SearchOptions",
    "TypeMapper",
    "index_document",
    "register_dataclass_model",
    "register_msgspec_model",
    "register_pydantic_model",
    "register_sqlalchemy_model",
    "register_sqlmodel_model",
    "remove_document",
]


def index_document(index: Any, instance: Any, on_error: str = "raise") -> None:
    auto = AutoIndexer(index, on_error=on_error)
    auto.index(instance)


def remove_document(index: Any, instance: Any, on_error: str = "raise") -> None:
    auto = AutoIndexer(index, on_error=on_error)
    auto.remove(instance)
