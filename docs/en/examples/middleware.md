---
title: "Middleware Examples"
parent: "Exemples"
nav_order: 5
---

# Middleware Examples

Practical examples for indexing and search middleware.

## Logging middleware

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

## Cache middleware

```python
from whoosh.middleware.base import Middleware, MiddlewareContext

class SimpleCacheMiddleware(Middleware):
    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        context.extra["cache_check"] = True
        return context

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        context.extra["cache_save"] = True
        return context
```

## Applied to searcher

```python
chain = MiddlewareChain([LoggingMiddleware(), SimpleCacheMiddleware()])
searcher = apply_middleware_to_searcher(ix.searcher(), chain.middlewares)
results = searcher.search(q)
```
