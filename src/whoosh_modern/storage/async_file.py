"""Async filesystem storage provider bridging SyncStorageProvider via to_thread.

This module provides :class:`AsyncFileStorage`, an :class:`AsyncStorageProvider`
that delegates all filesystem I/O to a core
:class:`~whoosh_modern.middleware.storage.FileStorageProvider` running on a
worker thread through :func:`asyncio.to_thread`, keeping the event loop
unblocked. This removes the previous hand-rolled copy of the filesystem logic.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

import asyncio
import os

from whoosh.plugins.storage_base import AsyncStorageProvider
from whoosh_modern.middleware.storage import FileStorageProvider


class AsyncFileStorage(AsyncStorageProvider):
    """Async filesystem storage provider backed by the local OS filesystem.

    All read/write/delete/list operations are dispatched to a worker thread via
    ``asyncio.to_thread`` so the event loop is never blocked by disk I/O. The
    underlying work is performed by a core
    :class:`~whoosh_modern.middleware.storage.FileStorageProvider`.

    The provider is instantiated from a project root ``root`` directory; each
    logical key is resolved to a physical path under that root by the wrapped
    provider. Parent directories are created automatically on write.

    Example::

        from whoosh_modern.storage.async_file import AsyncFileStorage

        storage = AsyncFileStorage(root="./index_segments")
        await storage.awrite("segment_1.dat", b"binary-data")
        data = await storage.aread("segment_1.dat")
    """

    def __init__(self, root: str) -> None:
        """Initialize the async file storage provider.

        Args:
            root: Path to the directory used as the storage root. The path is
                resolved to an absolute path by the wrapped
                :class:`FileStorageProvider`.

        Raises:
            OSError: If ``root`` cannot be converted to an absolute path
                (propagated from :func:`os.path.abspath`).
        """
        self._root = os.path.abspath(root)
        self._provider = FileStorageProvider(root)

    async def awrite(self, key: str, data: bytes) -> None:
        """Asynchronously write ``data`` to ``key``.

        Args:
            key: Logical key under the storage root.
            data: Binary payload to persist.
        """
        await asyncio.to_thread(self._provider.write, key, data)

    async def aread(self, key: str) -> bytes:
        """Asynchronously read the full binary content stored at ``key``.

        Args:
            key: Logical key to read.

        Returns:
            The complete byte payload stored under ``key``.

        Raises:
            FileNotFoundError: If ``key`` does not exist on disk.
        """
        return await asyncio.to_thread(self._provider.read, key)

    async def adelete(self, key: str) -> None:
        """Asynchronously delete the file stored at ``key``.

        If the key does not exist, the call is a no-op.

        Args:
            key: Logical key to delete.
        """
        await asyncio.to_thread(self._provider.delete, key)

    async def aexists(self, key: str) -> bool:
        """Asynchronously check whether ``key`` exists on disk.

        Args:
            key: Logical key to test.

        Returns:
            ``True`` if a file exists at the resolved path, ``False`` otherwise.
        """
        return await asyncio.to_thread(self._provider.exists, key)

    async def alist_keys(self) -> list[str]:
        """Asynchronously list all logical keys present under the storage root.

        Returns:
            A sorted list of logical keys. Returns an empty list if the root
            directory does not exist.
        """
        return await asyncio.to_thread(self._provider.list_keys)


__all__ = ["AsyncFileStorage"]
