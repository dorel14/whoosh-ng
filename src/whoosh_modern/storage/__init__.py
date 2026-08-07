"""Storage providers."""

from __future__ import annotations

from typing import Any

from whoosh_modern.storage.async_file import AsyncFileStorage
from whoosh_modern.storage.hybrid import AsyncHybridStorage, HybridStorage
from whoosh_modern.storage.s3 import S3Storage

__all__ = [
    "AsyncFileStorage",
    "AsyncHybridStorage",
    "HybridStorage",
    "S3Storage",
]


def __getattr__(name: str) -> Any:
    if name == "FileStorage":
        from whoosh_modern.application import FileStorage

        return FileStorage
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
