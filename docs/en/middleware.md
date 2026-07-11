---
title: "Middleware Architecture"
nav_order: 40
---

# Middleware Architecture

Whoosh-NG uses a middleware pipeline to allow plugins to intercept and modify indexing and search operations.

## Available Hooks

| Hook | Operation | Description |
|------|-----------|-------------|
| `startup(context)` | Lifecycle | Called when middleware is initialized |
| `shutdown(context)` | Lifecycle | Called when middleware is torn down |
| `before_index(context)` | Index | Before a document is added |
| `after_index(context)` | Index | After a document is added |
| `before_delete(context)` | Index | Before a document is deleted |
| `after_delete(context)` | Index | After a document is deleted |
| `before_search(context)` | Search | Before a query is executed |
| `after_search(context)` | Search | After results are returned |
| `on_error(context, exc)` | Error | When an exception occurs |
| `on_commit(context)` | Index | After a commit operation |

## Creating a Middleware

```python
from whoosh.middleware.base import Middleware
from whoosh.middleware.context import MiddlewareContext

class LoggingMiddleware(Middleware):
    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        print(f"Searching for: {context.query}")
        return context

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        print(f"Found {len(context.results) if context.results else 0} results")
        return context
```

## Built-in Middlewares

- **CompressionMiddleware**: Marks documents for compression at the backend level
- **EncryptionMiddleware**: Marks documents for encryption at the backend level
- **MetricsMiddleware**: Tracks indexing/search metrics internally
- **CacheMiddleware**: Provides in-memory search caching

## Execution Order

Middlewares execute in order for before hooks, in reverse order for after hooks:

```
before: M1 -> M2 -> M3 -> core
after:  core -> M3 -> M2 -> M1
```
