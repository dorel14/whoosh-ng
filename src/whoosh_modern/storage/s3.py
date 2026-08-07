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


class SnapshotStorage(S3StorageProvider):
    """Simple S3 snapshot storage without local cache.

    This is the simplest S3-backed storage strategy:

    - Write: upload segment directly to S3
    - Read: download segment from S3 to local temporary file

    Use this when you want S3 as a simple backup/restore target without
    the complexity of a local cache.

    Example::

        from whoosh_modern.storage import SnapshotStorage

        storage = SnapshotStorage(
            local_path="./index",
            bucket="my-index-bucket",
            prefix="snapshots",
        )
        storage.write("segment_1.dat", b"binary-segment-data")
        data = storage.read("segment_1.dat")
    """

    def __init__(
        self,
        local_path: str,
        bucket: str,
        prefix: str = "",
        client: Any | None = None,
    ) -> None:
        self._local_path = local_path
        super().__init__(bucket=bucket, prefix=prefix, client=client)
