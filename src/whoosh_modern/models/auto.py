"""Automatic model indexing into Whoosh.

Provides the ``AutoIndexer`` class that dynamically indexes model instances
into a Whoosh index, with optional SQLAlchemy event listeners for real-time
synchronization.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from whoosh.fields import ID

from .base import ModelIndex

logger = logging.getLogger(__name__)


class AutoIndexer:
    """Dynamically indexes model instances into a Whoosh index.

    The :class:`AutoIndexer` maintains an internal registry that maps each
    registered model class to its :class:`~whoosh_modern.models.base.ModelIndex`.
    Once a model is registered, instances can be indexed, removed, or kept in
    sync automatically when using an ORM that emits SQLAlchemy-style events
    (e.g. SQLAlchemy declarative models).

    Attributes:
        on_error: Error-handling strategy. One of ``"raise"``, ``"log"``,
            or ``"skip"``.
    """

    def __init__(self, index: Any, on_error: str = "raise") -> None:
        """Initialize the AutoIndexer.

        Args:
            index: A Whoosh index instance (typically created via
                :func:`whoosh.index.create_in` or ``open_dir``).
            on_error: Strategy for handling errors during indexing operations.
                ``"raise"`` re-raises the exception, ``"log"`` logs it at
                ``ERROR`` level, and ``"skip"`` silently ignores it.

        Raises:
            ValueError: If ``on_error`` is not one of the supported values
                (validation is deferred to operation time).
        """
        self._index = index
        self.on_error = on_error
        self._registry: dict[type, ModelIndex] = {}
        self._listeners: dict[type, list[Any]] = {}

    def register(self, model: type) -> ModelIndex:
        """Register a model class for automatic indexing.

        Creates a :class:`~whoosh_modern.models.base.ModelIndex` from the
        given model and stores it in the internal registry. If the model
        carries a SQLAlchemy ``__mapper__`` attribute, event listeners are
        attached to keep the index in sync on insert, update, and delete.

        Args:
            model: The model class to register. Must be a plain class,
                dataclass, Pydantic model, SQLAlchemy mapped class, or
                any class that :class:`~whoosh_modern.models.base.ModelIndex`
                can introspect.

        Returns:
            The :class:`~whoosh_modern.models.base.ModelIndex` created for
            the model.
        """
        model_index = ModelIndex(model)
        self._registry[model] = model_index
        if hasattr(model, "__mapper__"):
            self._attach_sqlalchemy_listeners(model)
        return model_index

    def _attach_sqlalchemy_listeners(self, model: type) -> None:
        """Attach SQLAlchemy ORM event listeners to a model.

        Registers ``after_insert``, ``after_update``, and ``after_delete``
        listeners that automatically update or remove documents in the Whoosh
        index. If SQLAlchemy is not installed, this method is a no-op.

        Args:
            model: The SQLAlchemy mapped class to observe.
        """
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
        """Handle an exception according to the configured error strategy.

        Args:
            exc: The exception raised during an indexing operation.
        """
        if self.on_error == "raise":
            raise
        if self.on_error == "log":
            logger.error("AutoIndexer error: %s", exc)
        if self.on_error == "skip":
            pass

    def index(self, instance: Any) -> None:
        """Index a single model instance into the Whoosh index.

        The instance's model class must have been previously registered via
        :meth:`register`. The instance is converted to a Whoosh document and
        added (or replaced) in the index using ``update_document``.

        Args:
            instance: A model instance to index. Its type must be registered.

        Raises:
            ValueError: If the instance's model class is not registered.
        """
        model = type(instance)
        if model not in self._registry:
            raise ValueError(f"Model {model} not registered with AutoIndexer")
        doc = self._registry[model].to_whoosh_document(instance)
        writer = self._index.writer()
        writer.update_document(**doc)
        writer.commit()

    def remove(self, instance: Any) -> None:
        """Remove a model instance from the Whoosh index.

        The document identified by the instance's ID field is deleted from
        the index. Both the model class must be registered and the ID field
        must be discoverable.

        Args:
            instance: A model instance to remove from the index.

        Raises:
            ValueError: If the model is not registered, no ID field can be
                found, or the ID value is ``None``.
        """
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
        """Asynchronously index a model instance.

        Delegates to :meth:`index` in a background thread so the event loop
        is not blocked.

        Args:
            instance: A model instance to index. Its type must be registered.

        Raises:
            ValueError: If the instance's model class is not registered.
        """
        await asyncio.to_thread(self.index, instance)

    async def remove_async(self, instance: Any) -> None:
        """Asynchronously remove a model instance from the index.

        Delegates to :meth:`remove` in a background thread so the event loop
        is not blocked.

        Args:
            instance: A model instance to remove from the index.

        Raises:
            ValueError: If the model is not registered, no ID field can be
                found, or the ID value is ``None``.
        """
        await asyncio.to_thread(self.remove, instance)


def _find_id_field(model_index: ModelIndex) -> str | None:
    """Find the Whoosh ``ID`` field name in a model's schema.

    Iterates over the schema and returns the name of the first field whose
    type is :class:`whoosh.fields.ID`.

    Args:
        model_index: The :class:`~whoosh_modern.models.base.ModelIndex` whose
            schema to search.

    Returns:
        The name of the first ``ID`` field found, or ``None`` if no such
        field exists in the schema.
    """
    for name, field in model_index.schema.items():
        if isinstance(field, ID):
            return str(name)
    return None
