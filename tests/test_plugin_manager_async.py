from __future__ import annotations

from whoosh.plugins.manager import Plugin, PluginManager


class SyncProbePlugin(Plugin):
    name = "sync_probe"
    version = "1.0.0"
    registered: bool = False

    def register(self, manager: PluginManager) -> None:
        SyncProbePlugin.registered = True


class AsyncProbePlugin(Plugin):
    name = "async_probe"
    version = "1.0.0"
    registered: bool = False

    async def register(self, manager: PluginManager) -> None:
        AsyncProbePlugin.registered = True


def test_sync_plugin_register() -> None:
    SyncProbePlugin.registered = False
    manager = PluginManager()
    manager.register(SyncProbePlugin())
    assert SyncProbePlugin.registered is True
    assert "sync_probe" in manager.list_plugins()


def test_async_plugin_register_bridge() -> None:
    AsyncProbePlugin.registered = False
    manager = PluginManager()
    manager.register(AsyncProbePlugin())
    assert AsyncProbePlugin.registered is True
    assert "async_probe" in manager.list_plugins()


def test_duplicate_plugin_raises() -> None:
    manager = PluginManager()
    manager.register(SyncProbePlugin())
    import pytest

    with pytest.raises(ValueError):
        manager.register(SyncProbePlugin())
