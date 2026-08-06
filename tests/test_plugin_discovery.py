"""Tests for PluginManager registries and multi-group entry-point discovery."""

from __future__ import annotations

import pytest

from whoosh.plugins.manager import STANDARD_GROUPS, Plugin, PluginManager


class _FakeEP:
    def __init__(self, name: str, plugin_cls: type[Plugin]) -> None:
        self.name = name
        self._plugin_cls = plugin_cls

    def load(self) -> type[Plugin]:
        return self._plugin_cls


def _make_eps(plugins_by_group: dict[str, list[type[Plugin]]]) -> object:
    class FakeEPs:
        def select(self, group: str = "") -> list[_FakeEP]:
            return [_FakeEP(p.name, p) for p in plugins_by_group.get(group, [])]

    return FakeEPs()


class DatasourcePlugin(Plugin):
    name = "ds-plugin"
    version = "1.0.0"

    def register(self, manager: PluginManager) -> None:
        manager.register_datasource("sql", object())


class VectorPlugin(Plugin):
    name = "vp-plugin"
    version = "1.0.0"

    def register(self, manager: PluginManager) -> None:
        manager.register_vector_provider("numpy", object())


class MiddlewarePlugin(Plugin):
    name = "mw-plugin"
    version = "1.0.0"

    def register(self, manager: PluginManager) -> None:
        manager.register_middleware("retry", object())


class EmbeddingPlugin(Plugin):
    name = "emb-plugin"
    version = "1.0.0"

    def register(self, manager: PluginManager) -> None:
        manager.register_embedding("minilm", object())


@pytest.fixture
def discovered_manager(monkeypatch: pytest.MonkeyPatch) -> PluginManager:
    plugins = {
        "whoosh.plugins": [],
        "whoosh.datasources": [DatasourcePlugin],
        "whoosh.vector.providers": [VectorPlugin],
        "whoosh.middlewares": [MiddlewarePlugin],
        "whoosh.embeddings": [EmbeddingPlugin],
        "whoosh.language": [],
        "whoosh.apps": [],
    }
    monkeypatch.setattr(
        "importlib.metadata.entry_points", lambda: _make_eps(plugins)
    )
    manager = PluginManager()
    for group in STANDARD_GROUPS:
        manager._load(group)
    yield manager
    PluginManager._default = None


class TestRegistryCRUD:
    def test_datasource_registry(self) -> None:
        m = PluginManager()
        m.register_datasource("sql", "provider")
        assert m.get_datasource("sql") == "provider"
        assert m.list_datasources() == ["sql"]
        with pytest.raises(KeyError):
            m.get_datasource("missing")

    def test_vector_provider_registry(self) -> None:
        m = PluginManager()
        m.register_vector_provider("numpy", "vec")
        assert m.get_vector_provider("numpy") == "vec"
        assert m.list_vector_providers() == ["numpy"]

    def test_middleware_registry(self) -> None:
        m = PluginManager()
        m.register_middleware("retry", "mw")
        assert m.get_middleware("retry") == "mw"
        assert m.list_middlewares() == ["retry"]

    def test_embedding_registry(self) -> None:
        m = PluginManager()
        m.register_embedding("minilm", "emb")
        assert m.get_embedding("minilm") == "emb"
        assert m.list_embeddings() == ["minilm"]


class TestMultiGroupDiscovery:
    def test_discovers_all_registries(self, discovered_manager: PluginManager) -> None:
        assert "sql" in discovered_manager.list_datasources()
        assert "numpy" in discovered_manager.list_vector_providers()
        assert "retry" in discovered_manager.list_middlewares()
        assert "minilm" in discovered_manager.list_embeddings()

    def test_discovered_plugins_registered(self, discovered_manager: PluginManager) -> None:
        names = discovered_manager.list_plugins()
        assert {"ds-plugin", "vp-plugin", "mw-plugin", "emb-plugin"} <= set(names)
