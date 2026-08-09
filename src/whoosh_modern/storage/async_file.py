"""Async filesystem storage provider bridging SyncStorageProvider via to_thread.

This module provides :class:`AsyncFileStorage`, an :class:`AsyncStorageProvider`
that performs all filesystem I/O on a worker thread through
:func:`asyncio.to_thread`, keeping the event loop unblocked.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

import asyncio
import os

from whoosh.plugins.storage_base import AsyncStorageProvider


class AsyncFileStorage(AsyncStorageProvider):
    """Async filesystem storage provider backed by the local OS filesystem.

    All read/write/delete/list operations are dispatched to a worker thread via
    ``asyncio.to_thread`` so the event loop is never blocked by disk I/O.

    The provider is instantiated from a project root ``root`` directory; each
    logical key is resolved to a physical path under that root. Parent
    directories are created automatically on write.

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
                resolved to an absolute path; intermediate directories are
                created lazily on write.

        Raises:
            OSError: If ``root`` cannot be converted to an absolute path
                (propagated from :func:`os.path.abspath`).
        """
        self._root = os.path.abspath(root)

    def _path(self, key: str) -> str:
        """Resolve a logical key to a physical filesystem path.

        Args:
            key: Logical key, which may use ``/`` or ``\\`` separators.

        Returns:
            The absolute filesystem path corresponding to ``key`` under the
            configured root, with separators normalised to ``os.sep``.
        """
        safe = key.replace("\\", os.sep).replace("/", os.sep)
        return os.path.join(self._root, safe)

    async def awrite(self, key: str, data: bytes) -> None:
        """Asynchronously write ``data`` to ``key``.

        Args:
            key: Logical key under the storage root.
            data: Binary payload to persist.

        Raises:
            OSError: If the file cannot be created or written (propagated from
                the underlying ``open``/``os.makedirs`` calls).
        """
        path = self._path(key)
        parent = os.path.dirname(path)
        if parent:
            await asyncio.to_thread(os.makedirs, parent, exist_ok=True)

        def _write() -> None:
            with open(path, "wb") as fh:
                fh.write(data)

        await asyncio.to_thread(_write)

    async def aread(self, key: str) -> bytes:
        """Asynchronously read the full binary content stored at ``key``.

        Args:
            key: Logical key to read.

        Returns:
            The complete byte payload stored under ``key``.

        Raises:
            FileNotFoundError: If ``key`` does not exist on disk.
            OSError: For other I/O errors raised by the underlying ``open``
                call.
        """

        def _read() -> bytes:
            with open(self._path(key), "rb") as fh:
                return fh.read()

        return await asyncio.to_thread(_read)

    async def adelete(self, key: str) -> None:
        """Asynchronously delete the file stored at ``key``.

        If the key does not exist, the call is a no-op (the underlying
        ``os.path.exists`` check prevents an error).

        Args:
            key: Logical key to delete.

        Raises:
            OSError: If the file exists but cannot be removed (propagated from
                :func:`os.remove`).
        """
        path = self._path(key)

        def _delete() -> None:
            if os.path.exists(path):
                os.remove(path)

        await asyncio.to_thread(_delete)

    async def aexists(self, key: str) -> bool:
        """Asynchronously check whether ``key`` exists on disk.

        Args:
            key: Logical key to test.

        Returns:
            ``True`` if a file exists at the resolved path, ``False`` otherwise.
        """
        return await asyncio.to_thread(os.path.exists, self._path(key))

    async def alist_keys(self) -> list[str]:
        """Asynchronously list all logical keys present under the storage root.

        The root directory is walked recursively; each file's relative path
        (relative to the root) is returned with OS separators normalised to
        ``/``. The result is sorted lexicographically.

        Returns:
            A sorted list of logical keys. Returns an empty list if the root
            directory does not exist.
        """

        def _list() -> list[str]:
            keys: list[str] = []
            root = self._root
            if not os.path.isdir(root):
                return keys
            for current, _dirs, files in os.walk(root):
                for name in files:
                    full = os.path.join(current, name)
                    rel = os.path.relpath(full, root)
                    keys.append(rel.replace(os.sep, "/"))
            return sorted(keys)

        return await asyncio.to_thread(_list)


__all__ = ["AsyncFileStorage"]
