"""Storage providers for Whoosh-NG.

Provides local file, S3, and hybrid (cache + remote) storage backends.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any

from whoosh_modern.storage.async_file import AsyncFileStorage
from whoosh_modern.storage.hybrid import AsyncHybridStorage, HybridStorage
from whoosh_modern.storage.s3 import S3Storage, SnapshotStorage

__all__ = [
    "AsyncFileStorage",
    "AsyncHybridStorage",
    "CachedObjectStorage",
    "HybridStorage",
    "S3Storage",
    "SnapshotStorage",
]


def __getattr__(name: str) -> Any:
    """Provide lazy access to deprecated/compat attribute names.

    Args:
        name: The attribute name being accessed.

    Returns:
        The resolved object.

    Raises:
        AttributeError: If the attribute does not exist.
    """
    if name == "CachedObjectStorage":
        return HybridStorage
    if name == "FileStorage":
        from whoosh_modern.application import FileStorage

        return FileStorage
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
