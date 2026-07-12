---
color_scheme: dark
title: "Whoosh-NG Documentation"
nav_order: 0
---

# Whoosh-NG Documentation

Pure-Python full-text indexing and search library, modernized for 2025+.

## Quick Start

```bash
pip install whoosh-ng
```

```python
import whoosh.index as index
from whoosh.fields import Schema, TEXT, ID

schema = Schema(id=ID(stored=True), content=TEXT())
ix = index.create_in("indexdir", schema)

with ix.writer() as w:
    w.add_document(id="1", content="hello world")

with ix.searcher() as s:
    results = s.search("world")
    print(results[0])
```

## Features

- Pure Python, no native dependencies
- Embedded search engine
- Plugin architecture for extensibility
- Middleware pipeline for cross-cutting concerns
- Vector search support (NumPy, HNSW, Faiss)
- Async support via optional extra
