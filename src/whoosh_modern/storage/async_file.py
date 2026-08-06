"""Async filesystem storage provider bridging SyncStorageProvider via to_thread."""

from __future__ import annotations

import asyncio
import os
from typing import Any

from whoosh.plugins.storage_base import AsyncStorageProvider


class AsyncFileStorage(AsyncStorageProvider):
    """Async filesystem storage provider.

    All operations are executed on a worker thread via ``asyncio.to_thread`` so
    the event loop is never blocked.
    """

    def __init__(self, root: str) -> None:
        self._root = os.path.abspath(root)

    def _path(self, key: str) -> str:
        safe = key.replace("\\", os.sep).replace("/", os.sep)
        return os.path.join(self._root, safe)

    async def awrite(self, key: str, data: bytes) -> None:
        path = self._path(key)
        parent = os.path.dirname(path)
        if parent:
            await asyncio.to_thread(os.makedirs, parent, exist_ok=True)

        def _write() -> None:
            with open(path, "wb") as fh:
                fh.write(data)

        await asyncio.to_thread(_write)

    async def aread(self, key: str) -> bytes:
        def _read() -> bytes:
            with open(self._path(key), "rb") as fh:
                return fh.read()

        return await asyncio.to_thread(_read)

    async def adelete(self, key: str) -> None:
        path = self._path(key)

        def _delete() -> None:
            if os.path.exists(path):
                os.remove(path)

        await asyncio.to_thread(_delete)

    async def aexists(self, key: str) -> bool:
        return await asyncio.to_thread(os.path.exists, self._path(key))

    async def alist_keys(self) -> list[str]:
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
