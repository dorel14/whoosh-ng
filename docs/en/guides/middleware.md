---
title: "Middleware"
nav_order: 27
parent: "Guides"
---

# Middleware

The middleware pipeline allows you to intercept and modify indexing and search operations. It is the primary extension mechanism for cross-cutting concerns like logging, caching, metrics, and security.

## Core Concepts

A middleware is a class that implements hooks into the indexing and search lifecycle:

```python
from whoosh.middleware.base import Middleware
from whoosh.middleware.context import MiddlewareContext

class MyMiddleware(Middleware):
    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        # Modify context.query or context.metadata
        return context

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        # Access context.results
        return context
```

## Available Hooks

| Hook | When | Common Uses |
|------|------|-------------|
| `startup(context)` | Middleware initialized | Open connections, warm caches |
| `shutdown(context)` | Middleware torn down | Close connections, flush buffers |
| `before_index(context)` | Before document added | Validation, enrichment, compression flags |
| `after_index(context)` | After document added | Metrics, events, cache invalidation |
| `before_delete(context)` | Before document deleted | Audit logging, access control |
| `after_delete(context)` | After document deleted | Metrics, cache invalidation |
| `before_search(context)` | Before query executes | Query rewriting, caching, auth |
| `after_search(context)` | After results returned | Logging, metrics, result modification |
| `on_error(context, exc)` | On exception | Error handling, fallbacks |
| `on_commit(context)` | After commit | Metrics, notifications |

## Built-in Middlewares

### MetricsMiddleware

Tracks basic statistics:

```python
from whoosh.middleware import MetricsMiddleware

metrics = MetricsMiddleware()
# After operations:
stats = metrics.get_metrics()
# Returns: {"documents_indexed": N, "searches_executed": N}
```

### CacheMiddleware

Caches search results in memory:

```python
from whoosh.middleware import CacheMiddleware

cache = CacheMiddleware()

# Check cache
cached = cache.get_cached("user query string")

# Store manually
cache.set_cached("user query string", results)
```

### CompressionMiddleware

Marks documents for compression at the backend level:

```python
from whoosh.middleware import CompressionMiddleware

compression = CompressionMiddleware()
# Sets document["_compressed"] = True
```

### EncryptionMiddleware

Marks documents for encryption at the backend level:

```python
from whoosh.middleware import EncryptionMiddleware

encryption = EncryptionMiddleware()
# Sets document["_encrypted"] = True
```

## MiddlewareChain

Orchestrates middleware execution:

```python
from whoosh.middleware import MiddlewareChain

chain = MiddlewareChain([
    MetricsMiddleware(),
    CacheMiddleware()
])

# Execute before hook
context = MiddlewareContext("search")
context.query = "test"
context = chain.run_before("before_search", context)

# ... core operation ...

# Execute after hook
context = chain.run_after("after_search", context)
```

### Execution Order

- `before_*` hooks run in registration order
- `after_*` hooks run in reverse order
- If a hook raises `StopOperation`, the pipeline aborts
- If `fail_open=False`, exceptions propagate immediately

## Integration

### With Writer

```python
from whoosh.middleware.integration import apply_middleware_to_writer

writer = apply_middleware_to_writer(ix.writer(), chain.middlewares)

with writer:
    writer.add_document(title="Hello", content="World")
```

### With Searcher

```python
from whoosh.middleware.integration import apply_middleware_to_searcher

searcher = apply_middleware_to_searcher(ix.searcher(), chain.middlewares)
results = searcher.search("query")
```

### With PluginManager

```python
from whoosh.plugins.manager import PluginManager

# Plugins can provide middleware
PluginManager.load_plugins()
chain = PluginManager.get_middleware_chain()
```

## Custom Middleware Example

```python
class RequestLoggingMiddleware(Middleware):
    """Log all search requests."""

    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        context.metadata["request_id"] = generate_request_id()
        logger.info(f"Search: {context.query}")
        return context

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        logger.info(f"Found {len(context.results)} results")
        return context

class RateLimitMiddleware(Middleware):
    """Abort searches exceeding rate limit."""

    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        if not rate_limiter.allow(context):
            raise StopOperation("Rate limit exceeded")
        return context

class QueryEnrichmentMiddleware(Middleware):
    """Add synonyms to the query."""

    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        if context.query:
            context.query += " " + get_synonyms(context.query)
        return context
```

## Error Handling

```python
class ResilientMiddleware(Middleware):
    """Continue on non-critical errors."""

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        try:
            send_to_analytics(context.results)
        except Exception:
            # Log but don't fail the search
            logger.warning("Analytics failed", exc_info=True)
        return context
```

## Best Practices

1. **Stateless**: Use `context.metadata` for per-request data
2. **Fail fast**: Only use `fail_open=True` for non-critical middleware
3. **Order matters**: Place caching before metrics, auth before routing
4. **Performance**: Keep hooks lightweight; use async for I/O
5. **Testing**: Mock the context object to test middleware in isolation
