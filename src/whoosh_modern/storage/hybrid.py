"""HybridStorage: local cache + remote backend for cloud-native indexes."""

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
    """

    def __init__(
        self,
        local_cache: str,
        remote: SyncStorageProvider,
        max_cache_size_mb: int = 1024,
    ) -> None:
        self._cache_root = os.path.abspath(local_cache)
        self._remote = remote
        self._max_cache_bytes = max_cache_size_mb * 1024 * 1024
        self._cache: OrderedDict[str, bytes] = OrderedDict()
        self._cache_size: int = 0
        os.makedirs(self._cache_root, exist_ok=True)

    def _cache_path(self, key: str) -> str:
        safe = key.replace("\\", os.sep).replace("/", os.sep)
        return os.path.join(self._cache_root, safe)

    def _cache_file_exists(self, key: str) -> bool:
        return os.path.exists(self._cache_path(key))

    def _read_cache(self, key: str) -> bytes | None:
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
        path = self._cache_path(key)
        if os.path.exists(path):
            os.remove(path)
        if key in self._cache:
            self._cache_size -= len(self._cache[key])
            del self._cache[key]

    def _enforce_cache_limit(self) -> None:
        while self._cache_size > self._max_cache_bytes and self._cache:
            oldest_key, oldest_data = self._cache.popitem(last=False)
            self._cache_size -= len(oldest_data)
            path = self._cache_path(oldest_key)
            if os.path.exists(path):
                os.remove(path)

    def invalidate(self, key: str) -> None:
        """Remove ``key`` from the local cache."""
        self._delete_cache(key)

    def prefetch(self, keys: list[str]) -> None:
        """Warm the local cache by reading ``keys`` from the remote."""
        for key in keys:
            try:
                data = self._remote.read(key)
            except Exception:
                continue
            self._write_cache(key, data)

    def write(self, key: str, data: bytes) -> None:
        self._remote.write(key, data)
        self._write_cache(key, data)

    def read(self, key: str) -> bytes:
        cached = self._read_cache(key)
        if cached is not None:
            return cached
        data = self._remote.read(key)
        self._write_cache(key, data)
        return data

    def delete(self, key: str) -> None:
        self._remote.delete(key)
        self._delete_cache(key)

    def exists(self, key: str) -> bool:
        if self._cache_file_exists(key):
            return True
        return self._remote.exists(key)

    def list_keys(self, include_cache: bool = False) -> list[str]:
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
    """

    def __init__(self, local_cache: str, remote: SyncStorageProvider) -> None:
        self._storage = HybridStorage(local_cache=local_cache, remote=remote)

    def invalidate(self, key: str) -> None:
        self._storage.invalidate(key)

    def prefetch(self, keys: list[str]) -> None:
        self._storage.prefetch(keys)

    async def awrite(self, key: str, data: bytes) -> None:
        import asyncio

        await asyncio.to_thread(self._storage.write, key, data)

    async def aread(self, key: str) -> bytes:
        import asyncio

        return await asyncio.to_thread(self._storage.read, key)

    async def adelete(self, key: str) -> None:
        import asyncio

        await asyncio.to_thread(self._storage.delete, key)

    async def aexists(self, key: str) -> bool:
        import asyncio

        return await asyncio.to_thread(self._storage.exists, key)

    async def alist_keys(self, include_cache: bool = False) -> list[str]:
        import asyncio

        return await asyncio.to_thread(self._storage.list_keys, include_cache=include_cache)


__all__ = ["HybridStorage", "AsyncHybridStorage"]
