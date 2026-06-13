from __future__ import annotations

import asyncio
from typing import Any, Callable, Coroutine, Type


class Event:
    pass


class EventBus:
    def __init__(self) -> None:
        self._listeners: dict[Type[Event], list[Callable[[Event], Coroutine[Any, Any, None]]]] = {}

    def subscribe(
        self, event_type: Type[Event]
    ) -> Callable[
        [Callable[[Event], Coroutine[Any, Any, None]]], Callable[[Event], Coroutine[Any, Any, None]]
    ]:
        def decorator(
            func: Callable[[Event], Coroutine[Any, Any, None]],
        ) -> Callable[[Event], Coroutine[Any, Any, None]]:
            self._listeners.setdefault(event_type, []).append(func)
            return func

        return decorator

    def publish(self, event: Event) -> None:
        listeners = self._listeners.get(type(event), [])
        for listener in listeners:
            try:
                coro = listener(event)
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(coro)
                except RuntimeError:
                    asyncio.run(coro)
            except Exception:
                pass

    def clear(self) -> None:
        self._listeners.clear()


event_bus = EventBus()
