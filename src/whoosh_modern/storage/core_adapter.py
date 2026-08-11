"""Adapter bridging core ``whoosh.filedb.filestore.Storage`` to ``SyncStorageProvider``.

Wraps any core storage backend (``FileStorage``, ``RamStorage``, …) so it can
be passed to moderne components (``SearchApplication``, ``HybridStorage``,
etc.) that expect a :class:`~whoosh.plugins.storage_base.SyncStorageProvider`.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from whoosh.plugins.storage_base import SyncStorageProvider

if TYPE_CHECKING:
    from whoosh.filedb.filestore import Storage


class CoreStorageAdapter(SyncStorageProvider):
    """Adapt a core ``whoosh`` storage to the moderne ``SyncStorageProvider`` API.

    The adapter translates the key-based ``SyncStorageProvider`` surface
    (``write``/``read``/``delete``/``exists``/``list_keys``) into the
    file-name-based core ``Storage`` API.

    Args:
        storage: A core :class:`whoosh.filedb.filestore.Storage` instance
            (e.g. ``FileStorage`` or ``RamStorage``).

    Example::

        from whoosh.filedb.filestore import FileStorage
        from whoosh_modern.storage import CoreStorageAdapter

        core_storage = FileStorage("indexdir")
        adapter = CoreStorageAdapter(core_storage)

        # Now usable as a SyncStorageProvider
        adapter.write("segment_1.dat", b"binary-data")
        data = adapter.read("segment_1.dat")
    """

    def __init__(self, storage: Storage) -> None:
        """Initialize the adapter with a core storage instance.

        Args:
            storage: The core storage object to wrap.
        """
        self._storage = storage

    def write(self, key: str, data: bytes) -> None:
        """Write *data* to the blob identified by *key*.

        Args:
            key: Blob key interpreted as a file name in the core storage.
            data: Raw bytes to persist.
        """
        fh = self._storage.create_file(key)
        try:
            fh.write(data)
        finally:
            fh.close()

    def read(self, key: str) -> bytes:
        """Read and return the blob identified by *key*.

        Args:
            key: Blob key interpreted as a file name in the core storage.

        Returns:
            The raw bytes stored under *key*.

        Raises:
            FileNotFoundError: If no blob exists at *key*.
        """
        fh = self._storage.open_file(key)
        try:
            return cast(bytes, fh.read())
        finally:
            fh.close()

    def delete(self, key: str) -> None:
        """Delete the blob identified by *key*.

        If the key does not exist, the call is a no-op.

        Args:
            key: Blob key interpreted as a file name in the core storage.
        """
        if self._storage.file_exists(key):
            self._storage.delete_file(key)

    def exists(self, key: str) -> bool:
        """Check whether a blob exists for *key*.

        Args:
            key: Blob key interpreted as a file name in the core storage.

        Returns:
            ``True`` if the blob exists, ``False`` otherwise.
        """
        return cast(bool, self._storage.file_exists(key))

    def list_keys(self) -> list[str]:
        """List all blob keys currently stored.

        Returns:
            A sorted list of file names present in the core storage.
        """
        return sorted(self._storage.list())


__all__ = ["CoreStorageAdapter"]
