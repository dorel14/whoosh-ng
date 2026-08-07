"""Whoosh-NG modern middleware package.

Re-exports the resilience pipeline (:class:`Middleware`, :class:`RetryMiddleware`,
:class:`LoggingMiddleware`, :class:`CacheMiddleware`, :class:`MiddlewarePipeline`)
and the hook-based business middleware (:class:`StorageMiddleware`,
:class:`SearchMiddleware`, :class:`AnalyzerMiddleware` and friends) which subclass
:class:`whoosh.middleware.base.Middleware`.
"""

from __future__ import annotations

from whoosh_modern.middleware.analyzer import (
    AnalyzerMiddleware,
    StemmingMiddleware,
    SynonymMiddleware,
)
from whoosh_modern.middleware.pipeline import (
    CacheMiddleware,
    LoggingMiddleware,
    Middleware,
    MiddlewarePipeline,
    RetryMiddleware,
)
from whoosh_modern.middleware.search import (
    QueryRewriteMiddleware,
    RankingMiddleware,
    SearchMiddleware,
)
from whoosh_modern.middleware.storage import (
    FileStorageProvider,
    S3StorageProvider,
    SQLiteStorageProvider,
    StorageMiddleware,
)

__all__ = [
    # resilience pipeline (legacy)
    "Middleware",
    "RetryMiddleware",
    "LoggingMiddleware",
    "CacheMiddleware",
    "MiddlewarePipeline",
    # storage middleware
    "StorageMiddleware",
    "FileStorageProvider",
    "SQLiteStorageProvider",
    "S3StorageProvider",
    # search middleware
    "SearchMiddleware",
    "QueryRewriteMiddleware",
    "RankingMiddleware",
    # analyzer middleware
    "AnalyzerMiddleware",
    "StemmingMiddleware",
    "SynonymMiddleware",
]
