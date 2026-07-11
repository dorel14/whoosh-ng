from __future__ import annotations

import asyncio
import threading

import pytest

from whoosh.utils.async_utils import (
    call_maybe_async,
    is_async_callable,
    maybe_await,
    run_async_from_sync,
    run_sync,
)


def test_run_sync_returns_value() -> None:
    assert asyncio.run(run_sync(lambda x: x + 1, 41)) == 42


def test_run_sync_runs_off_event_loop() -> None:
    main_thread = threading.current_thread()

    def blocking() -> bool:
        return threading.current_thread() is not main_thread

    async def runner() -> bool:
        return await run_sync(blocking)

    assert asyncio.run(runner()) is True


@pytest.mark.asyncio
async def test_maybe_await_passthrough() -> None:
    assert await maybe_await(7) == 7


@pytest.mark.asyncio
async def test_maybe_await_coroutine() -> None:
    assert await maybe_await(asyncio.sleep(0, 9)) == 9


@pytest.mark.asyncio
async def test_call_maybe_async_sync() -> None:
    assert await call_maybe_async(lambda x: x * 2, 3) == 6


@pytest.mark.asyncio
async def test_call_maybe_async_async() -> None:
    async def doubler(x: int) -> int:
        return x * 2

    assert await call_maybe_async(doubler, 4) == 8


def test_is_async_callable_function() -> None:
    async def a() -> None:
        pass

    def b() -> None:
        pass

    assert is_async_callable(a) is True
    assert is_async_callable(b) is False


def test_run_async_from_sync_executes() -> None:
    async def coro() -> int:
        return 11

    assert run_async_from_sync(coro()) == 11


@pytest.mark.asyncio
async def test_run_sync_async_marker() -> None:
    assert await run_sync(sum, [1, 2, 3]) == 6
