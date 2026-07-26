---
color_scheme: dark
title: "Middleware API"
nav_order: 7
parent: "API Reference"
---

# Middleware API

Reference for the middleware pipeline.

## MiddlewareContext

```python
class whoosh.middleware.context.MiddlewareContext
```

Context object passed through all middleware hooks.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `operation` | `str` | Operation type: `index`, `search`, `delete`, `commit` |
| `index` | `Any` | The index object |
| `backend` | `Any` | The backend storage object |
| `writer` | `Any` | The index writer |
| `searcher` | `Any` | The searcher |
| `document` | `dict \| None` | Document being indexed/deleted |
| `query` | `str` | Search query string |
| `collector` | `Any` | Collector instance |
| `results` | `Any` | Search results |
| `labels` | `dict` | Middleware identification labels |
| `metadata` | `dict` | Arbitrary middleware communication data |

### Methods

#### `copy()`

```python
ctx_copy = context.copy()
```

Create a shallow copy.

---

## Middleware

```python
class whoosh.middleware.base.Middleware
```

Base class for all middleware.

### Methods

#### `startup()`

```python
def startup(self, context: MiddlewareContext) -> None:
    """Called once on initialization."""
```

#### `shutdown()`

```python
def shutdown(self, context: MiddlewareContext) -> None:
    """Called once on teardown."""
```

#### `before_index()`

```python
def before_index(self, context: MiddlewareContext) -> MiddlewareContext:
    """Called before indexing a document."""
```

#### `after_index()`

```python
def after_index(self, context: MiddlewareContext) -> MiddlewareContext:
    """Called after indexing a document."""
```

#### `before_delete()`

```python
def before_delete(self, context: MiddlewareContext) -> MiddlewareContext:
    """Called before deleting a document."""
```

#### `after_delete()`

```python
def after_delete(self, context: MiddlewareContext) -> MiddlewareContext:
    """Called after deleting a document."""
```

#### `before_search()`

```python
def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
    """Called before executing a search."""
```

#### `after_search()`

```python
def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
    """Called after search results are returned."""
```

#### `on_error()`

```python
def on_error(self, context: MiddlewareContext, exc: Exception) -> None:
    """Called on exception. Re-raise by default."""
```

#### `on_commit()`

```python
def on_commit(self, context: MiddlewareContext) -> None:
    """Called after commit."""
```

---

## MiddlewareChain

```python
class whoosh.middleware.chain.MiddlewareChain
```

Orchestrates ordered middleware execution.

### Methods

#### `add()`

```python
chain.add(middleware: Middleware)
```

Add a middleware.

---

#### `extend()`

```python
chain.extend(middlewares: list[Middleware])
```

Add multiple middlewares.

---

#### `run_before()`

```python
context = chain.run_before(
    hook_name: str,
    context: MiddlewareContext,
    fail_open: bool = False
)
```

Run before hooks in order.

---

#### `run_after()`

```python
context = chain.run_after(
    hook_name: str,
    context: MiddlewareContext,
    fail_open: bool = False
)
```

Run after hooks in reverse.

---

#### `run_on_error()`

```python
chain.run_on_error(context, exc, fail_open=False)
```

Call on_error hooks.

---

## Built-in Middleware Classes

### MetricsMiddleware

```python
class whoosh.middleware.base.MetricsMiddleware
```

Tracks indexing/search counts.

#### Methods

##### `after_index()`

Increment documents indexed count.

##### `after_search()`

Increment searches executed count.

##### `get_metrics()`

```python
metrics = metrics_mw.get_metrics() -> dict
```

Return collected metrics.

---

### CacheMiddleware

```python
class whoosh.middleware.base.CacheMiddleware
```

In-memory search cache.

#### Methods

##### `before_search()`

Check cache for query.

##### `after_search()`

Store results in cache.

##### `get_cached()`

```python
cached = cache_mw.get_cached(query: str) -> Any
```

##### `set_cached()`

```python
cache_mw.set_cached(query: str, results: Any)
```

---

### CompressionMiddleware

```python
class whoosh.middleware.base.CompressionMiddleware
```

Mark documents for compression at backend level.

---

### EncryptionMiddleware

```python
class whoosh.middleware.base.EncryptionMiddleware
```

Mark documents for encryption at backend level.

---

## Exceptions

### StopOperation

```python
class whoosh.middleware.exceptions.StopOperation(Exception)
```

Raise to abort an operation.

---

## Integration Helpers

### `apply_middleware_to_writer()`

```python
def apply_middleware_to_writer(
    writer: IndexWriter,
    middleware: list[Middleware] = None
) -> MiddlewareWriter
```

---

### `apply_middleware_to_searcher()`

```python
def apply_middleware_to_searcher(
    searcher: Searcher,
    middleware: list[Middleware] = None
) -> MiddlewareSearcher
```
