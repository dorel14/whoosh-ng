---
title: "Middleware & Pipeline de Plugins"
nav_order: 41
lang: fr
---

# Middleware & Pipeline de Plugins

Module: `whoosh.middleware`, `whoosh.middleware.chain`, `whoosh.middleware.context`, `whoosh_modern.middleware`
Version: 2.0.0

Le pipeline de middleware permet d'intercepter et de modifier les opérations d'indexation et de recherche. C'est le mécanisme d'extension principal pour les préoccupations transverses comme la journalisation, la mise en cache, les métriques, la réécriture de requêtes et la sécurité. Le middleware peut provenir à la fois du package core `whoosh.middleware` et des plugins chargés via le `PluginManager`.

## Vue d'ensemble de l'architecture

```text
Writer/Searcher  ───►  MiddlewareChain
                           ├── Middleware 1 (hook before)
                           ├── Middleware 2 (hook before)
                           ├── ─── opération core ───
                           ├── Middleware 2 (hook after, inverse)
                           └── Middleware 1 (hook after, inverse)
```

- Les **hooks `before_*`** s'exécutent dans l'ordre d'enregistrement
- Les **hooks `after_*`** s'exécutent dans l'ordre inverse (comme une pile / oignon)
- Si un hook lève `StopOperation`, le pipeline s'arrête gracieusement
- Si `fail_open=False` (défaut), les exceptions se propagent immédiatement

## Classes de Base du Middleware

### Middleware (Classe de Base)

Localisée dans `whoosh.middleware.base`. Les sous-classes implémentent les hooks du cycle de vie :

```python
from whoosh.middleware.base import Middleware
from whoosh.middleware.context import MiddlewareContext

class MyMiddleware(Middleware):
    def startup(self, context: MiddlewareContext) -> None:
        """Appelé une fois quand le middleware est initialisé."""
        pass

    def shutdown(self, context: MiddlewareContext) -> None:
        """Appelé une fois quand le middleware est détruit."""
        pass

    def before_index(self, context: MiddlewareContext) -> MiddlewareContext:
        """Appelé avant qu'un document soit indexé. Modifier context.document."""
        return context

    def after_index(self, context: MiddlewareContext) -> MiddlewareContext:
        """Appelé après qu'un document a été indexé."""
        return context

    def before_delete(self, context: MiddlewareContext) -> MiddlewareContext:
        """Appelé avant la suppression d'un document."""
        return context

    def after_delete(self, context: MiddlewareContext) -> MiddlewareContext:
        """Appelé après la suppression d'un document."""
        return context

    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        """Appelé avant l'exécution d'une requête. Modifier context.query."""
        return context

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        """Appelé après le retour des résultats. Accéder à context.results."""
        return context

    def on_error(self, context: MiddlewareContext, exc: Exception) -> None:
        """Appelé quand une exception survient. Re-raise par défaut."""
        raise exc

    def on_commit(self, context: MiddlewareContext) -> None:
        """Appelé après une opération de commit."""
        pass
```

### MiddlewareContext

Localisé dans `whoosh.middleware.context`. L'objet contexte passé à chaque hook :

```python
class MiddlewareContext:
    def __init__(self, operation: str) -> None:
        self.operation: str           # ex: "add_document", "search"
        self.index: Any = None        # L'instance Index
        self.backend: Any = None       # Le backend de stockage
        self.writer: Any = None        # L'IndexWriter (si applicable)
        self.searcher: Any = None      # Le Searcher (si applicable)
        self.document: dict[str, Any] | None  # Document à indexer
        self.query: str = ""           # La chaîne de requête de recherche
        self.collector: Any = None     # Le collecteur (si applicable)
        self.results: Any = None       # Résultats de recherche
        self.labels: dict[str, Any] = {}    # Paires clé-valeur arbitraires
        self.metadata: dict[str, Any] = {} # Métadonnées par requête
```

Utilisez `context.copy()` pour créer une copie superficielle si vous devez préserver l'état.

### MiddlewareChain

Localisé dans `whoosh.middleware.chain`. Ordonnance l'exécution des middleware :

```python
from whoosh.middleware.chain import MiddlewareChain
from whoosh.middleware.context import MiddlewareContext

chain = MiddlewareChain([
    MetricsMiddleware(),
    CacheMiddleware(),
])

# Hooks before (dans l'ordre)
context = MiddlewareContext("search")
context.query = "hello world"
context = chain.run_before("before_search", context)

# ... opération de recherche core ...

# Hooks after (dans l'ordre inverse)
context = chain.run_after("after_search", context)
print(context.results)
```

**Support asynchrone** : Utilisez `async_run_before()`, `async_run_after()`, `async_run_on_error()` et `run_hook()` pour un middleware asynchrone.

