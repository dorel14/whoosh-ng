# type: ignore
from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from typing import Any

__all__ = ["AsyncLock", "try_for"]


class AsyncLock:
    """An asyncio-friendly wrapper around :class:`asyncio.Lock`.

    It mirrors the synchronous ``Lock`` used by the index storage layer (see
    :mod:`whoosh.util.filelock`) but is safe to use from coroutines:

    * ``acquire(blocking=, timeout=)`` -- blocking acquire with an optional
      deadline (``None`` waits forever, ``<= 0`` is non-blocking).
    * ``acquire_nowait()`` -- non-blocking attempt returning ``True`` if the
      lock was obtained.
    * ``release()`` -- release the lock.
    * ``locked`` -- property mirroring :attr:`asyncio.Lock.locked`.
    * async context-manager protocol (``async with lock:``).

    This is used by the asyncio-native :class:`whoosh.async_writer.AsyncWriter`
    to guarantee a single in-flight commit and to recover from
    :class:`whoosh.index.LockError` without corrupting the index.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()

    @property
    def locked(self) -> bool:
        return self._lock.locked()

    async def acquire_nowait(self) -> bool:
        """Try to acquire the lock without blocking.

        Implemented via ``asyncio.wait_for(..., 0)`` so it relies only on
        public, stubbed ``asyncio`` APIs (avoids ``asyncio.Lock.acquire_nowait``
        which is missing from some type stubs).

        :returns: ``True`` if the lock was acquired, ``False`` otherwise.
        """

        try:
            await asyncio.wait_for(self._lock.acquire(), 0)
        except TimeoutError:
            return False
        return True

    async def acquire(self, blocking: bool = True, timeout: float | None = None) -> bool:
        """Acquire the lock.

        :param blocking: if ``False`` (or ``timeout`` is ``<= 0``), return
            immediately with the result of a non-blocking attempt.
        :param timeout: maximum time in seconds to wait when blocking. ``None``
            waits indefinitely.
        :returns: ``True`` if the lock was acquired.
        """

        if not blocking or (timeout is not None and timeout <= 0):
            return await self.acquire_nowait()
        try:
            await asyncio.wait_for(self._lock.acquire(), timeout)
        except TimeoutError:
            return False
        return True

    def release(self) -> None:
        self._lock.release()

    async def __aenter__(self) -> AsyncLock:
        await self.acquire()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.release()


async def try_for(
    acquire: Callable[..., Any],
    timeout: float | None = None,
    delay: float = 0.1,
    attempts: int | None = None,
) -> bool:
    """Async equivalent of :func:`whoosh.util.filelock.try_for`.

    Repeatedly calls ``acquire`` until it returns a truthy value or the
    deadline/attempt limit is reached. The ``acquire`` callable may be either
    synchronous (returns a truthy/falsey value) or a coroutine function (its
    awaitable result is awaited and its truthiness is used).

    :param acquire: a zero-argument callable that attempts to acquire a lock.
    :param timeout: maximum total time in seconds (``None`` = no limit).
    :param delay: time to sleep between attempts.
    :param attempts: maximum number of attempts (``None`` = unlimited).
    :returns: ``True`` if ``acquire`` eventually returned truthy.
    """

    deadline: float | None = None if timeout is None else (time.monotonic() + timeout)
    tries = 0
    while True:
        result = acquire()
        if asyncio.iscoroutine(result):
            result = await result
        if result:
            return True
        tries += 1
        if attempts is not None and tries >= attempts:
            return False
        if deadline is not None and time.monotonic() >= deadline:
            return False
        await asyncio.sleep(delay)
