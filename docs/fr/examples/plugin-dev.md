---
color_scheme: dark
title: "Développement de Plugins"
parent: "Exemples"
nav_order: 3
lang: fr
---

# Développement de Plugins

Guide complet pour créer, enregistrer et tester vos propres plugins Whoosh-NG.

## 1. Classe de base des Plugins

Tous les plugins héritent de `whoosh.plugins.base.Plugin` :

```python
from whoosh.plugins.base import Plugin

class MyPlugin(Plugin):
    name = "my_plugin"
    version = "1.0.0"
    depends_on = []
    conflicts_with = []
    priority = 0
    middleware = []

    def register(self, manager):
        """Appelé quand le plugin est chargé."""
        manager.register("my_handler", MyHandler())

    def register_hooks(self):
        """Enregistrer les hooks avec le décorateur hookimpl."""
        from whoosh.hooks import hookimpl, register_hook

        @hookimpl
        def on_search(request, response):
            pass

        register_hook("on_search", hookimpl(on_search))
```

## 2. Enregistrement d’un Plugin

### Enregistrement manuel

```python
from whoosh.plugins.manager import PluginManager

plugin = MyPlugin()
PluginManager.register(plugin)
```

### Auto-découverte via Entry Points

Dans `pyproject.toml` :

```toml
[project]
name = "whoosh-ng-my-plugin"

[project.entry-points."whoosh_ng.plugins"]
my_plugin = "my_package.plugin:MyPlugin"
```

Auto-chargement :

```python
from whoosh.plugins.manager import PluginManager

PluginManager.load_plugins()
```

## 3. Exemple de Plugin Provider

```python
from whoosh.plugins.base import Plugin
from whoosh.registry import VectorRegistry

class MyVectorProvider:
    def search(self, query_vector, k=10):
        return [{"doc_id": "1", "score": 0.95}]

class MyVectorPlugin(Plugin):
    name = "my_vector"
    version = "1.0.0"

    def register(self, manager):
        provider = MyVectorProvider()
        VectorRegistry.register("my_vector", provider, self.name)
```

## 4. Tester son Plugin

```python
import pytest
from whoosh.plugins.manager import PluginManager

class TestMyPlugin:
    def test_register(self):
        plugin = MyPlugin()
        manager = PluginManager()
        plugin.register(manager)
        assert "my_handler" in manager._plugins

    def test_entry_point(self):
        manager = PluginManager()
        manager.register(MyPlugin())
        assert "my_plugin" in manager.list_enabled()
```

## 5. API du PluginManager

```python
from whoosh.plugins.manager import PluginManager

manager = PluginManager()
manager.register(MyPlugin())
manager.enable("my_plugin")
manager.disable("my_plugin")
manager.list_plugins()
manager.list_enabled()
plugin = manager.get("my_plugin")
```

## 6. Plugins Intégrés

- `whoosh_modern.vector` - Recherche vectorielle (NumPy)
- `whoosh_modern.autocomplete` - Autocomplétion par index inversé
- `whoosh_fastapi` - Endpoints REST FastAPI

```python
from whoosh.plugins.manager import PluginManager
from whoosh_modern.vector.plugin import VectorPlugin
from whoosh_modern.autocomplete.plugin import AutocompletePlugin

PluginManager.load_plugins()
```