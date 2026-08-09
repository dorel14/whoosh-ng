---
title: "Middleware & Plugin Pipeline"
nav_order: 41
permalink: /en/guides/middleware-sprint-c/
lang: en
---

# Middleware & Plugin Pipeline

Module: `whoosh.middleware`, `whoosh.middleware.chain`, `whoosh.middleware.context`, `whoosh_modern.middleware`
Version: 2.0.0

The middleware pipeline allows you to intercept and modify indexing and search operations. It is the primary extension mechanism for cross-cutting concerns like logging, caching, metrics, query rewriting, and security. Middleware can come from both the core `whoosh.middleware` package and from plugins loaded via the `PluginManager`.

## Architecture Overview

```text
Writer/Searcher  ───►  MiddlewareChain
                           ├── Middleware 1 (before hook)
                           ├── Middleware 2 (before hook)
                           ├── ─── core operation ───
                           ├── Middleware 2 (after hook, reverse)
                           └── Middleware 1 (after hook, reverse)
```

- **Before hooks** execute in registration order
- **After hooks** execute in reverse order (like a stack / onion)
- If a hook raises `StopOperation`, the pipeline aborts gracefully
- If `fail_open=False` (default), exceptions propagate immediately

## Core Middleware Classes

### Middleware (Base Class)

Located in `whoosh.middleware.base`. Subclasses implement lifecycle hooks:

```python
from whoosh.middleware.base import Middleware
from whoosh.middleware.context import MiddlewareContext

class MyMiddleware(Middleware):
    def startup(self, context: MiddlewareContext) -> None:
        """Called once when middleware is initialized."""
        pass

    def shutdown(self, context: MiddlewareContext) -> None:
        """Called once when middleware is torn down."""
        pass

    def before_index(self, context: MiddlewareContext) -> MiddlewareContext:
        """Called before a document is indexed. Modify context.document."""
        return context

    def after_index(self, context: MiddlewareContext) -> MiddlewareContext:
        """Called after a document is indexed."""
        return context

    def before_delete(self, context: MiddlewareContext) -> MiddlewareContext:
        """Called before a document is deleted."""
        return context

    def after_delete(self, context: MiddlewareContext) -> MiddlewareContext:
        """Called after a document is deleted."""
        return context

    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        """Called before a search query is executed. Modify context.query."""
        return context

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        """Called after results are returned. Access context.results."""
        return context

    def on_error(self, context: MiddlewareContext, exc: Exception) -> None:
        """Called when an exception occurs. Re-raise by default."""
        raise exc

    def on_commit(self, context: MiddlewareContext) -> None:
        """Called after a commit operation."""
        pass
```

### MiddlewareContext

Located in `whoosh.middleware.context`. The context object passed to every hook:

```python
class MiddlewareContext:
    def __init__(self, operation: str) -> None:
        self.operation: str           # e.g., "add_document", "search"
        self.index: Any = None        # The Index instance
        self.backend: Any = None       # The storage backend
        self.writer: Any = None        # The IndexWriter (if applicable)
        self.searcher: Any = None      # The Searcher (if applicable)
        self.document: dict[str, Any] | None  # Document being indexed
        self.query: str = ""           # The search query string
        self.collector: Any = None     # The collector (if applicable)
        self.results: Any = None       # Search results
        self.labels: dict[str, Any] = {}    # Arbitrary labels/key-value pairs
        self.metadata: dict[str, Any] = {} # Per-request metadata
```

Use `context.copy()` to create a shallow copy if you need to preserve state.

### MiddlewareChain

Located in `whoosh.middleware.chain`. Orchestrates middleware execution:

```python
from whoosh.middleware.chain import MiddlewareChain
from whoosh.middleware.context import MiddlewareContext

chain = MiddlewareChain([
    MetricsMiddleware(),
    CacheMiddleware(),
])

# Before hooks (in order)
context = MiddlewareContext("search")
context.query = "hello world"
context = chain.run_before("before_search", context)

# ... core search operation ...

# After hooks (in reverse order)
context = chain.run_after("after_search", context)
print(context.results)
```

