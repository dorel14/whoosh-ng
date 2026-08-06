"""Storage providers."""

from __future__ import annotations

from typing import Any

from whoosh_modern.storage.async_file import AsyncFileStorage

__all__ = ["AsyncFileStorage"]


def __getattr__(name: str) -> Any:
    if name == "FileStorage":
        from whoosh_modern.application import FileStorage

        return FileStorage
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
