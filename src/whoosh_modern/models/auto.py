from __future__ import annotations

import asyncio
import logging
from typing import Any

from whoosh.fields import ID

from .base import ModelIndex

logger = logging.getLogger(__name__)


class AutoIndexer:
    """Dynamically indexes model instances into a Whoosh index."""

    def __init__(self, index: Any, on_error: str = "raise") -> None:
        self._index = index
        self.on_error = on_error
        self._registry: dict[type, ModelIndex] = {}
        self._listeners: dict[type, list[Any]] = {}

    def register(self, model: type) -> ModelIndex:
        model_index = ModelIndex(model)
        self._registry[model] = model_index
        if hasattr(model, "__mapper__"):
            self._attach_sqlalchemy_listeners(model)
        return model_index

    def _attach_sqlalchemy_listeners(self, model: type) -> None:
        try:
             from sqlalchemy import event as sa_event  # pyright: ignore[reportMissingImports]
        except ImportError:
            return

        auto = self

        def _after_insert(mapper: Any, connection: Any, target: Any) -> None:
            try:
                writer = auto._index.writer()
                writer.update_document(**auto._registry[type(target)].to_whoosh_document(target))
                writer.commit()
            except Exception as exc:
                auto._handle_error(exc)

        def _after_update(mapper: Any, connection: Any, target: Any) -> None:
            try:
                writer = auto._index.writer()
                writer.update_document(**auto._registry[type(target)].to_whoosh_document(target))
                writer.commit()
            except Exception as exc:
                auto._handle_error(exc)

        def _after_delete(mapper: Any, connection: Any, target: Any) -> None:
            try:
                model_index = auto._registry.get(type(target))
                if model_index is None:
                    return
                id_field = _find_id_field(model_index)
                if id_field is None:
                    return
                id_value = getattr(target, id_field, None)
                if id_value is None:
                    return
                writer = auto._index.writer()
                writer.delete_by_term(id_field, str(id_value))
                writer.commit()
            except Exception as exc:
                auto._handle_error(exc)

        sa_event.listen(model, "after_insert", _after_insert)
        sa_event.listen(model, "after_update", _after_update)
        sa_event.listen(model, "after_delete", _after_delete)
        self._listeners[model] = [_after_insert, _after_update, _after_delete]

    def _handle_error(self, exc: Exception) -> None:
        if self.on_error == "raise":
            raise
        if self.on_error == "log":
            logger.error("AutoIndexer error: %s", exc)
        if self.on_error == "skip":
            pass

    def index(self, instance: Any) -> None:
        model = type(instance)
        if model not in self._registry:
            raise ValueError(f"Model {model} not registered with AutoIndexer")
        doc = self._registry[model].to_whoosh_document(instance)
        writer = self._index.writer()
        writer.update_document(**doc)
        writer.commit()

    def remove(self, instance: Any) -> None:
        model = type(instance)
        if model not in self._registry:
            raise ValueError(f"Model {model} not registered with AutoIndexer")
        model_index = self._registry[model]
        id_field = _find_id_field(model_index)
        if id_field is None:
            raise ValueError(f"No ID field found for {model}")
        id_value = getattr(instance, id_field, None)
        if id_value is None:
            raise ValueError(f"ID value is None for {model}")
        writer = self._index.writer()
        writer.delete_by_term(id_field, str(id_value))
        writer.commit()

    async def index_async(self, instance: Any) -> None:
        await asyncio.to_thread(self.index, instance)

    async def remove_async(self, instance: Any) -> None:
        await asyncio.to_thread(self.remove, instance)


def _find_id_field(model_index: ModelIndex) -> str | None:
    for name, field in model_index.schema.items():
        if isinstance(field, ID):
            return str(name)
    return None
