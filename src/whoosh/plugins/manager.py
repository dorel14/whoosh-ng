from __future__ import annotations

import logging
from abc import ABC
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Awaitable, ClassVar, cast

if TYPE_CHECKING:
    from whoosh.middleware.chain import MiddlewareChain  # type: ignore[import]
    from whoosh.query import Query  # type: ignore[import]

from whoosh.hooks import register_hook, HookImpl  # type: ignore[import]
from whoosh.utils.async_utils import is_async_callable, run_async_from_sync  # type: ignore[import]


logger = logging.getLogger(__name__)


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""

    name: str
    version: str
    depends_on: list[str] = field(default_factory=list)
    priority: int = 0
    middleware: list[str] = field(default_factory=list)


class Plugin(ABC):
    name: str
    version: str
    conflicts_with: list[str] = []
    owner: str = ""
    depends_on: list[str] = []
    priority: int = 0
    middleware: list[str] = []

    def register(self, manager: "PluginManager") -> None:
        pass

    def register_hooks(self) -> None:
        pass


class AnalyzerPlugin(Plugin):
    """Base class for plugins that provide custom analyzers.

    Subclasses should set the ``name`` attribute and implement
    ``register()`` to register one or more analyzers with the manager.
    """

    def register(self, manager: "PluginManager") -> None:
        raise NotImplementedError


class QueryRewritePlugin(Plugin):
    """Base class for plugins that rewrite queries before execution.

    Subclasses should implement ``rewrite(query, searcher)`` to return a
    modified or replacement query.
    """

    def rewrite(self, query: "Query", searcher: Any) -> "Query":
        return query


class PluginManager:
    _default: ClassVar[PluginManager | None] = None

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}
        self._order: list[str] = []
        self._enabled: set[str] = set()
        self._analyzers: dict[str, Any] = {}
        self._query_rewriters: dict[str, QueryRewritePlugin] = {}

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
        if is_async_callable(plugin.register):
            coro = plugin.register(self)  # type: ignore[func-returns-value]
            run_async_from_sync(cast("Awaitable[None]", coro))
        else:
            plugin.register(self)
        plugin.register_hooks()

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

    def get_middleware_chain(self) -> "MiddlewareChain":
        """Return a MiddlewareChain containing all plugin middleware, sorted by priority."""
        from whoosh.middleware.chain import MiddlewareChain

        middlewares = []
        for name in self._order:
            plugin = self._plugins.get(name)
            if plugin and hasattr(plugin, "middleware"):
                for mw_name in plugin.middleware:
                    if mw_name:
                        middlewares.append(self._get_middleware(mw_name))
        return MiddlewareChain(middlewares)

    def _get_middleware(self, name: str) -> Any:
        """Import and instantiate a middleware by string name."""
        from importlib import import_module

        parts = name.rsplit(".", 1)
        module_path = parts[0]
        class_name = parts[1] if len(parts) > 1 else parts[0]
        module = import_module(module_path)
        return getattr(module, class_name)()

    def register_analyzer(self, name: str, analyzer: Any) -> None:
        """Register a named analyzer provided by an analyzer plugin."""
        self._analyzers[name] = analyzer

    def get_analyzer(self, name: str) -> Any:
        """Return a registered analyzer by name."""
        if name not in self._analyzers:
            raise KeyError(f"Analyzer '{name}' is not registered")
        return self._analyzers[name]

    def list_analyzers(self) -> list[str]:
        """Return the names of all registered analyzers."""
        return list(self._analyzers.keys())

    def register_query_rewriter(self, plugin: QueryRewritePlugin) -> None:
        """Register a query rewriter plugin."""
        self._query_rewriters[plugin.name] = plugin

    def get_query_rewriter(self, name: str) -> QueryRewritePlugin:
        """Return a registered query rewriter plugin by name."""
        if name not in self._query_rewriters:
            raise KeyError(f"Query rewriter '{name}' is not registered")
        return self._query_rewriters[name]

    def list_query_rewriters(self) -> list[str]:
        """Return the names of all registered query rewriters."""
        return list(self._query_rewriters.keys())
