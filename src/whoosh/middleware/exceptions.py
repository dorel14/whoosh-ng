from __future__ import annotations


class StopOperation(Exception):
    """Raised by middleware to stop an indexing or search operation."""

    def __init__(self, message: str = "Operation stopped by middleware") -> None:
        self.message = message
        super().__init__(message)


class MiddlewareError(Exception):
    """Raised when a middleware fails and fail_open is False."""

    pass


__all__ = ["StopOperation", "MiddlewareError"]
