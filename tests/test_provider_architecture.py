from __future__ import annotations

import pytest
from dataclasses import dataclass, field
from typing import Any

from whoosh.hooks import HookImpl, call_hook, hookimpl, register_hook


@dataclass(frozen=True)
class IndexRequest:
    document: dict[str, Any]


@dataclass(frozen=True)
class SearchRequest:
    query_string: str
    limit: int = 10


class StorageProvider:
    async def read(self, key: str) -> bytes:
        raise NotImplementedError

    async def write(self, key: str, data: bytes) -> None:
        raise NotImplementedError

    async def delete(self, key: str) -> None:
        raise NotImplementedError


class FileStorageProvider(StorageProvider):
    def __init__(self, path: str = "") -> None:
        self.path = path

    async def read(self, key: str) -> bytes:
        return b"mocked-file-data"

    async def write(self, key: str, data: bytes) -> None:
        pass

    async def delete(self, key: str) -> None:
        pass


@dataclass(frozen=True)
class RankedResult:
    document_id: str
    score: float
    payload: dict[str, Any] = field(default_factory=dict)


class RankingProvider:
    async def rank(self, request: SearchRequest, hits: list[RankedResult]) -> list[RankedResult]:
        raise NotImplementedError


class BM25Provider(RankingProvider):
    async def rank(self, request: SearchRequest, hits: list[RankedResult]) -> list[RankedResult]:
        return sorted(hits, key=lambda r: r.score, reverse=True)


class HookedStorageProvider(StorageProvider):
    def __init__(self, provider: StorageProvider) -> None:
        self.provider = provider

    async def read(self, key: str) -> bytes:
        data = await self.provider.read(key)
        return data

    async def write(self, key: str, data: bytes) -> None:
        updated = await call_hook("before_write", key, data)
        await self.provider.write(key, updated if isinstance(updated, (bytes, bytearray)) else data)
        await call_hook("after_write", key, data)

    async def delete(self, key: str) -> None:
        await self.provider.delete(key)


class InMemoryStorageProvider(StorageProvider):
    def __init__(self) -> None:
        self._store: dict[str, bytes] = {}

    async def read(self, key: str) -> bytes:
        return self._store[key]

    async def write(self, key: str, data: bytes) -> None:
        self._store[key] = data

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)


@pytest.fixture(autouse=True)
def isolated_hooks() -> None:
    from whoosh import hooks as _hooks_mod

    _hooks_mod._hooks.clear()


def test_hookimpl_decorator() -> None:
    async def _impl(x: int) -> int:
        return x

    impl = hookimpl(_impl)
    assert impl.func is _impl


@pytest.mark.asyncio
async def test_register_and_call_hook() -> None:
    async def transform(request: SearchRequest) -> SearchRequest:
        return SearchRequest(request.query_string, limit=5)

    register_hook("before_search", hookimpl(transform))
    request = await call_hook("before_search", SearchRequest("q", limit=10))
    assert request[0].limit == 5


@pytest.mark.asyncio
async def test_hook_exception_isolation() -> None:
    async def bad() -> None:
        raise RuntimeError("oops")

    async def good() -> str:
        return "ok"

    register_hook("sample", hookimpl(bad))
    register_hook("sample", hookimpl(good))

    result = await call_hook("sample")
    assert result[0] == "ok"
