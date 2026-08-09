"""HybridStorage: local cache + remote backend for cloud-native indexes.

Author: dorel14
Version: 2.0.0
"""

from __future__ import annotations

import os
from collections import OrderedDict

from whoosh.plugins.storage_base import AsyncStorageProvider, SyncStorageProvider


class HybridStorage(SyncStorageProvider):
    """Compose a local cache and a remote backend.

    Read path::

        1. local cache hit → return immediately
        2. cache miss → read from remote, write-through into cache, return

    Write path::

        remote.write(key, data)  # source of truth
        → on success: local_cache.write(key, data)
        → on failure: raise before polluting cache

    Delete path::

        remote.delete(key) + local_cache.delete(key)

    ``list_keys`` uses the remote as source of truth; ``include_cache=True``
    returns the union of remote and cache keys.

    Example::

        from whoosh_modern.storage import HybridStorage, S3Storage

        remote = S3Storage(bucket="my-index-bucket", prefix="segments")
        storage = HybridStorage(local_cache="./cache", remote=remote)

        storage.write("segment_1.dat", b"binary-segment-data")
        data = storage.read("segment_1.dat")  # cached after first read
        storage.invalidate("segment_1.dat")   # force refresh from remote
        storage.prefetch(["segment_2.dat"])   # warm cache
    """

    def __init__(
        self,
        local_cache: str,
        remote: SyncStorageProvider,
        max_cache_size_mb: int = 1024,
    ) -> None:
        """Initialize the hybrid storage with a local cache and remote backend.

        Args:
            local_cache: Directory path for the local file-based cache.
            remote: Remote storage provider (e.g., S3Storage).
            max_cache_size_mb: Maximum cache size in megabytes before
                evicting oldest entries.
        """
        self._cache_root = os.path.abspath(local_cache)
        self._remote = remote
        self._max_cache_bytes = max_cache_size_mb * 1024 * 1024
        self._cache: OrderedDict[str, bytes] = OrderedDict()
        self._cache_size: int = 0
        os.makedirs(self._cache_root, exist_ok=True)

    def _cache_path(self, key: str) -> str:
        """Return the local filesystem path for a cache key.

        Args:
            key: The storage key.

        Returns:
            Safe filesystem path for the key.
        """
        safe = key.replace("\\", os.sep).replace("/", os.sep)
        return os.path.join(self._cache_root, safe)

    def _cache_file_exists(self, key: str) -> bool:
        """Check whether the cache key exists on the local filesystem.

        Args:
            key: The storage key.

        Returns:
            True if the file exists on disk, False otherwise.
        """
        return os.path.exists(self._cache_path(key))

    def _read_cache(self, key: str) -> bytes | None:
        """Read cached data for a key from the local filesystem.

        Args:
            key: The storage key.

        Returns:
            Cached bytes if present, None otherwise.
        """
        path = self._cache_path(key)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as fh:
            data = fh.read()
        self._cache[key] = data
        self._cache_size += len(data)
        self._enforce_cache_limit()
        return data

    def _write_cache(self, key: str, data: bytes) -> None:
        """Write data to the local cache for a key.

        Args:
            key: The storage key.
            data: Binary data to cache.
        """
        path = self._cache_path(key)
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(data)
        self._cache[key] = data
        self._cache_size += len(data)
        self._enforce_cache_limit()

    def _delete_cache(self, key: str) -> None:
        """Delete a key from the local cache.

        Args:
            key: The storage key to remove.
        """
        path = self._cache_path(key)
        if os.path.exists(path):
            os.remove(path)
        if key in self._cache:
            self._cache_size -= len(self._cache[key])
            del self._cache[key]

    def _enforce_cache_limit(self) -> None:
        """Evict oldest cache entries until within the size limit."""
        while self._cache_size > self._max_cache_bytes and self._cache:
            oldest_key, oldest_data = self._cache.popitem(last=False)
            self._cache_size -= len(oldest_data)
            path = self._cache_path(oldest_key)
            if os.path.exists(path):
                os.remove(path)

    def invalidate(self, key: str) -> None:
        """Remove ``key`` from the local cache.

        Args:
            key: The key to invalidate.
        """
        self._delete_cache(key)

    def prefetch(self, keys: list[str]) -> None:
        """Warm the local cache by reading ``keys`` from the remote.

        Args:
            keys: List of keys to prefetch from the remote backend.
        """
        for key in keys:
            try:
                data = self._remote.read(key)
            except Exception:
                continue
            self._write_cache(key, data)

    def write(self, key: str, data: bytes) -> None:
        """Write data to remote first, then write-through to cache.

        Args:
            key: The storage key.
            data: Binary data to store.
        """
        self._remote.write(key, data)
        self._write_cache(key, data)

    def read(self, key: str) -> bytes:
        """Read data, checking local cache first, then remote.

        Args:
            key: The storage key.

        Returns:
            Binary data for the key.
        """
        cached = self._read_cache(key)
        if cached is not None:
            return cached
        data = self._remote.read(key)
        self._write_cache(key, data)
        return data

    def delete(self, key: str) -> None:
        """Delete data from both remote and local cache.

        Args:
            key: The storage key to delete.
        """
        self._remote.delete(key)
        self._delete_cache(key)

    def exists(self, key: str) -> bool:
        """Check existence in local cache, then remote.

        Args:
            key: The storage key.

        Returns:
            True if the key exists in either cache or remote.
        """
        if self._cache_file_exists(key):
            return True
        return self._remote.exists(key)

    def list_keys(self, include_cache: bool = False) -> list[str]:
        """List keys from the remote, optionally including cache keys.

        Args:
            include_cache: If True, returns the union of remote and cache keys.

        Returns:
            Sorted list of key strings.
        """
        remote_keys = set(self._remote.list_keys())
        if include_cache:
            cache_keys: set[str] = set()
            for current, _dirs, files in os.walk(self._cache_root):
                for name in files:
                    full = os.path.join(current, name)
                    rel = os.path.relpath(full, self._cache_root)
                    cache_keys.add(rel.replace(os.sep, "/"))
            return sorted(remote_keys | cache_keys)
        return sorted(remote_keys)


