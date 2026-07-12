---
color_scheme: dark
title: "Plugin Development"
parent: "Examples"
nav_order: 3
---

# Plugin Development

Complete guide to building, registering, and testing custom Whoosh-NG plugins.

## 1. Plugin Base Class

All plugins inherit from `whoosh.plugins.base.Plugin`:

```python
from whoosh.plugins.base import Plugin

class MyPlugin(Plugin):
    name = "my_plugin"
    version = "1.0.0"
    depends_on = []  # Other plugins this requires
    conflicts_with = []  # Plugins that conflict
    priority = 0  # Load order (higher = later)
    middleware = []  # List of middleware class names

    def register(self, manager):
        """Called when plugin is loaded. Register your handlers here."""
        manager.register("my_handler", MyHandler())

    def register_hooks(self):
        """Register hooks using hookimpl decorator."""
        from whoosh.hooks import hookimpl, register_hook

        @hookimpl
        def on_search(request, response):
            # Hook logic here
            pass

        register_hook("on_search", hookimpl(on_search))
```

## 2. Registering a Plugin

### Manual Registration

```python
from whoosh.plugins.manager import PluginManager

plugin = MyPlugin()
PluginManager.register(plugin)
```

### Auto-Discovery via Entry Points

In `pyproject.toml`:

```toml
[project]
name = "whoosh-ng-my-plugin"

[project.entry-points."whoosh_ng.plugins"]
my_plugin = "my_package.plugin:MyPlugin"
```

Auto-load all registered plugins:

```python
from whoosh.plugins.manager import PluginManager

PluginManager.load_plugins()  # Uses 'whoosh.plugins' group by default
```

## 3. Provider Plugin Example

A provider plugin registers a new implementation for a registry:

```python
from whoosh.plugins.base import Plugin
from whoosh.registry import VectorRegistry

class MyVectorProvider:
    def search(self, query_vector, k=10):
        # Your vector similarity logic
        return [{"doc_id": "1", "score": 0.95}]

class MyVectorPlugin(Plugin):
    name = "my_vector"
    version = "1.0.0"

    def register(self, manager):
        provider = MyVectorProvider()
        VectorRegistry.register("my_vector", provider, self.name)
```

## 4. Creating a Custom Field Type

```python
from whoosh.fields import FieldType, TEXT
from whoosh.formats import Postings

class TagField(FieldType):
    scorable = True
    stored = True
    indexed = True
    format = Postings()

    def __init__(self, stored=True, scorable=True):
        super().__init__(format=Postings(), analyzer=None,
                        scorable=scorable, stored=stored)
```

## 5. Testing Your Plugin

```python
import pytest
from whoosh.plugins.manager import PluginManager
from whoosh.registry.base import Registry

class TestMyPlugin:
    def test_register(self):
        plugin = MyPlugin()
        manager = PluginManager()
        plugin.register(manager)
        assert "my_handler" in manager._plugins

    def test_entry_point(self):
        """Test that entry point loading works."""
        manager = PluginManager()
        manager.register(MyPlugin())
        assert "my_plugin" in manager.list_enabled()

    def test_conflict_detection(self):
        plugin1 = MyPlugin()
        plugin2 = ConflictingPlugin()
        manager = PluginManager()
        manager.register(plugin1)
        assert manager.detect_conflicts("my_plugin", "conflicting_plugin")
```

## 6. Async Plugin Methods

Plugins support async methods:

```python
from whoosh.plugins.base import Plugin
from typing import Awaitable

class AsyncPlugin(Plugin):
    name = "async_plugin"
    version = "1.0.0"

    async def register(self, manager):
        # Async initialization
        await some_async_setup()

    def register_hooks(self):
        from whoosh.hooks import hookimpl

        @hookimpl
        async def on_search(request, response):
            # Async hook
            await log_search_async(request)
```

## 7. Plugin Manager API

```python
from whoosh.plugins.manager import PluginManager

manager = PluginManager()

# Register a plugin instance
manager.register(MyPlugin())

# Enable/disable
manager.enable("my_plugin")
manager.disable("my_plugin")

# Check status
manager.list_plugins()   # All registered
manager.list_enabled()   # Enabled plugins

# Get plugin
plugin = manager.get("my_plugin")

# Version checking
manager.validate_version("my_plugin", "1.0.0")
```

## 8. Built-in Plugins

Whoosh-NG includes several built-in plugins:

- `whoosh_modern.vector` - Vector similarity search (NumPy provider)
- `whoosh_modern.autocomplete` - Inverted index autocomplete
- `whoosh_fastapi` - FastAPI REST endpoints

Load them:

```python
from whoosh.plugins.manager import PluginManager
from whoosh_modern.vector.plugin import VectorPlugin
from whoosh_modern.autocomplete.plugin import AutocompletePlugin

PluginManager.load_plugins()  # Auto-loads entry points
# Or manually:
manager = PluginManager()
manager.register(VectorPlugin())
manager.register(AutocompletePlugin())
```
