from __future__ import annotations

from typing import TYPE_CHECKING

from whoosh.backends.abc import Backend
from whoosh.filedb.filestore import FileStorage
from whoosh.index import EmptyIndexError, FileIndex

if TYPE_CHECKING:
    from whoosh.fields import Schema
    from whoosh.index import Index


class FileBackend(Backend):
    """File-system-based backend backed by :class:`~whoosh.filedb.FileStorage`.

    This is the default Whoosh backend. It stores each index as a
    directory containing binary segment and TOC files. It delegates
    directly to the existing :class:`~whoosh.index.FileIndex` class,
    so it is 100 % backward-compatible with existing code.

    Usage::

        from whoosh.backends.file import FileBackend
        backend = FileBackend("myindexdir")
        ix = backend.create(schema)
        ...
    """

    name = "file"

    def __init__(self, path: str, readonly: bool = False, supports_mmap: bool = True) -> None:
        self.path = path
        self.readonly = readonly
        self.supports_mmap = supports_mmap
        self._storage: FileStorage | None = None

    def __repr__(self) -> str:
        return f"FileBackend({self.path!r}, readonly={self.readonly})"

    async def startup(self) -> None:
        self._storage = FileStorage(
            self.path,
            supports_mmap=self.supports_mmap,
            readonly=self.readonly,
        )

    async def shutdown(self) -> None:
        if self._storage is not None:
            self._storage.close()
            self._storage = None

    # -- lazy storage accessor (works before startup() too) --------------

    def _get_storage(self) -> FileStorage:
        if self._storage is None:
            # Fallback for synchronous code paths that skip startup().
            self._storage = FileStorage(
                self.path,
                supports_mmap=self.supports_mmap,
                readonly=self.readonly,
            )
        return self._storage

    # -- index CRUD -------------------------------------------------------

    def create(self, schema: Schema) -> Index:
        storage = self._get_storage()
        storage.create()
        return FileIndex.create(storage, schema)

    def open(self, schema: Schema | None = None) -> Index:
        storage = self._get_storage()
        if not storage.index_exists():
            raise EmptyIndexError(f"No Whoosh index found at {self.path!r}")
        return FileIndex(storage, schema=schema)

    def exists(self) -> bool:
        return self._get_storage().index_exists()

    def destroy(self) -> None:
        storage = self._get_storage()
        storage.destroy()
        self._storage = None
