"""Engine for building a ``SyncStorageProvider`` from ``WhooshNGConfig.storage``.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any

from whoosh_modern.config.models import WhooshNGConfig
from whoosh_modern.storage import FileStorage, HybridStorage


class StorageEngine:
    """Build a ``SyncStorageProvider`` from ``WhooshNGConfig.storage``.

    Attributes:
        _config: The merged application configuration.
    """

    def __init__(self, config: WhooshNGConfig) -> None:
        """Initialize the engine with a merged configuration.

        Args:
            config: Merged Whoosh-NG configuration.
        """
        self._config = config

    def build(self) -> Any:
        """Build a SyncStorageProvider from the configured storage backend.

        Returns:
            A SyncStorageProvider instance.

        Raises:
            ValueError: If the storage configuration is invalid.
        """
        storage_config = self._config.storage
        storage_type = storage_config.type.lower()
        if storage_type == "file":
            path = storage_config.path or "./index"
            return FileStorage(path)
        if storage_type == "s3":
            try:
                from whoosh_modern.storage import S3Storage
            except ImportError as exc:
                raise ImportError(
                    "S3 storage requires boto3. Install with: pip install whoosh-ng[s3]"
                ) from exc
            bucket = storage_config.bucket
            if not bucket:
                raise ValueError("S3 storage requires a non-empty 'bucket'")
            return S3Storage(
                bucket=bucket,
                prefix=storage_config.prefix,
            )
        if storage_type == "hybrid":
            try:
                from whoosh_modern.storage import S3Storage
            except ImportError as exc:
                raise ImportError(
                    "Hybrid storage requires boto3. Install with: pip install whoosh-ng[s3]"
                ) from exc
            bucket = storage_config.bucket
            if not bucket:
                raise ValueError("Hybrid storage requires a non-empty 'bucket'")
            local_cache = storage_config.path or "./cache"
            remote = S3Storage(
                bucket=bucket,
                prefix=storage_config.prefix,
            )
            return HybridStorage(local_cache=local_cache, remote=remote)
        raise ValueError(f"Unsupported storage type: {storage_type}")
