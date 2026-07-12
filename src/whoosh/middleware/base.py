from __future__ import annotations

from typing import Any

from whoosh.middleware.context import MiddlewareContext
from whoosh.middleware.exceptions import MiddlewareError, StopOperation


class Middleware:
    """Base class for Whoosh middleware.

    Middleware can hook into the indexing and search pipeline.
    Supports both sync and async hooks via inspect.isawaitable detection.
    """

    def startup(self, context: MiddlewareContext) -> None:
        """Called once when the middleware is initialized."""
        pass

    def shutdown(self, context: MiddlewareContext) -> None:
        """Called once when the middleware is being torn down."""
        pass

    def before_index(self, context: MiddlewareContext) -> MiddlewareContext:
        """Called before a document is indexed."""
        return context

    def after_index(self, context: MiddlewareContext) -> MiddlewareContext:
        """Called after a document is indexed."""
        return context

    def before_delete(self, context: MiddlewareContext) -> MiddlewareContext:
        """Called before a document is deleted."""
        return context

    def after_delete(self, context: MiddlewareContext) -> MiddlewareContext:
        """Called after a document is deleted."""
        return context

    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        """Called before a search query is executed."""
        return context

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        """Called after a search query is executed."""
        return context

    def on_error(self, context: MiddlewareContext, exc: Exception) -> None:
        """Called when an exception occurs during indexing or search."""
        raise exc

    def on_commit(self, context: MiddlewareContext) -> None:
        """Called after a commit operation."""
        pass


class CompressionMiddleware(Middleware):
    """Middleware that marks documents for compression at the backend level.

    Note: Compression should be applied at the storage/backend level, not on
    the raw document. This middleware marks documents with a flag for the backend
    to apply compression.
    """

    def before_index(self, context: MiddlewareContext) -> MiddlewareContext:
        if context.document is not None:
            context.document["_compressed"] = True
        return context


class EncryptionMiddleware(Middleware):
    """Middleware that marks documents for encryption at the backend level.

    Note: Encryption should be applied at the storage/backend level with explicit
    key management, not on the raw document. This middleware marks documents
    with a flag for the backend to apply encryption.
    """

    def before_index(self, context: MiddlewareContext) -> MiddlewareContext:
        if context.document is not None:
            context.document["_encrypted"] = True
        return context


class MetricsMiddleware(Middleware):
    """Middleware that tracks indexing and search metrics internally."""

    def __init__(self) -> None:
        self._metrics: dict[str, int] = {}

    def after_index(self, context: MiddlewareContext) -> MiddlewareContext:
        self._metrics["documents_indexed"] = self._metrics.get("documents_indexed", 0) + 1
        return context

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        self._metrics["searches_executed"] = self._metrics.get("searches_executed", 0) + 1
        return context

    def get_metrics(self) -> dict[str, int]:
        return dict(self._metrics)


class CacheMiddleware(Middleware):
    """Middleware that provides a simple in-memory search cache."""

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}

    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        if context.query and context.query in self._cache:
            context.metadata["_cached"] = self._cache[context.query]
        return context

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        if context.query and context.results is not None:
            self._cache[context.query] = context.results
        return context

    def get_cached(self, query: str) -> Any | None:
        return self._cache.get(query)

    def set_cached(self, query: str, results: Any) -> None:
        self._cache[query] = results


__all__ = [
    "Middleware",
    "CompressionMiddleware",
    "EncryptionMiddleware",
    "MetricsMiddleware",
    "CacheMiddleware",
]
