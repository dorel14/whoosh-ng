---
color_scheme: dark
title: "API Overview"
nav_order: 0
parent: "API Reference"
---

# API Overview

This section provides a comprehensive reference of the Whoosh-NG public API.

## Modules

| Module | Description |
|--------|-------------|
| `whoosh.index` | High-level index creation, opening, and management |
| `whoosh.fields` | Schema and field type definitions |
| `whoosh.writing` | Writer classes and merge policies |
| `whoosh.searching` | Searcher, Results, and collectors |
| `whoosh.query` | Query classes and parsers |
| `whoosh.qparser` | Query parser implementation |
| `whoosh.analysis` | Tokenizers, filters, and analyzers |
| `whoosh.highlight` | Search result highlighting |
| `whoosh.spelling` | Spelling correction |
| `whoosh.sorting` | Facets and sorting |
| `whoosh.event_bus` | Event system |
| `whoosh.hooks` | Hook system |
| `whoosh.middleware` | Middleware pipeline |
| `whoosh.plugins` | Plugin system and registry |
| `whoosh.backends` | Storage backends |
| `whoosh.vector` | Vector search providers |
| `whoosh_modern.autocomplete` | Autocomplete providers |
| `whoosh_fastapi` | FastAPI integration |

## Quick Reference

### Index Lifecycle

```python
from whoosh.index import create_in, open_dir, exists_in

# Create
ix = create_in("indexdir", schema)

# Open
ix = open_dir("indexdir")

# Check
if exists_in("indexdir"):
    ix = open_dir("indexdir")
```

### Writing

```python
with ix.writer() as writer:
    writer.add_document(field1=value1, field2=value2)
    writer.commit()
```

### Reading

```python
from whoosh.qparser import QueryParser

with ix.searcher() as searcher:
    qp = QueryParser("content", ix.schema)
    q = qp.parse("query")
    results = searcher.search(q)
```

### Schema

```python
from whoosh.fields import Schema, TEXT, ID, NUMERIC

schema = Schema(
    title=TEXT(stored=True),
    path=ID(stored=True, unique=True),
    count=NUMERIC(int, stored=True)
)
```
