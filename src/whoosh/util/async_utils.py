"""Async utility helpers bridging sync core code and async plugin/hook code.

This module provides small primitives for running synchronous functions in a
thread pool, awaiting values that may or may not be awaitable, and invoking
async callables from synchronous code. These helpers keep the event loop
unblocked when sync core methods must be called from async contexts, and
provide a safe bridge when async plugin hooks must be called from sync code.

Auteur: SoniqueBay Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable, Coroutine
from typing import Any, TypeVar, overload

T = TypeVar("T")
R = TypeVar("R")


async def run_sync(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Execute a synchronous function in a thread pool.

    All async plugin code that needs to call sync core methods should use this
    helper so the event loop is never blocked by CPU-bound or blocking I/O work.
    """
    return await asyncio.to_thread(func, *args, **kwargs)


@overload
async def maybe_await(value: Awaitable[T]) -> T: ...


@overload
async def maybe_await(value: T) -> T: ...


async def maybe_await(value: Awaitable[T] | T) -> T:
    """Await ``value`` if it is awaitable, otherwise return it unchanged."""
    if inspect.isawaitable(value):
        return await value
    return value


@overload
async def call_maybe_async(func: Callable[..., Awaitable[R]], *args: Any, **kwargs: Any) -> R: ...


@overload
async def call_maybe_async(func: Callable[..., R], *args: Any, **kwargs: Any) -> R: ...


async def call_maybe_async(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Call ``func`` and await the result if it returned an awaitable.

    This bridges sync and async plugin/callable implementations: a sync callable
    runs inline, while an async callable is awaited.
    """
    result = func(*args, **kwargs)
    return await maybe_await(result)


def is_async_callable(func: Callable[..., Any]) -> bool:
    """Return ``True`` if ``func`` (or its ``__call__``) is a coroutine function."""
    if inspect.iscoroutinefunction(func):
        return True
    method = getattr(func, "__call__", None)  # noqa: B004 - intentional __call__ introspection for coroutine detection
    return inspect.iscoroutinefunction(method)


def run_async_from_sync(coro: Coroutine[Any, Any, T]) -> T:
    """Run a coroutine from synchronous code.

    Use this bridge when sync core code (e.g. ``PluginManager.register``) needs
    to invoke an async plugin hook. A new event loop is created; calling this
    from inside a running loop is unsupported and raises ``RuntimeError``.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop is not None:
        raise RuntimeError("run_async_from_sync cannot be called from within a running event loop")
    return asyncio.run(coro)


__all__ = [
    "run_sync",
    "maybe_await",
    "call_maybe_async",
    "is_async_callable",
    "run_async_from_sync",
]
