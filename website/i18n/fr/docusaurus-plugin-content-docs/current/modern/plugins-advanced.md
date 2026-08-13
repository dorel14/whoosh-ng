---
title: "Système de Plugins"
sidebar_position: 51
---

# Système de Plugins

Module : `whoosh.plugins.manager`
Version : 2.0.0

L'architecture à plugins de Whoosh-NG permet à des paquets externes d'étendre
le pipeline central d'indexation, de recherche et d'analyse. Les plugins sont
découverts via des [points d'entrée](https://docs.python.org/3/library/importlib.metadata.html#entry-points)
Python déclarés dans `pyproject.toml` et gérés par le `PluginManager`.

## Aperçu de l'architecture

```text
PluginManager (singleton)
    ├── load_plugins(group)          # Auto-découverte via les points d'entrée
    ├── register(plugin)             # Enregistrement manuel
    ├── enable(name) / disable(name) # Bascule du cycle de vie
    ├── get(name) / list_plugins()   # Inspection
    ├── get_middleware_chain()       # Construit la MiddlewareChain depuis les middlewares des plugins
    ├── register_datasource()        # Enregistre un provider de source de données
    ├── register_vector_provider()   # Enregistre un provider vectoriel
    ├── register_middleware()        # Enregistre une instance de middleware
    ├── register_embedding()         # Enregistre un provider d'embeddings
    ├── register_analyzer()          # Enregistre un analyseur nommé
    └── register_analyzer()          # Enregistre un rewriteur de requêtes
```

## Classes de base des plugins

### Plugin (ABC)

La classe de plugin racine. Les sous-classes définissent des attributs au niveau
classe et implémentent `register()`.

```python
from whoosh.plugins.manager import Plugin, PluginMetadata

class MyPlugin(Plugin):
    name = "my_plugin"
    version = "1.0.0"

    def register(self, manager: PluginManager) -> None:
        """Appelé au chargement du plugin ; enregistrez les providers ici."""
        manager.register_middleware("my_module.MyMiddleware", MyMiddleware())

    def register_hooks(self) -> None:
        """Enregistre les hooks d'événements (optionnel)."""
        from whoosh.hooks import hookimpl, register_hook

        @hookimpl
        def on_search(request, response):
            pass
        register_hook("on_search", hookimpl(on_search))
```

### AnalyzerPlugin

Pour les plugins fournissant des tokenizers/analyseurs personnalisés :

```python
from whoosh.plugins.manager import AnalyzerPlugin

class MyAnalyzerPlugin(AnalyzerPlugin):
    name = "my_analyzer"

    def register(self, manager):
        manager.register_analyzer("my_analyzer", MyTokenizer())
```

### QueryRewritePlugin

Pour les plugins transformant les requêtes avant exécution :

```python
from whoosh.plugins.manager import QueryRewritePlugin

class SynonymRewriterPlugin(QueryRewritePlugin):
    name = "synonym_rewriter"

    def rewrite(self, query, searcher):
        # Renvoie la requête modifiée
        return query
```

## PluginMetadata

Une dataclass décrivant les métadonnées du plugin :

| Champ         | Type              | Description                            |
|---------------|-------------------|----------------------------------------|
| `name`        | `str`             | Nom de plugin unique                   |
| `version`     | `str`             | Chaîne de version SemVer               |
| `depends_on`  | `list[str]`       | Noms des plugins requis                |
| `priority`    | `int`             | Priorité d'ordre de chargement (plus élevé = plus tard) |
| `middleware`  | `list[str]`       | Chemins pointés vers les classes de middleware |

## Groupes de points d'entrée

Le `PluginManager` découvre les plugins depuis ces groupes de points d'entrée
standard :

| Groupe                | Rôle                                 |
|----------------------|--------------------------------------|
| `whoosh.plugins`     | Plugins généraux                     |
| `whoosh.datasources` | Providers de source de données       |
| `whoosh.vector.providers` | Providers de similarité vectorielle |
| `whoosh.middlewares` | Classes de middleware                 |
| `whoosh.embeddings`  | Providers de modèles d'embeddings     |
| `whoosh.language`    | Analyseurs spécifiques à une langue  |
| `whoosh.apps`        | Usines d'applications (FastAPI, admin, etc.) |

## Créer et déployer un plugin

### Étape 1 : Définir la classe du plugin

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
        """Enregistre un provider vectoriel dans le VectorRegistry."""
        provider = MyCustomVectorProvider()
        VectorRegistry.register("my_vector", provider, owner=self.name)

    def register_hooks(self):
        """Enregistre des hooks optionnels (ex : on_search, on_index)."""
        pass
```

### Étape 2 : Déclarer le point d'entrée

Dans votre `pyproject.toml` :

```toml
[project]
name = "whoosh-ng-my-vector"
version = "1.0.0"
dependencies = ["whoosh-ng>=2.0"]

[project.entry-points."whoosh_ng.plugins"]
my_vector = "my_plugin.plugin:MyVectorPlugin"
```

### Étape 3 : Installer et vérifier

```bash
pip install -e .
```

```python
# Vérifie que le plugin est enregistré
from whoosh.plugins.manager import PluginManager

PluginManager.load_plugins()  # Auto-découvre tous les points d'entrée

manager = PluginManager._default
print(manager.list_plugins())
# ['whoosh_autocomplete', 'whoosh_vector', ..., 'my_vector']

# Vérifie le registre
from whoosh.registry import VectorRegistry
print(VectorRegistry.list_keys())
# ['my_vector', 'numpy']
```

## Enregistrement manuel (sans point d'entrée)

Pour les tests ou un usage programmatique :

```python
from whoosh.plugins.manager import PluginManager

manager = PluginManager()
manager.register(MyVectorPlugin())
manager.enable("my_vector")
```

## Cycle de vie des plugins

```
1. Point d'entrée découvert  ───►  2. register() appelé  ───►  3. register_hooks()
   │                               │                            │
   └── load_plugins(group)          └── enregistre provider/     └── register_hook()
                                       middleware/analyzer
```

### Activation / Désactivation

```python
from whoosh.plugins.manager import PluginManager

manager = PluginManager._default

manager.enable("my_vector")    # Active un plugin
manager.disable("my_vector")   # Désactive un plugin
print(manager.list_enabled())  # Uniquement les plugins activés
```

### Validation de version

```python
# Vérifie si un plugin respecte une version minimale
ok = manager.validate_version("my_vector", "1.0.0")
print(ok)  # True si la version du plugin >= 1.0.0
```

### Détection de conflits

```python
# Vérifie si deux plugins sont en conflit
if manager.detect_conflicts("plugin_a", "plugin_b"):
    print("Ces plugins ne peuvent pas être chargés ensemble")
```

## Référence de l'API du Plugin Manager

### `PluginManager.load_plugins(group=None)`

Charge tous les plugins depuis les groupes de points d'entrée. Si `group` est
`None`, charge depuis tous les groupes standards (`STANDARD_GROUPS`).

### `PluginManager.register(plugin)`

Enregistre une instance de plugin. Appelle `plugin.register(self)` et
`plugin.register_hooks()`. Supporte un `register()` asynchrone via `asyncio`.

### `PluginManager.get_middleware_chain()`

Construit et renvoie une `MiddlewareChain` à partir de tous les plugins
déclarant des entrées `middleware`. Les classes de middleware sont importées et
instanciées par chemin pointé.

### Méthodes d'enregistrement dans les registres

| Méthode                       | Description                          |
|------------------------------|--------------------------------------|
| `register_analyzer(name, analyzer)` | Enregistre un analyseur nommé   |
| `register_datasource(name, datasource)` | Enregistre une source de données |
| `register_vector_provider(name, provider)` | Enregistre un provider vectoriel |
| `register_middleware(name, middleware)` | Enregistre une instance de middleware |
| `register_embedding(name, embedding)` | Enregistre un provider d'embeddings |
| `register_query_rewriter(plugin)` | Enregistre un plugin de rewriteur de requêtes |

### Méthodes de recherche

| Méthode                       | Renvoie                          |
|------------------------------|----------------------------------|
| `get(name)`                  | Instance `Plugin`                |
| `list_plugins()`             | Tous les noms de plugins enregistrés |
| `list_enabled()`             | Noms des plugins activés         |
| `get_analyzer(name)`         | Analyseur appelable              |
| `list_analyzers()`           | Noms des analyseurs enregistrés  |
| `list_datasources()`         | Noms des sources de données enregistrées |
| `list_vector_providers()`    | Noms des providers vectoriels enregistrés |
| `list_middlewares()`         | Noms des middlewares enregistrés |
| `list_embeddings()`          | Noms des embeddings enregistrés  |
| `list_query_rewriters()`     | Noms des rewriteurs de requêtes enregistrés |

## Plugins intégrés

| Plugin            | Module                  | Groupe de point d'entrée |
|-------------------|-------------------------|--------------------------|
| `whoosh_autocomplete` | `whoosh_modern.autocomplete.plugin` | `whoosh.plugins` |
| `whoosh_vector`   | `whoosh_modern.vector.plugin`      | `whoosh.plugins` |
| `whoosh_fastapi`  | `whoosh_fastapi`                  | `whoosh.apps` |
| `whoosh_observability` | `whoosh.middleware.metrics`  | `whoosh.middlewares` |
| `whoosh_admin`    | `whoosh_admin`                   | `whoosh.apps` |

## Bonnes pratiques

1. **Responsabilité unique** : un plugin, une fonctionnalité
2. **Déclarer les dépendances** : utilisez `depends_on` pour les plugins requis
3. **Versionnement sémantique** : incrémentez la version pour les changements d'API
4. **Dégradation gracieuse** : vérifiez les dépendances optionnelles dans `register()`
5. **Éviter les effets de bord dans `__init__`** : toute l'initialisation dans `register()`
6. **Nettoyage** : si applicable, fournissez une logique de teardown

## Voir aussi

- [Guide du Middleware](middleware-pipeline.md) — Hooks du pipeline et middleware personnalisés
- [Guide d'Intégration des Providers](provider-integration.md) — Guide complet du pipeline pour tous les providers
- [Exemple de Développement de Plugin](../examples/plugin-dev.md) — Tutoriel pas à pas d'un plugin
- [API : Plugins](../api/plugins.md) — Référence complète de l'API
