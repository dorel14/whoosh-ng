from __future__ import annotations

import pytest

from whoosh.middleware.base import Middleware
from whoosh.middleware.chain import MiddlewareChain
from whoosh.middleware.context import MiddlewareContext


class SyncOrderMiddleware(Middleware):
    def __init__(self, log: list[str], tag: str) -> None:
        self.log = log
        self.tag = tag

    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        self.log.append(f"sync-before-{self.tag}")
        return context

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        self.log.append(f"sync-after-{self.tag}")
        return context


class AsyncOrderMiddleware(Middleware):
    def __init__(self, log: list[str], tag: str) -> None:
        self.log = log
        self.tag = tag

    async def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        self.log.append(f"async-before-{self.tag}")
        return context

    async def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        self.log.append(f"async-after-{self.tag}")
        return context


@pytest.mark.asyncio
async def test_async_chain_execution_order() -> None:
    log: list[str] = []
    chain = MiddlewareChain([SyncOrderMiddleware(log, "a"), AsyncOrderMiddleware(log, "b")])
    ctx = MiddlewareContext("search")
    ctx.query = "hello"

    before = await chain.async_run_before("before_search", ctx)
    after = await chain.async_run_after("after_search", before)

    assert after is not None
    assert log == [
        "sync-before-a",
        "async-before-b",
        "async-after-b",
        "sync-after-a",
    ]


@pytest.mark.asyncio
async def test_chain_mixed_sync_async_middleware() -> None:
    log: list[str] = []
    chain = MiddlewareChain([AsyncOrderMiddleware(log, "x")])
    ctx = MiddlewareContext("search")
    await chain.async_run_before("before_search", ctx)
    assert log == ["async-before-x"]
