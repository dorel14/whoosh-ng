"""Storage providers for Whoosh-NG.

Provides local file, S3, and hybrid (cache + remote) storage backends.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from whoosh_modern.middleware.storage import FileStorageProvider
from whoosh_modern.storage.async_file import AsyncFileStorage
from whoosh_modern.storage.hybrid import AsyncHybridStorage, HybridStorage
from whoosh_modern.storage.s3 import S3Storage, SnapshotStorage

FileStorage = FileStorageProvider
CachedObjectStorage = HybridStorage

__all__ = [
    "AsyncFileStorage",
    "AsyncHybridStorage",
    "CachedObjectStorage",
    "FileStorage",
    "FileStorageProvider",
    "HybridStorage",
    "S3Storage",
    "SnapshotStorage",
]
