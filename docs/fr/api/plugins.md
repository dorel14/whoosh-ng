---
color_scheme: dark
title: "API Plugins"
nav_order: 6
parent: "Référence API"
lang: fr
---

# API Plugins

Système de plugins, registres de providers et discovery.

## PluginManager

```python
class whoosh.plugins.manager.PluginManager
```

Point d'entrée unique pour gérer tous les plugins.

### Méthodes

| Méthode | Description |
|---------|-------------|
| `PluginManager.load_plugins()` | Auto-découvre et charge les entry points |
| `PluginManager.register(name, plugin)` | Enregistre un plugin |
| `PluginManager.enable(name)` | Active un plugin |
| `PluginManager.disable(name)` | Désactive un plugin |
| `PluginManager.get(name)` | Retourne le plugin par nom |
| `PluginManager.list_plugins()` | Liste des plugins enregistrés |

**Exemple:**
```python
from whoosh.plugins.manager import PluginManager

# Programmatique
PluginManager.register("mon_plugin", MonPlugin())
PluginManager.enable("mon_plugin")

# Entry points (dans pyproject.toml)
# [project.entry-points."whoosh_ng.plugins"]
# mon_plugin = "mon_package.plugin:MonPlugin"
PluginManager.load_plugins()
```

## BasePlugin

```python
class whoosh.plugins.base.BasePlugin
```

Classe de base pour tous les plugins.

### Méthodes à implémenter

| Méthode | Appelée quand |
|---------|---------------|
| `setup(registry)` | Plugin activé |
| `teardown(registry)` | Plugin désactivé |
| `on_startup()` | Démarrage application |
| `on_shutdown()` | Arrêt application |

### Attributs

| Attribut | Description |
|----------|-------------|
| `name` | Nom unique |
| `version` | Version du plugin |
| `dependencies` | Liste des noms de plugins requis |

## Registre

```python
class whoosh.registry.Registry
```

Registre global pour les providers de tous types.

### Méthodes

| Méthode | Description |
|---------|-------------|
| `registry.register(name, provider, category)` | Enregistre un provider |
| `registry.get(name, category)` | Récupère un provider |
| `registry.unregister(name, category)` | Supprime un provider |
| `registry.list_providers(category)` | Liste tous les providers d'une catégorie |

**Catégories courantes:**
- `"vector_provider"`
- `"autocomplete_provider"`
- `"storage_provider"`
- `"middleware"`

## VectorRegistry

```python
from whoosh.registry import VectorRegistry

VectorRegistry.register("numpy", NumpyProvider(), "mon_app")
provider = VectorRegistry.get("numpy", "mon_app")
```

## Exception

```python
class PluginNotFoundError(Exception)
```
