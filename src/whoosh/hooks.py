from __future__ import annotations

from typing import Any, Callable, Coroutine

from whoosh.event_bus import event_bus


_hooks: dict[str, list[Callable[..., Any]]] = {}


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
        except Exception:
            pass
    return results
