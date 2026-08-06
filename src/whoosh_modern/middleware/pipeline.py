"""Middleware pipeline for resilience: retry, caching, logging.

This module is imported as ``whoosh_modern.middleware`` (the package
``__init__`` re-exports these names) so legacy imports keep working while the
package also hosts the hook-based middleware (storage/search/analyzer) that
subclass :class:`whoosh.middleware.base.Middleware`.
"""

import logging
import random
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class Middleware(ABC):
    """Base middleware class for the resilience pipeline (wrap-style)."""

    @abstractmethod
    def wrap(self, operation: Callable[..., Any]) -> Callable[..., Any]:
        """Wrap an operation with middleware logic."""


class RetryMiddleware(Middleware):
    """Retry failed operations with exponential backoff."""

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
        """Wrap operation with retry logic."""

        def wrapped(*args: Any, **kwargs: Any) -> Any:
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
        """Calculate delay for a given retry attempt with optional jitter."""
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
    """Log operation execution times and errors."""

    def __init__(self, logger: logging.Logger | None = None, level: int | None = None) -> None:
        self._logger = logger or logging.getLogger("whoosh_modern")
        self._level = level or logging.INFO

    def wrap(self, operation: Callable[..., Any]) -> Callable[..., Any]:
        """Wrap operation with logging."""

        def wrapped(*args: Any, **kwargs: Any) -> Any:
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
    """Cache operation results to avoid redundant computation."""

    def __init__(self, maxsize: int = 128) -> None:
        self._cache: dict[str, Any] = {}
        self._maxsize = maxsize
        self._hits = 0
        self._misses = 0

    def wrap(self, operation: Callable[..., Any]) -> Callable[..., Any]:
        cache = self._cache
        maxsize = self._maxsize

        def wrapped(*args: Any, **kwargs: Any) -> Any:
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
        """Return cache statistics."""
        return {"hits": self._hits, "misses": self._misses, "size": len(self._cache)}

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0


class MiddlewarePipeline:
    """Chain multiple middlewares together."""

    def __init__(self, *middlewares: Middleware) -> None:
        self._middlewares = middlewares

    def execute(self, operation: Callable[..., Any]) -> Any:
        """Execute an operation through the middleware chain."""
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
