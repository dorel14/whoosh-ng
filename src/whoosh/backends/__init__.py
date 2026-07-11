from __future__ import annotations

from whoosh.backends.abc import Backend
from whoosh.backends.file import FileBackend
from whoosh.registry import BackendRegistry

__all__ = [
    "Backend",
    "FileBackend",
    "BackendRegistry",
]

# Eagerly register the built-in file backend so it is available by name.
BackendRegistry.register("file", FileBackend, "whoosh")
