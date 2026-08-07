---
title: "Plugin System"
nav_order: 51
permalink: /en/guides/plugins-sprint-c/
lang: en
---

# Plugin System

Module: `whoosh.plugins.manager`
Version: 2.0.0

Whoosh-NG's plugin architecture enables external packages to extend the core indexing, search, and analysis pipeline. Plugins are discovered via Python [entry points](https://docs.python.org/3/library/importlib.metadata.html#entry-points) declared in `pyproject.toml` and managed by the `PluginManager`.

## Architecture Overview

```text
PluginManager (singleton)
    ├── load_plugins(group)          # Auto-discover from entry points
    ├── register(plugin)             # Manual registration
    ├── enable(name) / disable(name) # Toggle lifecycle
    ├── get(name) / list_plugins()   # Inspection
    ├── get_middleware_chain()       # Build MiddlewareChain from plugin middleware
    ├── register_datasource()        # Register a datasource provider
    ├── register_vector_provider()   # Register a vector provider
    ├── register_middleware()        # Register a middleware instance
    ├── register_embedding()         # Register an embedding provider
    ├── register_analyzer()          # Register a named analyzer
    └── register_query_rewriter()    # Register a query rewriter
```

## Plugin Base Classes

### Plugin (ABC)

The root plugin class. Subclasses set class-level attributes and implement `register()`.

```python
from whoosh.plugins.manager import Plugin, PluginMetadata

class MyPlugin(Plugin):
    name = "my_plugin"
    version = "1.0.0"

    def register(self, manager: PluginManager) -> None:
        """Called when the plugin is loaded; register providers here."""
        manager.register_middleware("my_module.MyMiddleware", MyMiddleware())

    def register_hooks(self) -> None:
        """Register event hooks (optional)."""
        from whoosh.hooks import hookimpl, register_hook

        @hookimpl
        def on_search(request, response):
            pass
        register_hook("on_search", hookimpl(on_search))
```

### AnalyzerPlugin

For plugins that provide custom tokenizers/analyzers:

```python
from whoosh.plugins.manager import AnalyzerPlugin

class MyAnalyzerPlugin(AnalyzerPlugin):
    name = "my_analyzer"

    def register(self, manager):
        manager.register_analyzer("my_analyzer", MyTokenizer())
```

### QueryRewritePlugin

For plugins that transform queries before execution:

```python
from whoosh.plugins.manager import QueryRewritePlugin

class SynonymRewriterPlugin(QueryRewritePlugin):
    name = "synonym_rewriter"

    def rewrite(self, query, searcher):
        # Return modified query
        return query
```

## PluginMetadata

A dataclass describing plugin metadata:

| Field         | Type              | Description                            |
|---------------|-------------------|----------------------------------------|
| `name`        | `str`             | Unique plugin name                     |
| `version`     | `str`             | SemVer version string                  |
| `depends_on`  | `list[str]`       | Names of required plugins              |
| `priority`    | `int`             | Load ordering priority (higher = later)|
| `middleware`  | `list[str]`       | Dotted paths to middleware classes     |

## Entry Point Groups

The `PluginManager` discovers plugins from these standard entry-point groups:

| Group                | Purpose                              |
|----------------------|--------------------------------------|
| `whoosh.plugins`     | General plugins                      |
| `whoosh.datasources` | Data source providers                |
| `whoosh.vector.providers` | Vector similarity providers     |
| `whoosh.middlewares` | Middleware classes                    |
| `whoosh.embeddings`  | Embedding model providers            |
| `whoosh.language`    | Language-specific analyzers          |
| `whoosh.apps`        | App factories (FastAPI, admin, etc.) |

## Creating and Deploying a Plugin

### Step 1: Define the Plugin Class

```python
# my_plugin/plugin.py
from whoosh.plugins.manager import Plugin
from whoosh.registry import VectorRegistry

class MyVectorPlugin(Plugin):
    name = "my_vector"
    version = "1.0.0"
    depends_on = []
    conflicts_with = []
    priority = 0
    middleware = []

    def register(self, manager):
        """Register a vector provider with the VectorRegistry."""
        provider = MyCustomVectorProvider()
        VectorRegistry.register("my_vector", provider, owner=self.name)

    def register_hooks(self):
        """Register optional hooks (e.g., on_search, on_index)."""
        pass
```

### Step 2: Declare the Entry Point

In your `pyproject.toml`:

```toml
[project]
name = "whoosh-ng-my-vector"
version = "1.0.0"
dependencies = ["whoosh-ng>=2.0"]

[project.entry-points."whoosh_ng.plugins"]
my_vector = "my_plugin.plugin:MyVectorPlugin"
```

