---
title: "Plugin Development"
parent: "Exemples"
nav_order: 3
---

# Plugin Development

How to build and register a custom Whoosh-NG plugin.

## Minimal Plugin

```python
from whoosh.plugins.base import BasePlugin

class MyPlugin(BasePlugin):
    name = "my_plugin"
    version = "1.0.0"
    dependencies = []

    def setup(self, registry):
        registry.register("my_handler", MyHandler())

    def teardown(self, registry):
        registry.unregister("my_handler")
```

## Registration

```python
from whoosh.plugins.manager import PluginManager

PluginManager.register("my_plugin", MyPlugin())
PluginManager.enable("my_plugin")
```

## Entry Points

```toml
# pyproject.toml
[project.entry-points."whoosh_ng.plugins"]
my_plugin = "my_package.plugin:MyPlugin"
```

```python
# Auto-discovery
from whoosh.plugins.manager import PluginManager
PluginManager.load_plugins()
```

## Standalone Provider Plugin

```python
class MyProviderPlugin(BasePlugin):
    name = "my_provider"

    def setup(self, registry):
        registry.register("generator", MyGenerator(), "autocomplete")
```

## Testable Plugin

```python
import pytest
from whoosh.plugins.base import BasePlugin

class TestMyPlugin:
    def test_setup_registers(self):
        plugin = MyPlugin()
        registry = InMemoryRegistry()
        plugin.setup(registry)
        assert registry.get("my_handler") is not None

    def test_teardown_unregisters(self):
        plugin = MyPlugin()
        registry = InMemoryRegistry()
        plugin.setup(registry)
        plugin.teardown(registry)
        assert registry.get("my_handler") is None
```
