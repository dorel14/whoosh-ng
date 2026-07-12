from __future__ import annotations

from typing import Any


class MiddlewareContext:
    """Context object passed to middleware hooks.

    Contains all information about the current operation without passing many arguments.
    """

    def __init__(self, operation: str) -> None:
        self.operation = operation
        self.index: Any = None
        self.backend: Any = None
        self.writer: Any = None
        self.searcher: Any = None
        self.document: dict[str, Any] | None = None
        self.query: str = ""
        self.collector: Any = None
        self.results: Any = None
        self.labels: dict[str, Any] = {}
        self.metadata: dict[str, Any] = {}

    def copy(self) -> MiddlewareContext:
        """Create a shallow copy of the context."""
        ctx = MiddlewareContext(self.operation)
        ctx.index = self.index
        ctx.backend = self.backend
        ctx.writer = self.writer
        ctx.searcher = self.searcher
        ctx.document = self.document
        ctx.query = self.query
        ctx.collector = self.collector
        ctx.results = self.results
        ctx.labels = dict(self.labels)
        ctx.metadata = dict(self.metadata)
        return ctx


__all__ = ["MiddlewareContext"]
