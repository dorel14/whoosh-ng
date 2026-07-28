from __future__ import annotations

import dataclasses
from collections.abc import Callable
from typing import Any, TypeVar

from whoosh.fields import BOOLEAN, NUMERIC, STORED, TEXT, Schema

from ._protocols import HasFields
from .types import SearchField, SearchOptions

T = TypeVar("T")


class TypeMapper:
    """Central registry mapping Python types to Whoosh field types."""

    _registry: dict[Any, Callable[[Any], Any]] = {}

    @classmethod
    def register(cls, py_type: Any, factory: Callable[[Any], Any]) -> None:
        cls._registry[py_type] = factory

    @classmethod
    def map(cls, py_type: Any, options: SearchOptions) -> Any:
        if py_type in cls._registry:
            return cls._registry[py_type](options)
        return STORED


def _default_mappings() -> None:
    TypeMapper.register(
        str, lambda opt: TEXT(stored=opt.stored, analyzer=opt.analyzer or None)
    )
    TypeMapper.register(
        int, lambda opt: NUMERIC(int, stored=opt.stored, sortable=opt.sortable)
    )
    TypeMapper.register(
        float, lambda opt: NUMERIC(float, stored=opt.stored, sortable=opt.sortable)  # pyright: ignore[reportArgumentType]
    )
    TypeMapper.register(bool, lambda opt: BOOLEAN(stored=opt.stored))
    TypeMapper.register(type(None), lambda opt: STORED)


_default_mappings()


class ModelIndex:
    """Auto-maps a Python model to a Whoosh Schema."""

    def __init__(self, model: type, schema: Schema | None = None) -> None:
        self.model = model
        self.schema = schema or self._build_schema()

    def _build_schema(self) -> Schema:
        fields: dict[str, Any] = {}
        model = self.model

        if dataclasses.is_dataclass(model):
            for f in dataclasses.fields(model):
                options = f.metadata.get("search", SearchOptions())
                fields[f.name] = TypeMapper.map(f.type, options)
        elif isinstance(model, type) and isinstance(model, HasFields):
            for name, field_info in model.model_fields.items():
                options = getattr(field_info, "search", SearchOptions())
                fields[name] = TypeMapper.map(
                    field_info.annotation or str, options
                )
        else:
            for name, annotation in getattr(model, "__annotations__", {}).items():
                options = SearchOptions()
                attr = getattr(model, name, None)
                if isinstance(attr, SearchField):
                    options = attr.options
                fields[name] = TypeMapper.map(annotation, options)

        return Schema(**fields)

    def to_whoosh_document(self, instance: Any) -> dict[str, Any]:
        if dataclasses.is_dataclass(instance):
            return dataclasses.asdict(instance)  # type: ignore[arg-type]
        if isinstance(instance, HasFields):
            return {k: getattr(instance, k) for k in instance.model_fields}
        return {
            k: getattr(instance, k)
            for k in getattr(instance.__class__, "__annotations__", {})
        }