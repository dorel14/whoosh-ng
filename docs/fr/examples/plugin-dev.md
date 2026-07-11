---
title: "Développement de plugin"
parent: "Exemples"
lang: fr
nav_order: 3
---

# Développement de plugin

Créer un plugin personnalisé avec point d'entrée, setup/teardown, et test unitaire.

```python
from whoosh.plugins.base import BasePlugin

class MonPlugin(BasePlugin):
    name = "mon_plugin"
    version = "1.0.0"
    dependencies = []

    def setup(self, registry):
        registry.register("generator", MonGenerator(), "autocomplete")

    def teardown(self, registry):
        registry.unregister("generator", "autocomplete")
```

## Enregistrement programmatique

```python
from whoosh.plugins.manager import PluginManager

p = MonPlugin()
PluginManager.register("mon_plugin", p)
PluginManager.enable("mon_plugin")
```

## Entry point

```toml
# pyproject.toml
[project.entry-points."whoosh_ng.plugins"]
mon_plugin = "mon_package.plugin:MonPlugin"
```

## Test

```python
def test_plugin_setup():
    plugin = MonPlugin()
    registry = InMemoryRegistry()
    plugin.setup(registry)
    assert registry.get("generator", "autocomplete") is not None
```
