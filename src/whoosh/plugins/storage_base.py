from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SyncStorageProvider(ABC):
    """Synchronous storage provider contract for plugins.

    Concrete providers wrap a backend (file, sqlite, postgres, s3, ...) and
    expose a small, backend-agnostic read/write surface used by Whoosh core.
    """

    @abstractmethod
    def write(self, key: str, data: bytes) -> None:
        raise NotImplementedError

    @abstractmethod
    def read(self, key: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def exists(self, key: str) -> bool:
        raise NotImplementedError

    def list_keys(self) -> list[str]:
        raise NotImplementedError


class AsyncStorageProvider(ABC):
    """Asynchronous counterpart to :class:`SyncStorageProvider`.

    Plugins that talk to networked or async-native backends (PostgreSQL via
    asyncpg, S3, MinIO, Redis, ...) should subclass this provider and implement
    the ``a*`` coroutine methods. All async plugin code should call sync core
    methods through :func:`whoosh.utils.async.run_sync`.
    """

    @abstractmethod
    async def awrite(self, key: str, data: bytes) -> None:
        raise NotImplementedError

    @abstractmethod
    async def aread(self, key: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    async def adelete(self, key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def aexists(self, key: str) -> bool:
        raise NotImplementedError

    async def alist_keys(self) -> list[str]:
        raise NotImplementedError


__all__ = ["SyncStorageProvider", "AsyncStorageProvider"]