### MiddlewareRegistry

Localisé dans `whoosh.middleware.registry`. Un registre au niveau de la classe pour les middleware nommés :

```python
from whoosh.middleware.registry import MiddlewareRegistry

MiddlewareRegistry.register("my_mw", MyMiddleware(), owner="my_plugin")
mw = MiddlewareRegistry.get("my_mw")
MiddlewareRegistry.unregister("my_mw")
print(MiddlewareRegistry.list_all())  # ['my_mw', ...]
```

## Intégration du Middleware

### Wrappers: MiddlewareWriter & MiddlewareSearcher

Localisés dans `whoosh.middleware.wrappers`. Ces wrappers enveloppent le writer/searcher core pour exécuter automatiquement les hooks de middleware :

```python
from whoosh.middleware.wrappers import MiddlewareWriter, MiddlewareSearcher
from whoosh.middleware.chain import MiddlewareChain

chain = MiddlewareChain([MetricsMiddleware(), CacheMiddleware()])

# Envelopper un writer
with MiddlewareWriter(ix.writer(), chain) as writer:
    writer.add_document(title="Hello", content="World")

# Envelopper un searcher
with MiddlewareSearcher(ix.searcher(), chain) as searcher:
    results = searcher.search(query)
```

### Assistants d'Intégration

Localisés dans `whoosh.middleware.integration` :

```python
from whoosh.middleware.integration import apply_middleware_to_writer, apply_middleware_to_searcher

# Charge automatiquement le middleware depuis PluginManager si chain non fournie
writer = apply_middleware_to_writer(ix.writer())
searcher = apply_middleware_to_searcher(ix.searcher())
```

## Middleware Intégrés

### Middleware Core (`whoosh.middleware.base`)

| Classe                  | Hooks              | Description                              |
|------------------------|--------------------|------------------------------------------|
| `CompressionMiddleware` | `before_index`    | Marque les documents avec `_compressed = True` |
| `EncryptionMiddleware`  | `before_index`    | Marque les documents avec `_encrypted = True`  |
| `MetricsMiddleware`     | `after_index`, `after_search` | Compte les documents indexés et les recherches |
| `CacheMiddleware`       | `before_search`, `after_search` | Mise en cache en mémoire des résultats |

### Observabilité (`whoosh.middleware.metrics`)

`PrometheusMiddleware` — exporte des métriques vers Prometheus (nécessite `prometheus-client`) :

```python
from whoosh.middleware.metrics import PrometheusMiddleware

# Nécessite: pip install whoosh-ng[metrics]
prom = PrometheusMiddleware()
# Exporte: whoosh_searches_total, whoosh_documents_indexed_total, whoosh_search_duration_seconds
```

### Middleware Moderne (`whoosh_modern.middleware`)

#### Pipeline de Résilience (`whoosh_modern.middleware.pipeline`)

Ces middleware utilisent un **API de type wrapper** (pattern décorateur) plutôt que des hooks :

| Classe                  | Description                              |
|------------------------|------------------------------------------|
| `RetryMiddleware`      | Réessaie les opérations échouées avec backoff exponentiel |
| `LoggingMiddleware`    | Journalise le temps d'exécution et les erreurs |
| `CacheMiddleware`      | Met en cache les résultats d'opérations (éviction LRU) |
| `MiddlewarePipeline`   | Enchaîne plusieurs middleware de type wrapper |

```python
from whoosh_modern.middleware import MiddlewarePipeline, RetryMiddleware, LoggingMiddleware

pipeline = MiddlewarePipeline(
    LoggingMiddleware(),
    RetryMiddleware(attempts=3, backoff="exponential", jitter=True),
)

result = pipeline.execute(lambda: my_index_operation())
```

#### Middleware de Stockage (`whoosh_modern.middleware.storage`)

| Classe                  | Description                              |
|------------------------|------------------------------------------|
| `StorageMiddleware`    | Redirige la persistance vers des fournisseurs de stockage pluginables |
| `FileStorageProvider`  | Stockage sur système de fichiers local   |
| `SQLiteStorageProvider`| Stockage blob SQLite                    |
| `S3StorageProvider`    | Stockage cloud S3 / S3-compatible       |

```python
from whoosh_modern.middleware.storage import StorageMiddleware, FileStorageProvider

storage = StorageMiddleware(FileStorageProvider("/data/index"), name="primary")
```

#### Middleware de Recherche (`whoosh_modern.middleware.search`)

| Classe                      | Description                              |
|----------------------------|------------------------------------------|
| `QueryRewriteMiddleware`   | Réécrit `context.query` avant la recherche |
| `RankingMiddleware`        | Re-classe `context.results` après la recherche |

