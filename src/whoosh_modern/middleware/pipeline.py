"""Middleware pipeline for resilience: retry, caching, logging.

This module is imported as ``whoosh_modern.middleware`` (the package
``__init__`` re-exports these names) so legacy imports keep working while the
package also hosts the hook-based middleware (storage/search/analyzer) that
subclass :class:`whoosh.middleware.base.Middleware`.

Author: dorel14
Version: 3.0.0
"""

import logging
import random
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class Middleware(ABC):
    """Base middleware class for the resilience pipeline (wrap-style).

    Each subclass implements :meth:`wrap` to decorate an arbitrary operation
    callable, returning a new callable that adds cross-cutting behaviour such
    as retry, logging, or caching.
    """

    @abstractmethod
    def wrap(self, operation: Callable[..., Any]) -> Callable[..., Any]:
        """Wrap an operation with middleware logic.

        Args:
            operation: The callable to wrap.

        Returns:
            A callable that wraps *operation* with the middleware behaviour.
        """


class RetryMiddleware(Middleware):
    """Retry failed operations with exponential backoff.

    Args:
        attempts: Maximum number of attempts before giving up.
        backoff: Backoff strategy, one of ``"exponential"``,
            ``"linear"``, or ``"constant"``.
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

    def wrap(self, operation: Callable[..., Any]) -> Callable[..., Any]:
        """Wrap operation with retry logic.

        Args:
            operation: The callable to wrap.

        Returns:
            A callable that retries *operation* up to ``attempts`` times
            with backoff between attempts.
        """

        def wrapped(*args: Any, **kwargs: Any) -> Any:
            """Retry *operation* with backoff between attempts."""
            last_exception: Exception | None = None
            for attempt in range(self._attempts):
                try:
                    return operation(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == self._attempts - 1:
                        raise
                    delay = self._calculate_delay(attempt)
                    time.sleep(delay)
            raise last_exception  # type: ignore[misc]

        return wrapped

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given retry attempt with optional jitter.

        Args:
            attempt: Zero-indexed attempt number that just failed.

        Returns:
            The number of seconds to wait before the next retry.
        """
        base: float = 1.0
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
    """Log operation execution times and errors.

    Args:
        logger: A standard :class:`logging.Logger` instance to emit records
            to.  If ``None``, the ``"whoosh_modern"`` logger is used.
        level: Log level for successful operations.  Defaults to
            :data:`logging.INFO`.
    """

    def __init__(self, logger: logging.Logger | None = None, level: int | None = None) -> None:
        self._logger = logger or logging.getLogger("whoosh_modern")
        self._level = level or logging.INFO

    def wrap(self, operation: Callable[..., Any]) -> Callable[..., Any]:
        """Wrap operation with logging.

        Args:
            operation: The callable to wrap.

        Returns:
            A callable that logs the execution time and outcome of
            *operation*.
        """

        def wrapped(*args: Any, **kwargs: Any) -> Any:
            """Log the execution time and outcome of *operation*."""
            start = time.time()
            try:
                result = operation(*args, **kwargs)
                duration = time.time() - start
                self._logger.log(
                    self._level,
                    "Operation %s completed in %.3fs",
                    operation.__name__,
                    duration,
                )
                return result
            except Exception as e:
                duration = time.time() - start
                self._logger.error(
                    "Operation %s failed after %.3fs: %s",
                    operation.__name__,
                    duration,
                    e,
                )
                raise

        return wrapped


class CacheMiddleware(Middleware):
    """Cache operation results to avoid redundant computation.

    Args:
        maxsize: Maximum number of cached entries.  When the cache is full
            and a new entry is added, the oldest entry (insertion order) is
            evicted.
    """

    def __init__(self, maxsize: int = 128) -> None:
        self._cache: dict[str, Any] = {}
        self._maxsize = maxsize
        self._hits = 0
        self._misses = 0

    def wrap(self, operation: Callable[..., Any]) -> Callable[..., Any]:
        """Wrap operation with caching.

        Args:
            operation: The callable to wrap.

        Returns:
            A callable that caches results keyed on the operation's module,
            qualified name, and argument representation.
        """
        cache = self._cache
        maxsize = self._maxsize

        def wrapped(*args: Any, **kwargs: Any) -> Any:
            """Return a cached result for *operation* or compute and cache it."""
            key = f"{operation.__module__}.{operation.__qualname__}:{args!r}:{kwargs!r}"
            if key in cache:
                self._hits += 1
                return cache[key]
            result = operation(*args, **kwargs)
            self._misses += 1
            if len(cache) >= maxsize:
                oldest = next(iter(cache))
                del cache[oldest]
            cache[key] = result
            return result

        return wrapped

    @property
    def stats(self) -> dict[str, int]:
        """Return cache statistics.

        Returns:
            A dictionary with keys ``"hits"``, ``"misses"``, and ``"size"``
            describing the current state of the cache.
        """
        return {"hits": self._hits, "misses": self._misses, "size": len(self._cache)}

    def clear(self) -> None:
        """Clear all cached entries.

        Resets the cache contents and the hit/miss counters to zero.
        """
        self._cache.clear()
        self._hits = 0
        self._misses = 0


class MiddlewarePipeline:
    """Chain multiple middlewares together.

    Args:
        *middlewares: One or more :class:`Middleware` instances that will be
            applied in order so that the first middleware wraps the closest
            to the outermost layer.
    """

    def __init__(self, *middlewares: Middleware) -> None:
        self._middlewares = middlewares

    def execute(self, operation: Callable[..., Any]) -> Any:
        """Execute an operation through the middleware chain.

        Args:
            operation: The callable to execute.

        Returns:
            The return value of *operation* after it has been wrapped by
            every middleware in the chain.
        """
        wrapped = operation
        for mw in reversed(self._middlewares):
            wrapped = mw.wrap(wrapped)
        return wrapped()


__all__ = [
    "Middleware",
    "RetryMiddleware",
    "LoggingMiddleware",
    "CacheMiddleware",
    "MiddlewarePipeline",
]
