"""Resilience middleware (retry, logging, caching) built on the core hooks.

This module re-expresses the former ``whoosh_modern.middleware.pipeline``
wrap-style middleware as subclasses of :class:`whoosh.middleware.base.Middleware`.
Each class therefore participates in the core :class:`whoosh.middleware.chain.MiddlewareChain`
through the standard hooks (``before_index``/``after_index``/``before_search``/
``after_search``/``on_error``/``on_commit``) while keeping the historical
:meth:`wrap` helper so arbitrary callables can still be decorated.

:class:`MiddlewarePipeline` is a thin wrapper around ``MiddlewareChain`` that
executes a callable through the chain hooks and returns its result.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable
from typing import Any, cast

from whoosh.middleware.base import Middleware
from whoosh.middleware.chain import MiddlewareChain
from whoosh.middleware.context import MiddlewareContext

logger = logging.getLogger(__name__)

_DEFAULT_BASE_DELAY = 1.0


class RetryMiddleware(Middleware):
    """Retry failing operations with a configurable backoff.

    As a core middleware it advertises its retry policy in the context
    metadata (``retry_attempts`` / ``retry_backoff``) so downstream
    middleware and backends can react to it, and it counts the errors seen
    through :meth:`on_error`.  The :meth:`wrap` helper keeps the historical
    behaviour of retrying a plain callable.

    Args:
        attempts: Maximum number of attempts before giving up.
        backoff: Backoff strategy, one of ``"exponential"``, ``"linear"``
            or anything else for a constant delay.
        jitter: When ``True``, multiply each delay by a random factor in
            ``[0.5, 1.5)`` to avoid thundering-herd effects.
    """

    def __init__(
        self,
        attempts: int = 3,
        backoff: str = "exponential",
        jitter: bool = True,
    ) -> None:
        self._attempts = attempts
        self._backoff = backoff
        self._jitter = jitter
        self._errors = 0

    # -- core hooks ---------------------------------------------------

    def before_index(self, context: MiddlewareContext) -> MiddlewareContext:
        """Publish the retry policy before indexing.

        Args:
            context: The current middleware context.

        Returns:
            The context enriched with the retry policy metadata.
        """
        return self._annotate(context)

    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        """Publish the retry policy before searching.

        Args:
            context: The current middleware context.

        Returns:
            The context enriched with the retry policy metadata.
        """
        return self._annotate(context)

    def on_error(self, context: MiddlewareContext, exc: Exception) -> None:
        """Record the failure and re-raise it.

        Args:
            context: The current middleware context.
            exc: The exception raised by the operation.

        Raises:
            Exception: Always re-raises *exc* so the caller keeps control.
        """
        self._errors += 1
        context.metadata["retry_errors"] = self._errors
        raise exc

    # -- helpers ------------------------------------------------------

    @property
    def errors(self) -> int:
        """Return the number of errors observed through :meth:`on_error`.

        Returns:
            The cumulative error count.
        """
        return self._errors

    def _annotate(self, context: MiddlewareContext) -> MiddlewareContext:
        """Attach the retry policy to the context metadata.

        Args:
            context: The current middleware context.

        Returns:
            The same context instance, mutated in place.
        """
        context.metadata["retry_attempts"] = self._attempts
        context.metadata["retry_backoff"] = self._backoff
        return context

    def wrap(self, operation: Callable[..., Any]) -> Callable[..., Any]:
        """Wrap a callable with retry logic.

        Args:
            operation: The callable to wrap.

        Returns:
            A callable retrying *operation* up to ``attempts`` times with
            backoff between attempts.
        """

        def wrapped(*args: Any, **kwargs: Any) -> Any:
            """Retry *operation* with backoff between attempts."""
            last_exception: Exception | None = None
            for attempt in range(self._attempts):
                try:
                    return operation(*args, **kwargs)
                except Exception as exc:
                    last_exception = exc
                    self._errors += 1
                    if attempt == self._attempts - 1:
                        raise
                    time.sleep(self._calculate_delay(attempt))
            raise last_exception  # type: ignore[misc]

        return wrapped

    def _calculate_delay(self, attempt: int) -> float:
        """Compute the delay for a retry attempt, with optional jitter.

        Args:
            attempt: Zero-indexed attempt number that just failed.

        Returns:
            The number of seconds to wait before the next retry.
        """
        base = _DEFAULT_BASE_DELAY
        if self._backoff == "exponential":
            delay = base * (2.0**attempt)
        elif self._backoff == "linear":
            delay = base * float(attempt + 1)
        else:
            delay = base
        if self._jitter:
            delay *= 0.5 + random.random()
        return delay


class LoggingMiddleware(Middleware):
    """Log operation timings and errors.

    The ``before_*`` hooks stamp a monotonic start time in the context
    metadata, the ``after_*`` hooks log the elapsed duration, and
    :meth:`on_error` logs the failure before re-raising.  :meth:`wrap` keeps
    the historical callable-decorating behaviour.

    Args:
        logger: Logger used to emit records.  Defaults to the
            ``"whoosh_modern"`` logger.
        level: Log level for successful operations.  Defaults to
            :data:`logging.INFO`.
    """

    _START_KEY = "_logging_start"

    def __init__(self, logger: logging.Logger | None = None, level: int | None = None) -> None:
        self._logger = logger or logging.getLogger("whoosh_modern")
        self._level = level if level is not None else logging.INFO

    # -- core hooks ---------------------------------------------------

    def before_index(self, context: MiddlewareContext) -> MiddlewareContext:
        """Start timing an indexing operation.

        Args:
            context: The current middleware context.

        Returns:
            The context carrying the start timestamp.
        """
        return self._start(context)

    def after_index(self, context: MiddlewareContext) -> MiddlewareContext:
        """Log the duration of an indexing operation.

        Args:
            context: The current middleware context.

        Returns:
            The unchanged context.
        """
        return self._finish(context)

    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        """Start timing a search operation.

        Args:
            context: The current middleware context.

        Returns:
            The context carrying the start timestamp.
        """
        return self._start(context)

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        """Log the duration of a search operation.

        Args:
            context: The current middleware context.

        Returns:
            The unchanged context.
        """
        return self._finish(context)

    def on_commit(self, context: MiddlewareContext) -> None:
        """Log a commit event.

        Args:
            context: The current middleware context.
        """
        self._logger.log(self._level, "Commit completed for operation %s", context.operation)

    def on_error(self, context: MiddlewareContext, exc: Exception) -> None:
        """Log the failure and re-raise it.

        Args:
            context: The current middleware context.
            exc: The exception raised by the operation.

        Raises:
            Exception: Always re-raises *exc*.
        """
        self._logger.error("Operation %s failed: %s", context.operation, exc)
        raise exc

    def _start(self, context: MiddlewareContext) -> MiddlewareContext:
        """Store the operation start timestamp in the context metadata.

        Args:
            context: The current middleware context.

        Returns:
            The same context instance, mutated in place.
        """
        context.metadata[self._START_KEY] = time.perf_counter()
        return context

    def _finish(self, context: MiddlewareContext) -> MiddlewareContext:
        """Log the elapsed time recorded by :meth:`_start`.

        Args:
            context: The current middleware context.

        Returns:
            The same context instance.
        """
        start = context.metadata.pop(self._START_KEY, None)
        duration = time.perf_counter() - start if isinstance(start, float) else 0.0
        self._logger.log(
            self._level,
            "Operation %s completed in %.3fs",
            context.operation,
            duration,
        )
        return context

    def wrap(self, operation: Callable[..., Any]) -> Callable[..., Any]:
        """Wrap a callable with timing and error logging.

        Args:
            operation: The callable to wrap.

        Returns:
            A callable logging the execution time and outcome of
            *operation*.
        """

        def wrapped(*args: Any, **kwargs: Any) -> Any:
            """Log the execution time and outcome of *operation*."""
            name = getattr(operation, "__name__", repr(operation))
            start = time.perf_counter()
            try:
                result = operation(*args, **kwargs)
            except Exception as exc:
                self._logger.error(
                    "Operation %s failed after %.3fs: %s",
                    name,
                    time.perf_counter() - start,
                    exc,
                )
                raise
            self._logger.log(
                self._level,
                "Operation %s completed in %.3fs",
                name,
                time.perf_counter() - start,
            )
            return result

        return wrapped


class CacheMiddleware(Middleware):
    """Cache results to avoid redundant computation.

    In the core chain the cache is keyed on ``context.query``:
    :meth:`before_search` injects a previously stored result into
    ``context.results`` (also flagged in ``context.metadata["_cached"]``) and
    :meth:`after_search` stores fresh results.  :meth:`wrap` keeps the
    historical behaviour of caching a callable's result keyed on its
    arguments.  Both paths share the same bounded store and statistics.

    Args:
        maxsize: Maximum number of cached entries.  When full, the oldest
            entry (insertion order) is evicted.
    """

    def __init__(self, maxsize: int = 128) -> None:
        self._cache: dict[str, Any] = {}
        self._maxsize = maxsize
        self._hits = 0
        self._misses = 0

    # -- core hooks ---------------------------------------------------

    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        """Serve a cached result for the context query when available.

        Args:
            context: The current middleware context.

        Returns:
            The context, possibly populated with the cached results.
        """
        key = self._query_key(context)
        if key is not None and key in self._cache:
            self._hits += 1
            context.results = self._cache[key]
            context.metadata["_cached"] = True
        return context

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        """Store the search results for the context query.

        Args:
            context: The current middleware context.

        Returns:
            The unchanged context.
        """
        key = self._query_key(context)
        if key is None or context.results is None:
            return context
        if context.metadata.get("_cached"):
            return context
        self._misses += 1
        self._store(key, context.results)
        return context

    def _query_key(self, context: MiddlewareContext) -> str | None:
        """Build the cache key for a context.

        Args:
            context: The current middleware context.

        Returns:
            The cache key, or ``None`` when the context has no query.
        """
        return f"query:{context.query}" if context.query else None

    def _store(self, key: str, value: Any) -> None:
        """Insert an entry, evicting the oldest one when full.

        Args:
            key: Cache key.
            value: Value to cache.
        """
        if key not in self._cache and len(self._cache) >= self._maxsize:
            del self._cache[next(iter(self._cache))]
        self._cache[key] = value

    def wrap(self, operation: Callable[..., Any]) -> Callable[..., Any]:
        """Wrap a callable with result caching.

        Args:
            operation: The callable to wrap.

        Returns:
            A callable caching results keyed on the operation's module,
            qualified name, and argument representation.
        """

        def wrapped(*args: Any, **kwargs: Any) -> Any:
            """Return a cached result for *operation* or compute and cache it."""
            module = getattr(operation, "__module__", "?")
            qualname = getattr(operation, "__qualname__", repr(operation))
            key = f"{module}.{qualname}:{args!r}:{kwargs!r}"
            if key in self._cache:
                self._hits += 1
                return self._cache[key]
            result = operation(*args, **kwargs)
            self._misses += 1
            self._store(key, result)
            return result

        return wrapped

    @property
    def stats(self) -> dict[str, int]:
        """Return cache statistics.

        Returns:
            A dictionary with the ``"hits"``, ``"misses"`` and ``"size"``
            keys describing the current cache state.
        """
        return {"hits": self._hits, "misses": self._misses, "size": len(self._cache)}

    def clear(self) -> None:
        """Clear all cached entries and reset the hit/miss counters."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0


