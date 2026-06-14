from __future__ import annotations

import logging
from typing import Any, Callable

_hooks: dict[str, list[Callable[..., Any]]] = {}

logger = logging.getLogger(__name__)


class HookImpl:
    def __init__(self, func: Callable[..., Any]) -> None:
        self.func = func


def hookimpl(func: Callable[..., Any]) -> HookImpl:
    return HookImpl(func)


def register_hook(name: str, impl: HookImpl) -> None:
    _hooks.setdefault(name, []).append(impl.func)


async def call_hook(name: str, *args: Any, **kwargs: Any) -> list[Any]:
    """Call all hooks registered for a name (async version for compatibility)."""
    results: list[Any] = []
    for hook in _hooks.get(name, []):
        try:
            res = hook(*args, **kwargs)
            if hasattr(res, "__await__"):
                results.append(await res)
            else:
                results.append(res)
        except Exception as exc:
            logger.exception("Error executing hook '%s'", name, exc_info=exc)
    return results


def get_hooks(name: str) -> list[Callable[..., Any]]:
    """Return all hooks registered for a name."""
    return _hooks.get(name, [])


def clear_hooks(name: str | None = None) -> None:
    """Clear hooks. If name is None, clear all hooks."""
    if name is None:
        _hooks.clear()
    else:
        _hooks.pop(name, None)