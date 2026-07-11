---
title: "Middleware"
nav_order: 27
parent: "Guides"
lang: fr
---

# Middleware

Le pipeline de middleware permet d'intercepter et modifier les opérations d'indexation et de recherche. C'est le mécanisme d'extension principal pour les préoccupations transverses comme le logging, le cache, les métriques et la sécurité.

## Concepts de base

Un middleware est une classe qui implémente des hooks dans le cycle de vie :

```python
from whoosh.middleware.base import Middleware
from whoosh.middleware.context import MiddlewareContext

class MonMiddleware(Middleware):
    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        # Modifier context.query ou context.metadata
        return context

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        # Accéder à context.results
        return context
```

## Hooks disponibles

| Hook | Quand | Utilisations courantes |
|------|------|------------------------|
| `startup(context)` | Initialisation | Ouvrir connexions, remplir caches |
| `shutdown(context)` | Nettoyage | Fermer connexions, flush buffers |
| `before_index(context)` | Avant indexation | Validation, enrichissement, flags compression |
| `after_index(context)` | Après indexation | Métriques, événements, invalidation cache |
| `before_delete(context)` | Avant suppression | Journalisation audit, contrôle d'accès |
| `after_delete(context)` | Après suppression | Métriques, invalidation cache |
| `before_search(context)` | Avant recherche | Réécriture de requête, cache, auth |
| `after_search(context)` | Après résultats | Logging, métriques, modification résultats |
| `on_error(context, exc)` | Sur exception | Gestion d'erreur, fallbacks |
| `on_commit(context)` | Après commit | Métriques, notifications |

## Classes intégrées

### MetricsMiddleware

```python
from whoosh.middleware import MetricsMiddleware

metrics = MetricsMiddleware()
# Après opérations:
stats = metrics.get_metrics()
# Retourne: {"documents_indexed": N, "searches_executed": N}
```

### CacheMiddleware

```python
from whoosh.middleware import CacheMiddleware

cache = CacheMiddleware()
cached = cache.get_cached("requête utilisateur")
cache.set_cached("requête utilisateur", results)
```

## MiddlewareChain

```python
from whoosh.middleware import MiddlewareChain

chain = MiddlewareChain([
    MetricsMiddleware(),
    CacheMiddleware()
])

# Exécuter un hook before
context = MiddlewareContext("search")
context.query = "test"
context = chain.run_before("before_search", context)

# ... opération core ...

# Exécuter un hook after
context = chain.run_after("after_search", context)
```

## Intégration

### Avec Writer

```python
from whoosh.middleware.integration import apply_middleware_to_writer

writer = apply_middleware_to_writer(ix.writer(), chain.middlewares)

with writer:
    writer.add_document(title="Bonjour", content="Monde")
```

### Avec Searcher

```python
from whoosh.middleware.integration import apply_middleware_to_searcher

searcher = apply_middleware_to_searcher(ix.searcher(), chain.middlewares)
results = searcher.search("query")
```

## Exemple: middleware personnalisé

```python
class RequestLoggingMiddleware(Middleware):
    """Journaliser toutes les recherches."""

    def before_search(self, context: MiddlewareContext):
        context.metadata["request_id"] = generate_request_id()
        logger.info(f"Recherche: {context.query}")
        return context

    def after_search(self, context: MiddlewareContext):
        logger.info(f"Trouvé: {len(context.results)} résultats")
        return context

class RateLimitMiddleware(Middleware):
    """Abandonner les recherches dépassant la limite."""

    def before_search(self, context: MiddlewareContext):
        if not rate_limiter.allow(context):
            raise StopOperation("Limite de taux dépassée")
        return context
```

## Gestion des erreurs

```python
class ResilientMiddleware(Middleware):
    """Continuer malgré les erreurs non critiques."""

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        try:
            send_to_analytics(context.results)
        except Exception:
            logger.warning("Analytics failed", exc_info=True)
        return context
```

## Bonnes pratiques

1. **Sans état**: Utilisez `context.metadata` pour les données par requête
2. **Fail fast**: Utilisez `fail_open=True` uniquement pour middleware non critique
3. **L'ordre compte**: Placez le cache avant les métriques, l'auth avant le routage
4. **Performance**: Gardez les hooks légers; utilisez async pour les I/O
5. **Testabilité**: Mockez le contexte pour tester le middleware isolément
