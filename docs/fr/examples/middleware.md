---
title: "Exemples de middleware"
parent: "Exemples"
lang: fr
nav_order: 5
---

# Exemples de middleware

Exemples pratiques de middlewares d'indexation et de recherche.

## Middleware de logging

```python
from whoosh.middleware.base import Middleware, MiddlewareContext
from whoosh.middleware.integration import apply_middleware_to_writer, apply_middleware_to_searcher

class LoggingMiddleware(Middleware):
    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        print(f"search: {context.query}")
        return context

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        if context.results is not None:
            print(f"results: {len(context.results)}")
        return context
```

## Appliqué au searcher

```python
chain = MiddlewareChain([LoggingMiddleware()])
searcher = apply_middleware_to_searcher(ix.searcher(), chain.middlewares)
results = searcher.search(q)
```
