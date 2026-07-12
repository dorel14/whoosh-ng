---
color_scheme: dark
title: "Exemples Middleware"
parent: "Exemples"
nav_order: 5
lang: fr
---

# Exemples de Middleware

Des exemples pratiques pour construire et utiliser les middleware de Whoosh-NG.

## 1. Middleware de Logging

```python
from whoosh.middleware.base import Middleware
from whoosh.middleware.context import MiddlewareContext

class LoggingMiddleware(Middleware):
    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        print(f"[RECHERCHE] Requête: {context.query}")
        return context

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        if context.results is not None:
            print(f"[RÉSULTATS] {len(context.results)} résultats trouvés")
        return context
```

## 2. Middleware de Metrics

```python
from whoosh.middleware.base import Middleware
from whoosh.middleware.context import MiddlewareContext

class MetricsMiddleware(Middleware):
    def __init__(self) -> None:
        self._metrics = {}

    def after_index(self, context: MiddlewareContext) -> MiddlewareContext:
        self._metrics["documents_indexés"] = self._metrics.get("documents_indexés", 0) + 1
        return context

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        self._metrics["recherches_executées"] = self._metrics.get("recherches_executées", 0) + 1
        return context

    def get_metrics(self) -> dict:
        return dict(self._metrics)
```

## 3. Middleware de Cache

```python
from whoosh.middleware.base import Middleware
from whoosh.middleware.context import MiddlewareContext

class SearchCacheMiddleware(Middleware):
    def __init__(self) -> None:
        self._cache = {}

    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        if context.query and str(context.query) in self._cache:
            context.metadata["_résultat_cache"] = self._cache[str(context.query)]
        return context

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        if context.query and context.results is not None:
            self._cache[str(context.query)] = context.results
        return context
```

## 4. Appliquer un Middleware

```python
from whoosh.middleware.chain import MiddlewareChain
from whoosh.middleware.integration import apply_middleware_to_searcher

chain = MiddlewareChain([
    LoggingMiddleware(),
    MetricsMiddleware(),
])

with ix.searcher() as base_searcher:
    searcher = apply_middleware_to_searcher(base_searcher, chain.middlewares)
    results = searcher.search(query)
```

## Points clés

| Hook | Phase | Description |
|------|-------|-------------|
| `startup` | Init | Appelé une fois à l'initialisation |
| `shutdown` | Nettoyage | Appelé à la fermeture |
| `before_index` | Indexation | Avant l'ajout d'un document |
| `after_index` | Indexation | Après l'ajout d'un document |
| `before_delete` | Suppression | Avant la suppression |
| `after_delete` | Suppression | Après la suppression |
| `before_search` | Recherche | Avant l'exécution de la requête |
| `after_search` | Recherche | Après le retour des résultats |
| `on_error` | Erreur | En cas d'exception |
| `on_commit` | Commit | Après writer.commit() |