class AsyncHybridStorage(AsyncStorageProvider):
    """Async variant of :class:`HybridStorage`.

    Remote operations are executed on a worker thread via ``asyncio.to_thread``
    so the event loop is never blocked.

    Example::

        import asyncio
        from whoosh_modern.storage import AsyncHybridStorage, S3Storage

        remote = S3Storage(bucket="my-index-bucket", prefix="segments")
        storage = AsyncHybridStorage(local_cache="./cache", remote=remote)

        async def main() -> None:
            await storage.awrite("segment_1.dat", b"data")
            data = await storage.aread("segment_1.dat")
            await storage.adelete("segment_1.dat")

        asyncio.run(main())
    """

    def __init__(self, local_cache: str, remote: SyncStorageProvider) -> None:
        """Initialize the async hybrid storage.

        Args:
            local_cache: Directory path for the local file-based cache.
            remote: Remote storage provider (e.g., S3Storage).
        """
        self._storage = HybridStorage(local_cache=local_cache, remote=remote)

    def invalidate(self, key: str) -> None:
        """Invalidate a key in the local cache (sync wrapper).

        Args:
            key: The key to invalidate.
        """
        self._storage.invalidate(key)

    def prefetch(self, keys: list[str]) -> None:
        """Prefetch keys into the local cache (sync wrapper).

        Args:
            keys: List of keys to prefetch.
        """
        self._storage.prefetch(keys)

    async def awrite(self, key: str, data: bytes) -> None:
        """Asynchronously write data to the remote backend and cache.

        Args:
            key: The storage key.
            data: Binary data to store.
        """
        import asyncio

        await asyncio.to_thread(self._storage.write, key, data)

    async def aread(self, key: str) -> bytes:
        """Asynchronously read data, checking cache then remote.

        Args:
            key: The storage key.

        Returns:
            Binary data for the key.
        """
        import asyncio

        return await asyncio.to_thread(self._storage.read, key)

    async def adelete(self, key: str) -> None:
        """Asynchronously delete data from remote and cache.

        Args:
            key: The storage key to delete.
        """
        import asyncio

        await asyncio.to_thread(self._storage.delete, key)

    async def aexists(self, key: str) -> bool:
        """Asynchronously check if a key exists.

        Args:
            key: The storage key.

        Returns:
            True if the key exists in cache or remote.
        """
        import asyncio

        return await asyncio.to_thread(self._storage.exists, key)

    async def alist_keys(self, include_cache: bool = False) -> list[str]:
        """Asynchronously list keys from remote (optionally with cache keys).

        Args:
            include_cache: If True, include cache keys in the result.

        Returns:
            Sorted list of key strings.
        """
        import asyncio

        return await asyncio.to_thread(self._storage.list_keys, include_cache=include_cache)


__all__ = ["HybridStorage", "AsyncHybridStorage"]
