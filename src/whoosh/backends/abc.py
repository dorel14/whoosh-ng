from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from whoosh.fields import Schema
    from whoosh.index import Index
    from whoosh.middleware.base import Middleware


class Backend(ABC):
    """Abstract base class for Whoosh storage+search backends.

    A backend owns the lifecycle of an index: creation, opening,
    writing, reading, searching, optimizing, and teardown. The concrete
    implementation decides where data lives (filesystem, SQLite, …)
    and how full-text search is performed (Whoosh own codec, FTS5, …).

    Context-manager friendly::

        async with backend:
            ix = backend.create(schema)
            w = ix.writer()
            ...
    """

    #: Sub-classes must expose the name used in the registry.
    name: str = ""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

    # -- lifecycle -------------------------------------------------------

    async def startup(self) -> None:
        """Called once before the backend is used. Override to allocate
        connection pools, run migrations, etc."""
        return None

    async def shutdown(self) -> None:
        """Called once when the backend is being torn down. Override to
        close connections, release locks, etc."""
        return None

    # -- index CRUD -------------------------------------------------------

    @abstractmethod
    def create(self, schema: Schema) -> Index:
        """Create a brand-new empty index and return an :class:`Index`."""

    @abstractmethod
    def open(self, schema: Schema | None = None) -> Index:
        """Open an existing index and return an :class:`Index`.

        :param schema: if given, override the stored schema.
        :raises EmptyIndexError: if the index does not exist or is empty.
        """

    @abstractmethod
    def exists(self) -> bool:
        """Return ``True`` if a non-empty index exists at the configured
        location."""

    def destroy(self) -> None:
        """Remove the index and any associated resources. Default
        implementation raises :exc:`NotImplementedError`."""
        raise NotImplementedError
