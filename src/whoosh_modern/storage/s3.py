"""S3Storage wraps S3StorageProvider as a SyncStorageProvider alias."""

from __future__ import annotations

from whoosh_modern.middleware.storage import S3StorageProvider


class S3Storage(S3StorageProvider):
    """S3-backed storage provider.

    This is a thin alias over :class:`~whoosh_modern.middleware.storage.S3StorageProvider`
    so users can import ``S3Storage`` from ``whoosh_modern.storage``.

    Example::

        from whoosh_modern.storage import S3Storage

        storage = S3Storage(bucket="my-index-bucket", prefix="segments")
        storage.write("segment_1.dat", b"binary-segment-data")
        data = storage.read("segment_1.dat")
        storage.delete("segment_1.dat")
        keys = storage.list_keys()
    """
