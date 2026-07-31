"""Middleware pipeline for resilience: retry, caching, logging."""

import logging
import random
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class Middleware(ABC):
    """Base middleware class."""

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