class MiddlewarePipeline:
    """Execute a callable through a core :class:`MiddlewareChain`.

    The pipeline registers every middleware in a ``MiddlewareChain`` and runs
    the ``before_search``/``after_search`` hooks around the operation.  For
    backwards compatibility, middleware exposing a ``wrap`` callable (such as
    :class:`RetryMiddleware` or :class:`LoggingMiddleware`) also decorate the
    operation itself, the first middleware being the outermost layer.

    Args:
        *middlewares: Middleware instances applied in order.
    """

    def __init__(self, *middlewares: Middleware) -> None:
        self._middlewares: tuple[Middleware, ...] = middlewares
        self._chain = MiddlewareChain(list(middlewares))

    @property
    def chain(self) -> MiddlewareChain:
        """Return the underlying core middleware chain.

        Returns:
            The :class:`whoosh.middleware.chain.MiddlewareChain` instance.
        """
        return self._chain

    def execute(self, operation: Callable[..., Any]) -> Any:
        """Execute an operation through the middleware chain.

        Args:
            operation: The zero-argument callable to execute.

        Returns:
            The value returned by *operation*.

        Raises:
            Exception: Any exception raised by *operation* after the
                ``on_error`` hooks have been notified.
        """
        wrapped = operation
        for middleware in reversed(self._middlewares):
            wrap = getattr(middleware, "wrap", None)
            if callable(wrap):
                wrapped = cast("Callable[..., Any]", wrap(wrapped))

        context = MiddlewareContext("execute")
        context = self._chain.run_before("before_search", context)
        try:
            result = wrapped()
        except Exception as exc:
            self._chain.run_on_error(context, exc, fail_open=True)
            raise
        context.results = result
        self._chain.run_after("after_search", context)
        return result


__all__ = [
    "RetryMiddleware",
    "LoggingMiddleware",
    "CacheMiddleware",
    "MiddlewarePipeline",
]
