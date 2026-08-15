"""Whoosh-NG modern middleware package.

Re-exports the core hook-based base class
(:class:`whoosh.middleware.base.Middleware`) so that
``from whoosh_modern.middleware import Middleware`` always resolves to the core
class, plus the resilience middleware built on top of it
(:class:`RetryMiddleware`, :class:`LoggingMiddleware`, :class:`CacheMiddleware`,
:class:`MiddlewarePipeline`) and the business middleware
(:class:`StorageMiddleware`, :class:`SearchMiddleware`,
:class:`AnalyzerMiddleware` and friends).

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from whoosh.middleware.base import Middleware
from whoosh_modern.middleware.analyzer import (
    AnalyzerMiddleware,
    StemmingMiddleware,
    SynonymMiddleware,
)
from whoosh_modern.middleware.embedding import EmbeddingMiddleware
from whoosh_modern.middleware.resilience import (
    CacheMiddleware,
    LoggingMiddleware,
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
    # core base class (re-export)
    "Middleware",
    # resilience middleware
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
    # embedding middleware
    "EmbeddingMiddleware",
]
