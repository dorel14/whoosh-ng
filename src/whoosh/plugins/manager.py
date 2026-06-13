from __future__ import annotations

from abc import ABC
from typing import ClassVar


class Plugin(ABC):
    name: str
    version: str
    conflicts_with: list[str] = []

    def register(self, registry) -> None:
        pass


class PluginManager:
    _default: ClassVar[PluginManager | None] = None

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}
        self._order: list[str] = []
        self._enabled: set[str] = set()

    @classmethod
    def load_plugins(cls, group: str = "whoosh.plugins") -> None:
        if cls._default is None:
            cls._default = cls()
        cls._default._load(group)

    def _load(self, group: str) -> None:
        from importlib.metadata import entry_points

        eps = entry_points()
        if hasattr(eps, "select"):
            group_eps = eps.select(group=group)
        elif hasattr(eps, "get"):
            group_eps = eps.get(group, [])
        else:
            group_eps = [ep for ep in eps if getattr(ep, "group", None) == group]
        for ep in group_eps:
            try:
                plugin_cls = ep.load()
            except Exception as exc:
                raise RuntimeError(f"Failed to load plugin '{ep.name}': {exc}") from exc
            self.register(plugin_cls())

    def register(self, plugin: Plugin) -> None:
        if plugin.name in self._plugins:
            raise ValueError(f"Plugin '{plugin.name}' is already registered")
        self._plugins[plugin.name] = plugin
        self._order.append(plugin.name)
        self._enabled.add(plugin.name)

    def get(self, name: str) -> Plugin:
        try:
            return self._plugins[name]
        except KeyError:
            raise KeyError(f"Plugin '{name}' is not registered")

    def list_plugins(self) -> list[str]:
        return list(self._order)

    def enable(self, name: str) -> None:
        self._enabled.add(name)

    def disable(self, name: str) -> None:
        self._enabled.discard(name)

    def list_enabled(self) -> list[str]:
        return list(self._enabled)

    @staticmethod
    def _parse_version(version: str) -> tuple[int, ...]:
        return tuple(int(part) for part in version.split(".") if part.isdigit())

    def validate_version(self, name: str, required: str) -> bool:
        plugin = self.get(name)
        return self._parse_version(plugin.version) >= self._parse_version(required)

    def detect_conflicts(self, name1: str, name2: str) -> bool:
        plugin = self._plugins.get(name1)
        if plugin is None:
            return False
        return name2 in getattr(plugin, "conflicts_with", [])
