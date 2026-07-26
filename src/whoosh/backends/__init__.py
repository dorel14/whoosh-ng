from __future__ import annotations

from whoosh.backends.abc import Backend
from whoosh.backends.file import FileBackend
from whoosh.backends.lmdb import LmdbBackend
from whoosh.registry import BackendRegistry

__all__ = [
    "Backend",
    "FileBackend",
    "LmdbBackend",
    "BackendRegistry",
]

# Eagerly register the built-in file backend so it is available by name.
BackendRegistry.register("file", FileBackend, "whoosh")
BackendRegistry.register("lmdb", LmdbBackend, "whoosh")