```python
from whoosh_modern.middleware.search import QueryRewriteMiddleware

def add_synonyms(query: str) -> str:
    # Étendre la requête avec des synonymes avant l'exécution
    return query + " " + get_synonyms(query)

rewriter = QueryRewriteMiddleware(rewriter=add_synonyms)
```

#### Middleware d'Analyse (`whoosh_modern.middleware.analyzer`)

| Classe                  | Description                              |
|------------------------|------------------------------------------|
| `StemmingMiddleware`   | Applique un stemmer aux champs de document et à la requête |
| `SynonymMiddleware`    | Étend le texte avec des synonymes (placeholder) |

## Créer un Middleware Personnalisé

### Middleware Basé sur des Hooks

```python
from whoosh.middleware.base import Middleware
from whoosh.middleware.context import MiddlewareContext

class RequestLoggingMiddleware(Middleware):
    """Journaliser toutes les recherches avec le timing."""

    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        import time
        context.metadata["_start_time"] = time.time()
        logger.info(f"[RECHERCHE] Requête: {context.query}")
        return context

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        elapsed = time.time() - context.metadata.get("_start_time", time.time())
        result_count = len(context.results) if context.results is not None else 0
        logger.info(f"[RÉSULTATS] Trouvé {result_count} résultats en {elapsed:.3f}s")
        return context
```

### Middleware de Type Wrapper

```python
from whoosh_modern.middleware.pipeline import Middleware as WrapMiddleware

class RetryMiddleware(WrapMiddleware):
    """Réessaie les opérations échouées avec backoff."""

    def __init__(self, attempts: int = 3) -> None:
        self._attempts = attempts

    def wrap(self, operation):
        def wrapped(*args, **kwargs):
            last_exc = None
            for attempt in range(self._attempts):
                try:
                    return operation(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    if attempt < self._attempts - 1:
                        time.sleep(2 ** attempt)
            raise last_exc
        return wrapped
```

### Middleware avec Intégration de Plugin

Enregistrer du middleware via un plugin pour qu'il soit automatiquement découvert :

```python
from whoosh.plugins.manager import Plugin

class LoggingPlugin(Plugin):
    name = "logging"
    version = "1.0.0"
    middleware = ["whoosh_modern.middleware.pipeline.LoggingMiddleware"]

    def register(self, manager):
        manager.register_middleware(
            "logging",
            LoggingMiddleware(),
        )
```

## Gestion des Erreurs

### StopOperation

Abandonner une opération de pipeline gracieusement :

```python
from whoosh.middleware.exceptions import StopOperation

class RateLimitMiddleware(Middleware):
    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        if not rate_limiter.allow(context):
            raise StopOperation("Limite de taux dépassée")
        return context
```

### Comportement fail_open

```python
class ResilientMiddleware(Middleware):
    def on_error(self, context: MiddlewareContext, exc: Exception) -> None:
        try:
            send_to_analytics(context.results)
        except Exception:
            # Journaliser mais ne pas échouer la recherche
            logger.warning("Analytics failed", exc_info=True)
        # La chaîne de middleware continue
```

## Découverte de Middleware depuis les Plugins

Quand `PluginManager.load_plugins()` est appelé, tous les plugins qui déclarent une liste `middleware` auront leurs classes de middleware importées et instanciées. La méthode `get_middleware_chain()` construit une `MiddlewareChain` à partir de tous les middleware enregistrés :

```python
from whoosh.plugins.manager import PluginManager

PluginManager.load_plugins()  # Découvre les plugins et leurs middleware

manager = PluginManager._default
chain = manager.get_middleware_chain()
# chain est une MiddlewareChain prête à l'emploi
```

## Bonnes Pratiques

1. **Sans état** : Utilisez `context.metadata` pour les données par requête, pas les attributs d'instance
2. **Hooks légers** : Gardez les hooks `before_*` et `after_*` rapides ; utilisez async pour les E/S
3. **L'ordre compte** : Placez le cache avant les métriques, l'authentification avant le routage
4. **Fail fast** : N'utilisez `fail_open=True` que pour les middleware non critiques
5. **Testabilité** : Mockez le `MiddlewareContext` pour tester le middleware indépendamment
6. **Nettoyage** : Implémentez `shutdown()` pour les ressources comme les connexions et les minuteurs

## Voir Aussi

- [Guide Système de Plugins](plugins-sprint-c.md) — Enregistrement et entry points des plugins
- [Exemples: Middleware](../examples/middleware.md) — Patterns de middleware pratiques
- [API: Middleware](../api/middleware.md) — Référence complète de l'API
- [API: Middleware Pipeline (moderne)](../api/modern.md) — Extensions middleware modernes