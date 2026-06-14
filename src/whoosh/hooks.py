from __future__ import annotations

import logging
from typing import Any, Callable

from whoosh.event_bus import event_bus, Event

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
