from __future__ import annotations

from typing import Any

from whoosh.middleware.base import Middleware
from whoosh.middleware.context import MiddlewareContext
from whoosh.middleware.exceptions import MiddlewareError


class MiddlewareRegistry:
    """Central registry for middleware components."""

    _middlewares: dict[str, Middleware] = {}

    @classmethod
    def register(cls, name: str, middleware: Middleware, owner: str = "") -> None:
        cls._middlewares[name] = middleware
        middleware.startup(MiddlewareContext(f"register_{name}"))

    @classmethod
    def unregister(cls, name: str) -> Middleware | None:
        return cls._middlewares.pop(name, None)

    @classmethod
    def get(cls, name: str) -> Middleware | None:
        return cls._middlewares.get(name)

    @classmethod
    def list_all(cls) -> list[str]:
        return list(cls._middlewares)

    @classmethod
    def clear(cls) -> None:
        cls._middlewares.clear()


__all__ = ["MiddlewareRegistry"]
