from __future__ import annotations

import inspect
from typing import Any

from whoosh.middleware.base import Middleware
from whoosh.middleware.context import MiddlewareContext
from whoosh.middleware.exceptions import MiddlewareError, StopOperation


class MiddlewareChain:
    """Ordered chain of middleware with before/after hook execution.

    Execution order:
    - Before hooks: middleware_1.before -> middleware_2.before -> ... -> core
    - After hooks (reverse): ... -> middleware_2.after -> middleware_1.after
    """

    def __init__(self, middlewares: list[Middleware] | None = None) -> None:
        self._middlewares: list[Middleware] = middlewares or []

    def add(self, middleware: Middleware) -> None:
        """Add a middleware to the end of the chain."""
        self._middlewares.append(middleware)

    def extend(self, middlewares: list[Middleware]) -> None:
        """Add multiple middlewares to the chain."""
        self._middlewares.extend(middlewares)

    def run_before(
        self, hook_name: str, context: MiddlewareContext, fail_open: bool = False
    ) -> MiddlewareContext:
        """Execute before_* hooks in order."""
        for middleware in self._middlewares:
            hook = getattr(middleware, hook_name, None)
            if hook is None:
                continue
            result = hook(context)
            if inspect.isawaitable(result):
                raise RuntimeError(
                    f"Middleware {middleware.__class__.__name__}.{hook_name} is async; use async_run_before"
                )
            if isinstance(result, MiddlewareContext):
                context = result
        return context

    async def async_run_before(
        self, hook_name: str, context: MiddlewareContext, fail_open: bool = False
    ) -> MiddlewareContext:
        """Execute before_* hooks in order (async version)."""
        for middleware in self._middlewares:
            hook = getattr(middleware, hook_name, None)
            if hook is None:
                continue
            result = hook(context)
            if inspect.isawaitable(result):
                result = await result  # type: ignore[misc]
            if isinstance(result, MiddlewareContext):
                context = result
        return context

    def run_after(
        self, hook_name: str, context: MiddlewareContext, fail_open: bool = False
    ) -> MiddlewareContext:
        """Execute after_* hooks in reverse order."""
        for middleware in reversed(self._middlewares):
            hook = getattr(middleware, hook_name, None)
            if hook is None:
                continue
            result = hook(context)
            if inspect.isawaitable(result):
                raise RuntimeError(
                    f"Middleware {middleware.__class__.__name__}.{hook_name} is async; use async_run_after"
                )
            if isinstance(result, MiddlewareContext):
                context = result
        return context

    async def async_run_after(
        self, hook_name: str, context: MiddlewareContext, fail_open: bool = False
    ) -> MiddlewareContext:
        """Execute after_* hooks in reverse order (async version)."""
        for middleware in reversed(self._middlewares):
            hook = getattr(middleware, hook_name, None)
            if hook is None:
                continue
            result = hook(context)
            if inspect.isawaitable(result):
                result = await result  # type: ignore[misc]
            if isinstance(result, MiddlewareContext):
                context = result
        return context

    async def run_hook(
        self, hook_name: str, context: MiddlewareContext, fail_open: bool = False
    ) -> MiddlewareContext:
        """Execute a single hook on all middleware in order."""
        return await self.async_run_before(hook_name, context, fail_open)

    def run_on_error(
        self, context: MiddlewareContext, exc: Exception, fail_open: bool = False
    ) -> None:
        """Call on_error hook on all middleware."""
        for middleware in self._middlewares:
            on_error = getattr(middleware, "on_error", None)
            if on_error is None:
                continue
            try:
                result = on_error(context, exc)
                if inspect.isawaitable(result):
                    raise RuntimeError("on_error hook is async; use async_run_on_error")
            except Exception:
                if not fail_open:
                    raise MiddlewareError(
                        f"Middleware {middleware.__class__.__name__} on_error failed"
                    ) from exc

    async def async_run_on_error(
        self, context: MiddlewareContext, exc: Exception, fail_open: bool = False
    ) -> None:
        """Call on_error hook on all middleware (async version)."""
        for middleware in self._middlewares:
            on_error = getattr(middleware, "on_error", None)
            if on_error is None:
                continue
            try:
                result = on_error(context, exc)
                if inspect.isawaitable(result):
                    await result  # type: ignore[misc]
            except Exception:
                if not fail_open:
                    raise MiddlewareError(
                        f"Middleware {middleware.__class__.__name__} on_error failed"
                    ) from exc


__all__ = ["MiddlewareChain"]
