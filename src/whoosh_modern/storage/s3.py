"""S3-backed storage providers (direct and snapshot strategies).

This module exposes :class:`S3Storage` (a thin alias over
:class:`~whoosh_modern.middleware.storage.S3StorageProvider`) and
:class:`SnapshotStorage`, which downloads segments into local temporary files
on read.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any

from whoosh_modern.middleware.storage import S3StorageProvider


class S3Storage(S3StorageProvider):
    """S3 (or S3-compatible) backed storage provider.

    This is a thin alias over
    :class:`~whoosh_modern.middleware.storage.S3StorageProvider` so users can
    import ``S3Storage`` from ``whoosh_modern.storage`` directly.

    ``boto3`` is an optional dependency: it is imported lazily by the parent
    class so the rest of Whoosh-NG does not require it. A custom
    ``client`` may be injected for testing.

    Example::

        from whoosh_modern.storage import S3Storage

        storage = S3Storage(bucket="my-index-bucket", prefix="segments")
        storage.write("segment_1.dat", b"binary-segment-data")
        data = storage.read("segment_1.dat")
        storage.delete("segment_1.dat")
        keys = storage.list_keys()

    Args:
        bucket: Name of the S3 bucket to use.
        prefix: Optional key prefix applied to every logical key. Leading and
            trailing slashes are stripped.
        client: Optional pre-configured ``boto3`` S3 client. When ``None`` (the
            default) a client is created via ``boto3.client("s3")``.

    Raises:
        ImportError: If ``boto3`` is not installed and no ``client`` is
            provided.
    """


class SnapshotStorage(S3StorageProvider):
    """Simple S3 snapshot storage without a local cache.

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

    Args:
        local_path: Local filesystem path used as scratch space for temporary
            files created during reads.
        bucket: Name of the S3 bucket to use.
        prefix: Optional key prefix applied to every logical key. Leading and
            trailing slashes are stripped.
        client: Optional pre-configured ``boto3`` S3 client. When ``None`` (the
            default) a client is created via ``boto3.client("s3")``.

    Raises:
        ImportError: If ``boto3`` is not installed and no ``client`` is
            provided.
    """

    def __init__(
        self,
        local_path: str,
        bucket: str,
        prefix: str = "",
        client: Any | None = None,
    ) -> None:
        """Initialize the snapshot storage provider.

        Args:
            local_path: Local filesystem path used as scratch space for
                temporary files created during reads.
            bucket: Name of the S3 bucket to use.
            prefix: Optional key prefix applied to every logical key. Leading
                and trailing slashes are stripped.
            client: Optional pre-configured ``boto3`` S3 client. When ``None``
                (the default) a client is created via
                ``boto3.client("s3")``.

        Raises:
            ImportError: If ``boto3`` is not installed and no ``client`` is
                provided.
        """
        self._local_path = local_path
        super().__init__(bucket=bucket, prefix=prefix, client=client)