**Async support**: Use `async_run_before()`, `async_run_after()`, `async_run_on_error()`, and `run_hook()` for async middleware.

### MiddlewareRegistry

Located in `whoosh.middleware.registry`. A class-level registry for named middleware:

```python
from whoosh.middleware.registry import MiddlewareRegistry

MiddlewareRegistry.register("my_mw", MyMiddleware(), owner="my_plugin")
mw = MiddlewareRegistry.get("my_mw")
MiddlewareRegistry.unregister("my_mw")
print(MiddlewareRegistry.list_all())  # ['my_mw', ...]
```

## Middleware Integration

### Wrappers: MiddlewareWriter & MiddlewareSearcher

Located in `whoosh.middleware.wrappers`. These wrap the core writer/searcher to automatically execute middleware hooks:

```python
from whoosh.middleware.wrappers import MiddlewareWriter, MiddlewareSearcher
from whoosh.middleware.chain import MiddlewareChain

chain = MiddlewareChain([MetricsMiddleware(), CacheMiddleware()])

# Wrap a writer
with MiddlewareWriter(ix.writer(), chain) as writer:
    writer.add_document(title="Hello", content="World")

# Wrap a searcher
with MiddlewareSearcher(ix.searcher(), chain) as searcher:
    results = searcher.search(query)
```

### Integration Helpers

Located in `whoosh.middleware.integration`:

```python
from whoosh.middleware.integration import apply_middleware_to_writer, apply_middleware_to_searcher

# Auto-loads middleware from PluginManager if chain is not provided
writer = apply_middleware_to_writer(ix.writer())
searcher = apply_middleware_to_searcher(ix.searcher())
```

## Built-in Middleware

### Core Middleware (`whoosh.middleware.base`)

| Class                  | Hooks              | Description                              |
|------------------------|--------------------|------------------------------------------|
| `CompressionMiddleware` | `before_index`    | Marks documents with `_compressed = True` |
| `EncryptionMiddleware`  | `before_index`    | Marks documents with `_encrypted = True`  |
| `MetricsMiddleware`     | `after_index`, `after_search` | Tracks indexed docs and search count |
| `CacheMiddleware`       | `before_search`, `after_search` | In-memory result caching |

### Observability (`whoosh.middleware.metrics`)

`PrometheusMiddleware` — exports metrics to Prometheus (requires `prometheus-client`):

```python
from whoosh.middleware.metrics import PrometheusMiddleware

# Requires: pip install whoosh-ng[metrics]
prom = PrometheusMiddleware()
# Exports: whoosh_searches_total, whoosh_documents_indexed_total, whoosh_search_duration_seconds
```

### Modern Middleware (`whoosh_modern.middleware`)

#### Resilience Pipeline (`whoosh_modern.middleware.pipeline`)

These use a **wrap-style** API (decorator pattern) rather than hooks:

| Class                  | Description                              |
|------------------------|------------------------------------------|
| `RetryMiddleware`      | Retries failed operations with exponential backoff |
| `LoggingMiddleware`    | Logs operation execution time and errors |
| `CacheMiddleware`      | Caches operation results (LRU eviction)  |
| `MiddlewarePipeline`   | Chains multiple wrap-style middlewares   |

```python
from whoosh_modern.middleware import MiddlewarePipeline, RetryMiddleware, LoggingMiddleware

pipeline = MiddlewarePipeline(
    LoggingMiddleware(),
    RetryMiddleware(attempts=3, backoff="exponential", jitter=True),
)

result = pipeline.execute(lambda: my_index_operation())
```

#### Storage Middleware (`whoosh_modern.middleware.storage`)

| Class                  | Description                              |
|------------------------|------------------------------------------|
| `StorageMiddleware`    | Routes persistence through pluggable storage providers |
| `FileStorageProvider`  | Local filesystem storage                 |
| `SQLiteStorageProvider`| SQLite-backed blob storage               |
| `S3StorageProvider`    | S3 / S3-compatible cloud storage         |

