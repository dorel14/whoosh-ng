from __future__ import annotations

from typing import TYPE_CHECKING, Any

from whoosh.backends.abc import Backend
from whoosh.index import EmptyIndexError, FileIndex
from whoosh.filedb.filestore import FileStorage

if TYPE_CHECKING:
    from whoosh.fields import Schema
    from whoosh.index import Index


class LmdbBackend(Backend):
    """LMDB-backed storage backend.

    This backend stores index data in an LMDB environment. It is intentionally
    minimal: it reuses the existing Whoosh ``FileStorage``/``FileIndex`` stack
    by keeping a filesystem directory inside the LMDB-managed location, so it
    remains compatible with the rest of the codec/reading pipeline without
    reimplementing segment management here.

    Usage::

        from whoosh.backends.lmdb import LmdbBackend
        backend = LmdbBackend("myindexdir")
        ix = backend.create(schema)
        ...
    """

    name = "lmdb"

    def __init__(self, path: str, readonly: bool = False, map_size: int = 1 << 30) -> None:
        self.path = path
        self.readonly = readonly
        self.map_size = map_size
        self._storage: FileStorage | None = None
        self._env: Any = None

    def __repr__(self) -> str:
        return f"LmdbBackend({self.path!r}, readonly={self.readonly})"

    async def startup(self) -> None:
        try:
            import lmdb  # type: ignore[import-untyped]
        except ImportError as exc:
            raise RuntimeError(
                "lmdb backend requires the 'lmdb' package. "
                "Install it with: pip install lmdb"
            ) from exc

        self._env = lmdb.open(
            self.path,
            map_size=self.map_size,
            readonly=self.readonly,
            lock=not self.readonly,
            max_dbs=16,
        )
        self._storage = FileStorage(
            self.path,
            supports_mmap=False,
            readonly=self.readonly,
        )

    async def shutdown(self) -> None:
        if self._storage is not None:
            self._storage.close()
            self._storage = None
        if self._env is not None:
            self._env.close()
            self._env = None

    def _get_storage(self) -> FileStorage:
        if self._storage is None:
            self._storage = FileStorage(
                self.path,
                supports_mmap=False,
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
