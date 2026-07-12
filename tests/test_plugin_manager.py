from __future__ import annotations

import pytest

from whoosh.plugins.manager import Plugin, PluginManager


class SamplePlugin(Plugin):
    name = "sample"
    version = "1.2.0"

    def register(self, manager: PluginManager) -> None:
        pass


class BadPlugin(Plugin):
    name = "bad"
    version = "0.1.0"
    conflicts_with = ["other"]


class OtherPlugin(Plugin):
    name = "other"
    version = "2.0.0"


@pytest.fixture
def manager() -> PluginManager:
    return PluginManager()


def test_register_and_get(manager: PluginManager) -> None:
    manager.register(SamplePlugin())
    assert manager.get("sample").name == "sample"


def test_duplicate_registration(manager: PluginManager) -> None:
    manager.register(SamplePlugin())
    with pytest.raises(ValueError):
        manager.register(SamplePlugin())


def test_list_plugins(manager: PluginManager) -> None:
    manager.register(SamplePlugin())
    manager.register(OtherPlugin())
    assert manager.list_plugins() == ["sample", "other"]


def test_enable_disable(manager: PluginManager) -> None:
    manager.register(SamplePlugin())
    manager.disable("sample")
    assert manager.list_enabled() == []
    manager.enable("sample")
    assert manager.list_enabled() == ["sample"]


def test_validate_version(manager: PluginManager) -> None:
    manager.register(SamplePlugin())
    assert manager.validate_version("sample", "1.0.0") is True
    assert manager.validate_version("sample", "2.0.0") is False


def test_detect_conflicts(manager: PluginManager) -> None:
    manager.register(BadPlugin())
    manager.register(OtherPlugin())
    assert manager.detect_conflicts("bad", "other") is True
    assert manager.detect_conflicts("other", "bad") is False


def test_load_plugins_failure_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeEP:
        name = "broken"

        def load(self):
            raise RuntimeError("boom")

    class FakeEPs:
        def select(self, group: str = "", name: str = ""):
            return [FakeEP()]

    monkeypatch.setattr(
        "importlib.metadata.entry_points",
        lambda: FakeEPs(),
    )
    with pytest.raises(RuntimeError, match="Failed to load plugin"):
        PluginManager.load_plugins()
