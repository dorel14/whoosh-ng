---
title: "Migration Guide"
nav_order: 32
parent: "Getting Started"
---

# Migration Guide

This guide helps you migrate from Whoosh legacy or Whoosh-Reloaded 3.x to Whoosh-NG 4.0.

## From Whoosh 1.x/2.x (Legacy)

### Import Paths

| Legacy | Whoosh-NG |
|--------|-----------|
| `import whoosh` | `import whoosh` |
| `from whoosh.index import create_in` | `from whoosh.index import create_in` |
| `from whoosh.fields import Schema, TEXT` | `from whoosh.fields import Schema, TEXT` |
| `from whoosh.qparser import QueryParser` | `from whoosh.qparser import QueryParser` |

The core API is intentionally stable. Most existing code works unchanged.

### Spelling API

```python
# Legacy
from whoosh.spelling import SpellChecker
corrector = SpellChecker(ix.reader(), "content")

# Whoosh-NG
from whoosh.spelling import ReaderCorrector
corrector = ReaderCorrector(ix.searcher().reader(), "content", ix.schema["content"])
suggestions = corrector.suggest("helo", limit=5)
```

### Highlighting

```python
# Legacy API unchanged
results[0].highlights("content")
```

## From Whoosh-Reloaded 3.x

### No Breaking Changes

Whoosh-NG is a continuation of Whoosh-Reloaded. All existing code works as-is.

### Optional: Plugin Migration

If you used `whoosh_modern` directly:

```python
# Old
from whoosh_modern.vector.numpy_provider import NumpyProvider

# New (via registry)
from whoosh.vector import NumpyProvider
from whoosh.registry import VectorRegistry

VectorRegistry.register("numpy", NumpyProvider(), "my_app")
```

### Middleware (New in 4.0)

```python
# Optional migration: add middleware to existing code

from whoosh.middleware import Middleware, MiddlewareContext

class LoggingMiddleware(Middleware):
    def before_search(self, context):
        print(f"Query: {context.query}")
        return context

# Wrap existing writer/searcher
writer = apply_middleware_to_writer(ix.writer(), [LoggingMiddleware()])
```

### SchemaBuilder (New in 4.0)

```python
# Old
schema = Schema(title=TEXT(stored=True), content=TEXT)

# New (fluent API)
from whoosh.fields import SchemaBuilder

schema = (
    SchemaBuilder()
    .field("title", TEXT(stored=True))
    .field("content", TEXT)
    .build()
)
```

## Upgrade Checklist

1. **Update dependencies**:
   ```bash
   pip install --upgrade whoosh-ng
   ```

2. **Run tests**:
   ```bash
   uv run pytest tests/ -q
   ```

3. **Update optional deps** (if using plugins):
   ```bash
   pip install whoosh-ng[all]
   ```

4. **Review middleware**: Consider adding middleware for cross-cutting concerns

5. **Update config**: If using `whoosh.config`, review new options

## Deprecations

| Feature | Status | Replacement |
|---------|--------|-------------|
| `whoosh_modern.vector` | Deprecated | `whoosh.vector` |
| Raw `whoosh.store` | Deprecated | `whoosh.backends` |
| Direct `SegmentWriter` usage | Discouraged | Use `IndexWriter` |

## Breaking Changes

Whoosh-NG 4.0 maintains backward compatibility. If you find a breaking change, please report it as an issue.

### Exception Hierarchy

New in 4.0: `MiddlewareError` and `StopOperation` in middleware:

```python
from whoosh.middleware.exceptions import MiddlewareError, StopOperation
```

## Getting Help

- [GitHub Issues](https://github.com/your-org/whoosh-NG/issues)
- [Documentation](/en/)
- [Migration Examples](/en/examples/migration)