```python
from whoosh_modern.middleware.storage import StorageMiddleware, FileStorageProvider

storage = StorageMiddleware(FileStorageProvider("/data/index"), name="primary")
```

#### Search Middleware (`whoosh_modern.middleware.search`)

| Class                      | Description                              |
|----------------------------|------------------------------------------|
| `QueryRewriteMiddleware`   | Rewrites `context.query` before search   |
| `RankingMiddleware`        | Re-ranks `context.results` after search  |

```python
from whoosh_modern.middleware.search import QueryRewriteMiddleware

def add_synonyms(query: str) -> str:
    # Expand query with synonyms before execution
    return query + " " + get_synonyms(query)

rewriter = QueryRewriteMiddleware(rewriter=add_synonyms)
```

#### Analyzer Middleware (`whoosh_modern.middleware.analyzer`)

| Class                  | Description                              |
|------------------------|------------------------------------------|
| `StemmingMiddleware`   | Applies a stemmer to document fields and query |
| `SynonymMiddleware`    | Expands text with synonyms (placeholder) |

## Creating Custom Middleware

### Hook-Based Middleware

```python
from whoosh.middleware.base import Middleware
from whoosh.middleware.context import MiddlewareContext

class RequestLoggingMiddleware(Middleware):
    """Log all search requests with timing."""

    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        import time
        context.metadata["_start_time"] = time.time()
        logger.info(f"[SEARCH] Query: {context.query}")
        return context

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        elapsed = time.time() - context.metadata.get("_start_time", time.time())
        result_count = len(context.results) if context.results is not None else 0
        logger.info(f"[RESULTS] Found {result_count} hits in {elapsed:.3f}s")
        return context
```

### Wrap-Style Middleware

```python
from whoosh_modern.middleware.pipeline import Middleware as WrapMiddleware

class RetryMiddleware(WrapMiddleware):
    """Retry failed operations with backoff."""

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

### Middleware with Plugin Integration

Register middleware via a plugin so it's automatically discovered:

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

## Error Handling

### StopOperation

Abort a pipeline operation gracefully:

```python
from whoosh.middleware.exceptions import StopOperation

class RateLimitMiddleware(Middleware):
    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        if not rate_limiter.allow(context):
            raise StopOperation("Rate limit exceeded")
        return context
```

### fail_open Behavior

```python
class ResilientMiddleware(Middleware):
    def on_error(self, context: MiddlewareContext, exc: Exception) -> None:
        try:
            send_to_analytics(context.results)
        except Exception:
            # Log but don't fail the search
            logger.warning("Analytics failed", exc_info=True)
        # Middleware chain continues
```

## Middleware Discovery from Plugins

When `PluginManager.load_plugins()` is called, all plugins that declare a `middleware` list will have those middleware classes imported and instantiated. The `get_middleware_chain()` method builds a `MiddlewareChain` from all registered middleware:

```python
from whoosh.plugins.manager import PluginManager

PluginManager.load_plugins()  # Discovers plugins and their middleware

manager = PluginManager._default
chain = manager.get_middleware_chain()
# chain is a MiddlewareChain ready for use
```

## Best Practices

1. **Statelessness**: Use `context.metadata` for per-request data, not instance attributes
2. **Lightweight hooks**: Keep `before_*` and `after_*` hooks fast; use async for I/O
3. **Order matters**: Place caching before metrics, authentication before routing
4. **Fail fast**: Only use `fail_open=True` for non-critical middleware
5. **Test isolation**: Mock the `MiddlewareContext` to test middleware independently
6. **Clean up**: Implement `shutdown()` for resources like connections and timers

## See Also

- [Plugin System Guide](plugins-advanced.md) — Plugin registration and entry points
- [Middleware Examples](../examples/middleware.md) — Practical middleware patterns
- [API: Middleware](../api/middleware.md) — Full API reference
- [API: Middleware Pipeline (modern)](../api/modern.md) — Modern middleware extensions
