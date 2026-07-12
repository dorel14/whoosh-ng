from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar("T")


class Registry(Generic[T]):
    def __init__(self, name: str = "") -> None:
        self._name = name
        self._items: dict[str, T] = {}
        self._owners: dict[str, str] = {}

    def register(self, key: str, item: T, owner: str = "") -> None:
        if key in self._items:
            raise KeyError(f"Registry '{self._name}' already contains '{key}'")
        self._items[key] = item
        self._owners[key] = owner or type(item).__name__

    def get(self, key: str) -> T:
        try:
            return self._items[key]
        except KeyError:
            raise KeyError(f"Registry '{self._name}' has no entry '{key}'")

    def unregister(self, key: str) -> None:
        self._items.pop(key, None)
        self._owners.pop(key, None)

    def list_keys(self) -> list[str]:
        return list(self._items.keys())

    def owner(self, key: str) -> str:
        return self._owners.get(key, "")
