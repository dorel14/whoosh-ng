---
color_scheme: dark
title: "Middleware Examples"
parent: "Examples"
nav_order: 5
---

# Middleware Examples

Practical examples for building and using Whoosh-NG middleware.

## 1. Logging Middleware

```python
from whoosh.middleware.base import Middleware
from whoosh.middleware.context import MiddlewareContext

class LoggingMiddleware(Middleware):
    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        print(f"[SEARCH] Query: {context.query}")
        return context

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        if context.results is not None:
            print(f"[RESULTS] Found {len(context.results)} hits")
        return context
```

## 2. Metrics Middleware

```python
from whoosh.middleware.base import Middleware
from whoosh.middleware.context import MiddlewareContext

class MetricsMiddleware(Middleware):
    def __init__(self) -> None:
        self._metrics = {}

    def after_index(self, context: MiddlewareContext) -> MiddlewareContext:
        self._metrics["documents_indexed"] = self._metrics.get("documents_indexed", 0) + 1
        return context

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        self._metrics["searches_executed"] = self._metrics.get("searches_executed", 0) + 1
        return context

    def get_metrics(self) -> dict:
        return dict(self._metrics)
```

## 3. Cache Middleware

```python
from whoosh.middleware.base import Middleware
from whoosh.middleware.context import MiddlewareContext

class SearchCacheMiddleware(Middleware):
    def __init__(self) -> None:
        self._cache = {}

    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        if context.query and str(context.query) in self._cache:
            context.metadata["_cached_result"] = self._cache[str(context.query)]
        return context

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        if context.query and context.results is not None:
            self._cache[str(context.query)] = context.results
        return context
```

## 4. Applying Middleware to an Index

```python
from whoosh.middleware.chain import MiddlewareChain
from whoosh.middleware.integration import apply_middleware_to_searcher

# Create middleware chain
chain = MiddlewareChain([
    LoggingMiddleware(),
    MetricsMiddleware(),
])

# Apply to a searcher
with ix.searcher() as base_searcher:
    searcher = apply_middleware_to_searcher(base_searcher, chain.middlewares)
    results = searcher.search(query)
```

## 5. Middleware Lifecycle

```python
class LifecycleMiddleware(Middleware):
    def startup(self, context):
        print("Middleware initialized")

    def shutdown(self, context):
        print("Middleware shutting down")

    def on_error(self, context, exc):
        print(f"Error: {exc}")
        raise exc
```

## Key Hooks

| Hook | Phase | Context |
|------|-------|---------|
| `startup` | Init | Called once on middleware init |
| `shutdown` | Cleanup | Called once on teardown |
| `before_index` | Indexing | Before document added |
| `after_index` | Indexing | After document added |
| `before_delete` | Deletion | Before document deleted |
| `after_delete` | Deletion | After document deleted |
| `before_search` | Search | Before query executed |
| `after_search` | Search | After results returned |
| `on_error` | Error | When exception occurs |
| `on_commit` | Commit | After writer.commit() |