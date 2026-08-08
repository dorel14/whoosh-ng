---
title: "Système de Plugins"
nav_order: 51
permalink: /fr/guides/plugins-sprint-c/
lang: fr
---

# Système de Plugins

Module: `whoosh.plugins.manager`
Version: 2.0.0

L'architecture à plugins de Whoosh-NG permet aux paquets externes d'étendre le moteur d'indexation, de recherche et d'analyse de texte. Les plugins sont découverts via les [entry points](https://docs.python.org/3/library/importlib.metadata.html#entry-points) Python déclarés dans `pyproject.toml` et gérés par le `PluginManager`.

## Vue d'ensemble de l'architecture

```text
PluginManager (singleton)
    ├── load_plugins(group)          # Auto-découverte depuis entry points
    ├── register(plugin)             # Enregistrement manuel
    ├── enable(name) / disable(name) # Activer/désactiver le cycle de vie
    ├── get(name) / list_plugins()   # Inspection
    ├── get_middleware_chain()       # Construire MiddlewareChain depuis middleware des plugins
    ├── register_datasource()        # Enregistrer un fournisseur de source de données
    ├── register_vector_provider()   # Enregistrer un fournisseur de vecteurs
    ├── register_middleware()        # Enregistrer une instance de middleware
    ├── register_embedding()         # Enregistrer un fournisseur d'embeddings
    ├── register_analyzer()          # Enregistrer un analyseur nommé
    └── register_query_rewriter()    # Enregistrer un réécrivant de requête
```

## Classes de Base des Plugins

### Plugin (ABC)

La classe de base pour tous les plugins. Les sous-classes définissent les attributs de classe et implémentent `register()` :

```python
from whoosh.plugins.manager import Plugin, PluginMetadata

class MyPlugin(Plugin):
    name = "my_plugin"
    version = "1.0.0"

    def register(self, manager: PluginManager) -> None:
        """Appelé quand le plugin est chargé ; enregistrer les fournisseurs ici."""
        manager.register_middleware("my_module.MyMiddleware", MyMiddleware())

    def register_hooks(self) -> None:
        """Enregistrer les hooks d'événements (optionnel)."""
        from whoosh.hooks import hookimpl, register_hook

        @hookimpl
        def on_search(request, response):
            pass
        register_hook("on_search", hookimpl(on_search))
```

### AnalyzerPlugin

Pour les plugins qui fournissent des tokenizers/analyseurs personnalisés :

```python
from whoosh.plugins.manager import AnalyzerPlugin

class MyAnalyzerPlugin(AnalyzerPlugin):
    name = "my_analyzer"

    def register(self, manager):
        manager.register_analyzer("my_analyzer", MyTokenizer())
```

### QueryRewritePlugin

Pour les plugins qui transforment les requêtes avant l'exécution :

```python
from whoosh.plugins.manager import QueryRewritePlugin

class SynonymRewriterPlugin(QueryRewritePlugin):
    name = "synonym_rewriter"

    def rewrite(self, query, searcher):
        # Retourner la requête modifiée
        return query
```

## PluginMetadata

Un dataclass décrivant les métadonnées du plugin :

| Champ         | Type              | Description                            |
|---------------|-------------------|----------------------------------------|
| `name`        | `str`             | Nom unique du plugin                   |
| `version`     | `str`             | Version sémantique                     |
| `depends_on`  | `list[str]`       | Noms des plugins requis                |
| `priority`    | `int`             | Priorité d'ordre de chargement (plus haut = plus tard) |
| `middleware`  | `list[str]`       | Chemins pointés vers les classes de middleware |

## Groupes d'Entry Points

Le `PluginManager` découvre les plugins depuis ces groupes d'entry points standards :

| Groupe                      | Utilisation                          |
|-----------------------------|--------------------------------------|
| `whoosh.plugins`            | Plugins généraux                     |
| `whoosh.datasources`        | Fournisseurs de sources de données   |
| `whoosh.vector.providers`   | Fournisseurs de similarité vectorielle |
| `whoosh.middlewares`        | Classes de middleware                 |
| `whoosh.embeddings`         | Fournisseurs de modèles d'embedding  |
| `whoosh.language`           | Analyseurs linguistiques             |
| `whoosh.apps`               | Usines d'applications (FastAPI, admin, etc.) |

## Créer et Déployer un Plugin

### Étape 1 : Définir la Classe du Plugin

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
        """Enregistrer un fournisseur de vecteurs dans le VectorRegistry."""
        provider = MyCustomVectorProvider()
        VectorRegistry.register("my_vector", provider, owner=self.name)

    def register_hooks(self):
        """Enregistrer les hooks optionnels (ex: on_search, on_index)."""
        pass
```

### Étape 2 : Déclarer l'Entry Point

Dans votre `pyproject.toml` :

```toml
[project]
name = "whoosh-ng-my-vector"
version = "1.0.0"
dependencies = ["whoosh-ng>=2.0"]

[project.entry-points."whoosh_ng.plugins"]
my_vector = "my_plugin.plugin:MyVectorPlugin"
```

### Étape 3 : Installer et Vérifier

```bash
pip install -e .
```

```python
# Vérifier que le plugin est bien enregstré
from whoosh.plugins.manager import PluginManager

PluginManager.load_plugins()  # Découvre tous les entry points

manager = PluginManager._default
print(manager.list_plugins())
# ['whoosh_autocomplete', 'whoosh_vector', ..., 'my_vector']

# Vérifier le registre
from whoosh.registry import VectorRegistry
print(VectorRegistry.list_keys())
# ['my_vector', 'numpy']
```

## Enregistrement Manuel (Sans Entry Point)

Pour les tests ou un usage programmatique :

```python
from whoosh.plugins.manager import PluginManager

manager = PluginManager()
manager.register(MyVectorPlugin())
manager.enable("my_vector")
```

## Cycle de Vie d'un Plugin

```
1. Entry point découvert  ───►  2. register() appelé  ───►  3. register_hooks()
   │                               │                            │
   └── load_plugins(group)          └── register provider/     └── register_hook()
                                      middleware/analyzer
```

### Activation / Désactivation

```python
from whoosh.plugins.manager import PluginManager

manager = PluginManager._default

manager.enable("my_vector")    # Activer un plugin
manager.disable("my_vector")   # Désactiver un plugin
print(manager.list_enabled())  # Seuls les plugins activés
```

### Validation de Version

```python
# Vérifie si un plugin respecte une version minimale
ok = manager.validate_version("my_vector", "1.0.0")
print(ok)  # True si la version du plugin >= 1.0.0
```

### Détection de Conflits

```python
# Vérifie si deux plugins entrent en conflit
if manager.detect_conflicts("plugin_a", "plugin_b"):
    print("Ces plugins ne peuvent pas être chargés ensemble")
```

## API du PluginManager

### `PluginManager.load_plugins(group=None)`

Charge tous les plugins depuis les groupes d'entry points. Si `group` est `None`, charge tous les groupes standards (`STANDARD_GROUPS`).

### `PluginManager.register(plugin)`

Enregistre une instance de plugin. Appelle `plugin.register(self)` et `plugin.register_hooks()`. Supporte les méthodes `register()` asynchrones via `asyncio`.

### `PluginManager.get_middleware_chain()`

Construit et retourne une `MiddlewareChain` à partir de tous les plugins qui déclarent une liste `middleware`. Les classes de middleware sont importées et instanciées par chemin pointé.

### Méthodes d'Enregistrement dans les Registres

| Méthode                       | Description                          |
|-------------------------------|--------------------------------------|
| `register_analyzer(name, analyzer)` | Enregistrer un analyseur nommé   |
| `register_datasource(name, datasource)` | Enregistrer une source de données  |
| `register_vector_provider(name, provider)` | Enregistrer un fournisseur de vecteurs |
| `register_middleware(name, middleware)` | Enregistrer une instance de middleware |
| `register_embedding(name, embedding)` | Enregistrer un fournisseur d'embeddings |
| `register_query_rewriter(plugin)` | Enregistrer un plugin réécrivant des requêtes |

### Méthodes de Recherche

| Méthode                       | Retourne                          |
|-------------------------------|----------------------------------|
| `get(name)`                   | Instance `Plugin`                |
| `list_plugins()`              | Noms de tous les plugins enregistrés |
| `list_enabled()`              | Noms des plugins activés         |
| `get_analyzer(name)`          | Analyseur callable               |
| `list_analyzers()`            | Noms des analyseurs enregistrés  |
| `list_datasources()`          | Noms des sources de données enregistrées |
| `list_vector_providers()`     | Noms des fournisseurs de vecteurs enregistrés |
| `list_middlewares()`          | Noms des middleware enregistrés  |
| `list_embeddings()`           | Noms des fournisseurs d'embeddings enregistrés |
| `list_query_rewriters()`      | Noms des réécrivants enregistrés |

## Plugins Intégrés

| Plugin            | Module                  | Groupe d'Entry Point       |
|-------------------|-------------------------|----------------------------|
| `whoosh_autocomplete` | `whoosh_modern.autocomplete.plugin` | `whoosh.plugins` |
| `whoosh_vector`   | `whoosh_modern.vector.plugin`      | `whoosh.plugins` |
| `whoosh_fastapi`  | `whoosh_fastapi`                  | `whoosh.apps` |
| `whoosh_observability` | `whoosh.middleware.metrics`  | `whoosh.middlewares` |
| `whoosh_admin`    | `whoosh_admin`                   | `whoosh.apps` |

## Bonnes Pratiques

1. **Responsabilité unique** : Un plugin, une fonctionnalité
2. **Déclarez les dépendances** : Utilisez `depends_on` pour les plugins requis
3. **Version sémantique** : Incrémentez la version pour les changements d'API
4. **Degradation gracieuse** : Vérifiez les dépendances optionnelles dans `register()`
5. **Pas d'effets de bord dans `__init__`** : Toute l'initialisation dans `register()`
6. **Nettoyage** : Si applicable, fournissez une logique de teardown

## Voir Aussi

- [Guide Middleware](middleware-sprint-c.md) — Pipeline hooks et middleware personnalisé
- [Exemple: Développement de Plugin](../examples/plugin-dev.md) — Tutoriel pas à pas
- [API: Plugins](../api/plugins.md) — Référence complète de l'API
