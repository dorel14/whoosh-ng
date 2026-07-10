---
title: "Plugins"
nav_order: 26
parent: "Guides"
lang: fr
---

# Plugins

Whoosh-NG utilise une architecture à plugins pour garder le core léger tout en permettant des fonctionnalités avancées. Les plugins sont chargés via des entry points et gérés par le `PluginManager`.

## Architecture des plugins

```text
PluginManager
    ├── load_plugins()           # Auto-découvrir depuis entry points
    ├── register(name, plugin)   # Enregistrement manuel
    ├── enable(name)            # Activer un plugin
    ├── disable(name)           # Désactiver un plugin
    ├── get(name)               # Récupérer un plugin
    └── list_plugins()          # Lister tous les plugins
```

## Plugins intégrés

| Plugin | Description |
|--------|-------------|
| whoosh-ng-vector | Recherche vectorielle (NumPy, HNSW, Faiss) |
| whoosh-ng-autocomplete | Autocomplétion par edge n-gram |
| whoosh-ng-fastapi | Factory d'app FastAPI |
| whoosh-ng-observability | Métriques Prometheus |
| whoosh-ng-admin | Interface d'administration |

## Créer un plugin

Tout plugin hérite de `BasePlugin` :

```python
from whoosh.plugins.base import BasePlugin

class MonPlugin(BasePlugin):
    name = "mon_plugin"
    version = "1.0.0"
    dependencies = []

    def setup(self, registry):
        """Appelé quand le plugin est activé."""
        registry.register("mon_provider", MonProvider())

    def teardown(self, registry):
        """Appelé quand le plugin est désactivé."""
        registry.unregister("mon_provider")

    def middleware(self):
        """Middleware à injecter dans le pipeline."""
        return [MonMiddleware()]

    def on_startup(self):
        """Appelé une fois au démarrage."""
        pass

    def on_shutdown(self):
        """Appelé une fois à l'arrêt."""
        pass
```

## Enregistrement de plugin

### Via entry_points (pyproject.toml)

```toml
[project.entry-points."whoosh_ng.plugins"]
mon_plugin = "mon_package.plugin:MonPlugin"
```

### Programmatique

```python
from whoosh.plugins.manager import PluginManager

plugin = MonPlugin()
PluginManager.register("mon_plugin", plugin)
PluginManager.enable("mon_plugin")
```

## Cycle de vie d'un plugin

```
register() -> setup() -> enable() -> hooks middleware -> teardown() -> disable()
```

## Dépendances entre plugins

```python
class VectorPlugin(BasePlugin):
    name = "vector"
    dependencies = ["metrics"]  # Requiert le plugin metrics
```

Le `PluginManager` résout l'ordre de chargement et détecte les conflits.

## Bonnes pratiques

1. **Un plugin, une responsabilité**: Gardez les plugins petits et focalisés
2. **Déclarez les dépendances**: Aidez PluginManager à résoudre l'ordre
3. **Nettoyez bien**: Implémentez `teardown()` pour supprimer les registres
