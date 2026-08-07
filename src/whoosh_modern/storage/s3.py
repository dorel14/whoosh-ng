"""S3Storage wraps S3StorageProvider as a SyncStorageProvider alias."""

from __future__ import annotations

from whoosh_modern.middleware.storage import S3StorageProvider


class S3Storage(S3StorageProvider):
    """S3-backed storage provider.

    This is a thin alias over :class:`~whoosh_modern.middleware.storage.S3StorageProvider`
    so users can import ``S3Storage`` from ``whoosh_modern.storage``.
    """
