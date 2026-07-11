---
title: "Plugins"
nav_order: 26
parent: "Guides"
---

# Plugins

Whoosh-NG uses a plugin architecture to keep the core lightweight while enabling advanced features. Plugins are loaded via entry points and managed by the `PluginManager`.

## Plugin Architecture

```text
PluginManager
    ├── load_plugins()     # Auto-discover from entry points
    ├── register(name, plugin)  # Manual registration
    ├── enable(name)       # Enable a plugin
    ├── disable(name)      # Disable a plugin
    ├── get(name)          # Retrieve a plugin
    └── list_plugins()     # List all plugins
```

## Built-in Plugins

| Plugin | Package | Description |
|--------|---------|-------------|
| whoosh-ng-vector | `whoosh_modern.vector` | Vector search providers (NumPy, HNSW, Faiss) |
| whoosh-ng-autocomplete | `whoosh_modern.autocomplete` | Edge ngram autocomplete |
| whoosh-ng-fastapi | `whoosh_fastapi` | FastAPI app factory |
| whoosh-ng-observability | `whoosh_observability` | Prometheus metrics |
| whoosh-ng-admin | `whoosh_admin` | Admin UI |

## Creating a Plugin

Every plugin is a subclass of `BasePlugin`:

```python
from whoosh.plugins.base import BasePlugin

class MyPlugin(BasePlugin):
    name = "my_plugin"
    version = "1.0.0"
    dependencies = []

    def setup(self, registry):
        """Called when the plugin is enabled."""
        registry.register("my_provider", MyProvider())

    def teardown(self, registry):
        """Called when the plugin is disabled."""
        registry.unregister("my_provider")

    def middleware(self):
        """Return middleware to inject into the pipeline."""
        return [MyMiddleware()]

    def on_startup(self):
        """Called once at application startup."""
        pass

    def on_shutdown(self):
        """Called once at application shutdown."""
        pass
```

## Plugin Registration

### Via entry_points (pyproject.toml)

```toml
[project.entry-points."whoosh_ng.plugins"]
my_plugin = "my_package.plugin:MyPlugin"
```

### Programmatic

```python
from whoosh.plugins.manager import PluginManager

plugin = MyPlugin()
PluginManager.register("my_plugin", plugin)
PluginManager.enable("my_plugin")
```

## Plugin Lifecycle

```
register() -> setup() -> enable() -> middleware hooks -> teardown() -> disable()
```

## Plugin Dependencies

Plugins can declare dependencies on other plugins:

```python
class VectorPlugin(BasePlugin):
    name = "vector"
    version = "1.0.0"
    dependencies = ["metrics"]  # Requires metrics plugin
```

The `PluginManager` resolves dependency order and detects conflicts.

## Example: Vector Plugin

```python
from whoosh.plugins.base import BasePlugin
from whoosh.vector.base import VectorProvider, VectorField
from whoosh.vector.numpy_provider import NumpyProvider

class VectorPlugin(BasePlugin):
    name = "vector"
    version = "1.0.0"
    dependencies = []

    def setup(self, registry):
        provider = NumpyProvider()
        registry.register("numpy", provider, owner="vector")

    def middleware(self):
        from whoosh.middleware import MetricsMiddleware
        return [MetricsMiddleware()]

    def on_startup(self):
        print("Vector plugin loaded")
```

## Example: FastAPI Plugin

```python
from whoosh.plugins.base import BasePlugin

class FastAPIPlugin(BasePlugin):
    name = "fastapi"
    version = "1.0.0"

    def setup(self, registry):
        self.app = None

    def create_app(self, index, **kwargs):
        from whoosh_fastapi import create_app
        self.app = create_app(index=index, **kwargs)
        return self.app

    def middleware(self):
        from whoosh.middleware import CacheMiddleware
        return [CacheMiddleware()]
```

## Best Practices

1. **Keep plugins small**: One plugin, one responsibility
2. **Declare dependencies**: Help PluginManager resolve load order
3. **Handle conflicts**: Check for existing registrations before adding
4. **Clean up**: Implement `teardown()` to remove registries and middleware
5. **Version your plugin**: Semver for compatibility checking
