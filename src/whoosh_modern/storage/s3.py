"""S3-backed storage providers (direct and snapshot strategies).

This module exposes :class:`S3Storage` (a thin alias over
:class:`~whoosh_modern.middleware.storage.S3StorageProvider`) and
:class:`SnapshotStorage`, which downloads segments into local scratch files on
read so the remote remains the source of truth while reads are served from a
local copy.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

import os

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
    """S3 snapshot storage with a local scratch copy on read.

    The remote S3 bucket remains the source of truth. On ``read`` the object is
    downloaded from S3 and also persisted into ``local_path`` so subsequent
    reads of the same key can be served from the local scratch copy.

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
        client: object | None = None,
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
        self._local_path = os.path.abspath(local_path)
        os.makedirs(self._local_path, exist_ok=True)
        super().__init__(bucket=bucket, prefix=prefix, client=client)

    def _safe_local_path(self, key: str) -> str:
        """Build a sanitized local filesystem path for ``key``.

        The key is validated to reject directory traversal (``..``) segments
        and absolute path components before being joined onto
        ``local_path``. The resulting path is also verified to resolve to a
        location inside ``local_path`` as a defense-in-depth measure against
        symlink or normalization tricks.

        Args:
            key: The blob key.

        Returns:
            The absolute local filesystem path corresponding to ``key``.

        Raises:
            ValueError: If ``key`` contains a ``..`` path segment, an
                absolute path component, or otherwise resolves outside of
                ``local_path``.
        """
        normalized_key = key.replace("\\", "/")
        segments = normalized_key.split("/")
        if ".." in segments:
            raise ValueError(f"Invalid key {key!r}: path traversal ('..') is not allowed")
        if os.path.isabs(normalized_key) or (len(normalized_key) > 1 and normalized_key[1] == ":"):
            raise ValueError(f"Invalid key {key!r}: absolute paths are not allowed")

        candidate = os.path.normpath(os.path.join(self._local_path, normalized_key.replace("/", os.sep)))
        local_root = os.path.normpath(self._local_path)
        if candidate != local_root and not candidate.startswith(local_root + os.sep):
            raise ValueError(f"Invalid key {key!r}: resolves outside of local_path")
        return candidate

    def read(self, key: str) -> bytes:
        """Read the object for ``key`` from S3 and cache it locally.

        Args:
            key: The blob key.

        Returns:
            The raw bytes stored in the S3 object, also persisted under
            ``local_path``.

        Raises:
            ValueError: If ``key`` attempts to traverse outside of
                ``local_path`` via ``..`` segments or absolute path
                components.
        """
        data = super().read(key)
        path = self._safe_local_path(key)
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(data)
        return data


__all__ = ["S3Storage", "SnapshotStorage"]