### Step 3: Install and Verify

```bash
pip install -e .
```

```python
# Verify the plugin is registered
from whoosh.plugins.manager import PluginManager

PluginManager.load_plugins()  # Auto-discovers all entry points

manager = PluginManager._default
print(manager.list_plugins())
# ['whoosh_autocomplete', 'whoosh_vector', ..., 'my_vector']

# Check the registry
from whoosh.registry import VectorRegistry
print(VectorRegistry.list_keys())
# ['my_vector', 'numpy']
```

## Manual Registration (No Entry Point)

For testing or programmatic use:

```python
from whoosh.plugins.manager import PluginManager

manager = PluginManager()
manager.register(MyVectorPlugin())
manager.enable("my_vector")
```

## Plugin Lifecycle

```
1. Entry point discovered  ───►  2. register() called  ───►  3. register_hooks()
   │                               │                            │
   └── load_plugins(group)          └── register provider/     └── register_hook()
                                      middleware/analyzer
```

### Enabling / Disabling

```python
from whoosh.plugins.manager import PluginManager

manager = PluginManager._default

manager.enable("my_vector")    # Activate a plugin
manager.disable("my_vector")   # Deactivate a plugin
print(manager.list_enabled())  # Only enabled plugins
```

### Version Validation

```python
# Check if a plugin meets a minimum version
ok = manager.validate_version("my_vector", "1.0.0")
print(ok)  # True if plugin version >= 1.0.0
```

### Conflict Detection

```python
# Check if two plugins conflict
if manager.detect_conflicts("plugin_a", "plugin_b"):
    print("These plugins cannot be loaded together")
```

## Plugin Manager API Reference

### `PluginManager.load_plugins(group=None)`

Load all plugins from entry-point groups. If `group` is `None`, loads from all standard groups (`STANDARD_GROUPS`).

### `PluginManager.register(plugin)`

Register a plugin instance. Calls `plugin.register(self)` and `plugin.register_hooks()`. Supports async `register()` via `asyncio`.

### `PluginManager.get_middleware_chain()`

Builds and returns a `MiddlewareChain` from all plugins that declare `middleware` entries. Middleware classes are imported and instantiated by dotted path.

### Registry Registration Methods

| Method                       | Description                          |
|------------------------------|--------------------------------------|
| `register_analyzer(name, analyzer)` | Register a named analyzer   |
| `register_datasource(name, datasource)` | Register a datasource  |
| `register_vector_provider(name, provider)` | Register a vector provider |
| `register_middleware(name, middleware)` | Register a middleware instance |
| `register_embedding(name, embedding)` | Register an embedding provider |
| `register_query_rewriter(plugin)` | Register a query rewriter plugin |

### Lookup Methods

| Method                       | Returns                          |
|------------------------------|----------------------------------|
| `get(name)`                  | `Plugin` instance                |
| `list_plugins()`             | All registered plugin names      |
| `list_enabled()`             | Enabled plugin names             |
| `get_analyzer(name)`         | Analyzer callable                |
| `list_analyzers()`           | Registered analyzer names        |
| `list_datasources()`         | Registered datasource names      |
| `list_vector_providers()`    | Registered vector provider names |
| `list_middlewares()`         | Registered middleware names      |
| `list_embeddings()`          | Registered embedding names       |
| `list_query_rewriters()`     | Registered query rewriter names  |

## Built-in Plugins

| Plugin            | Module                  | Entry-point Group       |
|-------------------|-------------------------|-------------------------|
| `whoosh_autocomplete` | `whoosh_modern.autocomplete.plugin` | `whoosh.plugins` |
| `whoosh_vector`   | `whoosh_modern.vector.plugin`      | `whoosh.plugins` |
| `whoosh_fastapi`  | `whoosh_fastapi`                  | `whoosh.apps` |
| `whoosh_observability` | `whoosh.middleware.metrics`  | `whoosh.middlewares` |
| `whoosh_admin`    | `whoosh_admin`                   | `whoosh.apps` |

## Best Practices

1. **Single responsibility**: One plugin, one feature
2. **Declare dependencies**: Use `depends_on` for required plugins
3. **Semantic versioning**: Increment version for API changes
4. **Graceful degradation**: Check for optional dependencies in `register()`
5. **Avoid side effects in `__init__`**: All setup in `register()`
6. **Clean up**: If applicable, provide teardown logic

## See Also

- [Middleware Guide](middleware-sprint-c.md) — Pipeline hooks and custom middleware
- [Plugin Development Example](../examples/plugin-dev.md) — Step-by-step plugin tutorial
- [API: Plugins](../api/plugins.md) — Full API reference
