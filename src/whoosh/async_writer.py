from __future__ import annotations

import asyncio
import time
from typing import Any, Optional, Tuple

from whoosh.index import Index, LockError
from whoosh.locking import AsyncLock
from whoosh.writing import IndexWriter

__all__ = ["AsyncWriter"]


class AsyncWriter(IndexWriter):
    """Asyncio-native convenience wrapper around an :class:`whoosh.index.Index`.

    This is the asyncio equivalent of :class:`whoosh.writing.AsyncWriter`. It
    buffers ``add_document`` / ``update_document`` / ``delete_*`` calls in memory
    and replays them once it can obtain the underlying (synchronous) writer,
    which is run on a worker thread via ``loop.run_in_executor`` so the event
    loop is never blocked (issue #578 / #369).

    The blocking index storage layer is not async, so the actual replay/commit
    happens on a worker thread. The public API, however, is ``async`` and uses
    an :class:`whoosh.locking.AsyncLock` to guarantee a single in-flight commit
    and to recover cleanly from :class:`whoosh.index.LockError`.

    Basic usage::

        w = AsyncWriter(index)
        w.add_document(title="First", content="Hello there.")
        w.add_document(title="Second", content="This is easy!")
        await w.commit(timeout=30)

    If the writer cannot be obtained immediately (the index is locked), the
    buffered calls are replayed as soon as the lock becomes available. Call
    :meth:`acancel` to discard the buffered calls instead of committing.
    """

    def __init__(self, index: Index, delay: float = 0.25, writerargs: Optional[dict] = None):
        """
        :param index: the :class:`whoosh.index.Index` to write to.
        :param delay: the delay (in seconds) between attempts to instantiate the
            actual writer when the index is locked.
        :param writerargs: an optional dictionary specifying keyword arguments
            to pass to the index's ``writer()`` method.
        """

        self.index = index
        self.writerargs = writerargs or {}
        self.delay = delay
        self.events: list[Tuple[str, Tuple[Any, ...], dict]] = []

        self._lock = AsyncLock()
        self._started = False
        self._committed = False
        self._cancelled = False
        self._error: Optional[BaseException] = None
        self._writer: Optional[IndexWriter] = None
        self._done: Optional["asyncio.Future[Any]"] = None

        try:
            self._writer = self.index.writer(**self.writerargs)
        except LockError:
            self._writer = None

    # -- synchronization helpers -------------------------------------------

    def reader(self):  # type: ignore[override]
        return self.index.reader()

    def searcher(self, **kwargs):
        from whoosh.searching import Searcher

        return Searcher(self.reader(), fromindex=self.index, **kwargs)

    # -- buffering ----------------------------------------------------------

    def _record(self, method: str, args: Tuple[Any, ...], kwargs: dict) -> None:
        if self._writer is not None:
            # We already hold the underlying writer, so apply immediately.
            getattr(self._writer, method)(*args, **kwargs)
        else:
            self.events.append((method, args, kwargs))

    def delete_document(self, *args, **kwargs):
        self._record("delete_document", args, kwargs)

    def add_document(self, **fields):  # type: ignore[override]
        self._record("add_document", (), fields)

    def update_document(self, **fields):  # type: ignore[override]
        self._record("update_document", (), fields)

    def add_field(self, *args, **kwargs):
        self._record("add_field", args, kwargs)

    def remove_field(self, *args, **kwargs):
        self._record("remove_field", args, kwargs)

    def delete_by_term(self, *args, **kwargs):
        self._record("delete_by_term", args, kwargs)

    def add_reader(self, reader):  # type: ignore[override]
        # Passed straight through; replaying a reader is not buffered.
        if self._writer is not None:
            self._writer.add_reader(reader)
        else:
            # Buffer as a closure so it can be replayed on the real writer.
            self.events.append(("add_reader", (reader,), {}))

    # -- background work ----------------------------------------------------

    def _run(self, commit_args: Tuple[Any, ...], commit_kwargs: dict, timeout: Optional[float]) -> None:
        """Synchronous work executed on a worker thread via ``run_in_executor``."""

        try:
            if self._cancelled:
                return

            writer = self._writer
            # Acquire the underlying writer, retrying if the index is locked
            # (issue #369). If we already held it (eager acquisition), this is
            # a no-op.
            deadline = None if timeout is None else (time.monotonic() + timeout)
            while writer is None:
                try:
                    writer = self.index.writer(**self.writerargs)
                except LockError:
                    if deadline is not None and time.monotonic() >= deadline:
                        raise LockError(
                            "Could not acquire the index writer within the timeout"
                        )
                    time.sleep(self.delay)

            for method, args, kwargs in self.events:
                getattr(writer, method)(*args, **kwargs)
            writer.commit(*commit_args, **commit_kwargs)
            self._committed = True
        except BaseException as e:  # surface to the awaiting coroutine
            self._error = e
            raise

    # -- public async API ---------------------------------------------------

    async def commit(self, *args: Any, timeout: Optional[float] = None, **kwargs: Any) -> None:
        """Replay the buffered calls and commit the index asynchronously.

        :param timeout: maximum time (seconds) to wait for the commit to
            complete. ``None`` waits indefinitely. This also bounds how long the
            wrapper will retry acquiring a locked index.
        :raises RuntimeError: if ``commit()`` has already been called, or a
            commit is already in flight.
        :raises BaseException: re-raises any error that occurred in the worker
            thread (so async failures are observable -- issue #578).
        """

        async with self._lock:
            if self._committed:
                raise RuntimeError(
                    "AsyncWriter.commit() has already been called; this writer is spent"
                )
            if self._writer is not None:
                # We already hold the underlying writer: commit directly on a
                # worker thread (keeps the event loop free).
                loop = asyncio.get_running_loop()
                await asyncio.wait_for(
                    loop.run_in_executor(None, self._run, args, kwargs, timeout),
                    timeout,
                )
                return

            if self._started:
                raise RuntimeError(
                    "AsyncWriter.commit() is already running; call it only once"
                )
            self._started = True
            loop = asyncio.get_running_loop()
            self._done = loop.run_in_executor(None, self._run, args, kwargs, timeout)
            assert self._done is not None
            try:
                await asyncio.wait_for(asyncio.shield(self._done), timeout)
            except asyncio.TimeoutError:
                # The commit is still running in the worker thread; surface the
                # timeout but do not leave the object in an inconsistent state.
                raise TimeoutError(
                    "AsyncWriter.commit() did not finish within the timeout"
                ) from None

        # Re-raise any error from the worker thread now that the lock is free.
        if self._error is not None:
            raise self._error

    async def wait(self, timeout: Optional[float] = None) -> bool:
        """Wait for a background commit to finish; re-raise any failure.

        :returns: ``True`` if the commit completed successfully.
        """

        if self._done is not None:
            await asyncio.wait_for(self._done, timeout)
        if self._error is not None:
            raise self._error
        return self._committed

    async def acancel(self, *args: Any, **kwargs: Any) -> None:
        """Cancel the buffered writes asynchronously.

        If the underlying writer was acquired eagerly, ``cancel()`` is called on
        it directly. Otherwise the buffered events are dropped and any
        background thread will not replay or commit anything.
        """

        async with self._lock:
            if self._committed:
                raise RuntimeError("AsyncWriter has already committed; cannot cancel")
            if self._writer is not None:
                self._writer.cancel(*args, **kwargs)
                self._committed = True
            else:
                self._cancelled = True
