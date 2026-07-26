---
color_scheme: dark
title: "Plugins & Registry"
nav_order: 6
parent: "API Reference"
---

# Plugins & Registry

Extend Whoosh-NG through the plugin system and registries.

## Plugin System

### BasePlugin

```python
class whoosh.plugins.base.BasePlugin
```

All plugins inherit from this class.

#### Attributes

- `name (str)`: Plugin name.
- `version (str)`: Plugin version.
- `dependencies (list[str])`: Required plugins.

#### Methods

##### `setup()`

```python
def setup(self, registry) -> None:
    """Called when the plugin is enabled."""
```

##### `teardown()`

```python
def teardown(self, registry) -> None:
    """Called when the plugin is disabled."""
```

##### `middleware()`

```python
def middleware(self) -> list[Middleware]:
    """Return middleware instances."""
```

---

### PluginManager

```python
class whoosh.plugins.manager.PluginManager
```

Manages plugin lifecycle.

#### Methods

##### `load_plugins()`

```python
PluginManager.load_plugins()
```

Auto-discover plugins from entry points.

---

##### `register()`

```python
PluginManager.register(name: str, plugin: BasePlugin)
```

Register a plugin manually.

---

##### `enable()`

```python
PluginManager.enable(name: str)
```

Enable a registered plugin.

---

##### `disable()`

```python
PluginManager.disable(name: str)
```

Disable a plugin.

---

##### `get()`

```python
plugin = PluginManager.get(name: str)
```

Get a plugin instance.

---

##### `list_plugins()`

```python
plugins = PluginManager.list_plugins()
```

List all registered plugins.

---

##### `get_middleware_chain()`

```python
chain = PluginManager.get_middleware_chain()
```

Get the combined middleware chain from all plugins.

---

## Registry System

Registries provide centralized object management.

### Registry Base

```python
class whoosh.registry.base.Registry
```

Generic registry.

#### Methods

##### `register()`

```python
Registry.register(
    key: str,
    value: Any,
    owner: str = None
)
```

Register a value.

---

##### `un
