---
title: "Basic Indexing"
parent: "Exemples"
nav_order: 1
---

# Basic Indexing

Examples for indexing documents in Whoosh-NG.

## Set Up

```python
from whoosh import index
from whoosh.fields import Schema, TEXT, ID, NUMERIC

schema = Schema(
    title=TEXT(stored=True),
    path=ID(stored=True, unique=True),
    content=TEXT,
    rating=NUMERIC(float, stored=True)
)
```

## Quick Start Index

```python
from whoosh import index

# Clean prior index (development only!)
import shutil
try:
    shutil.rmtree("indexdir")
except FileNotFoundError:
    pass

ix = index.create_in("indexdir", schema)

with ix.writer() as writer:
    writer.add_document(
        title="First Document",
        content="Hello world from whoosh",
        path="/1",
        rating=4.5
    )
    writer.commit()
```

## Reload Index

```python
ix = index.open_dir("indexdir")

with ix.writer() as writer:
    writer.add_document(
        title="Second Document",
        content="Python search library",
        path="/2",
        rating=5.0
    )
    writer.commit()
```

## Bulk Insert

```python
documents = [
    {"title": "Doc 1", "content": "Lorem ipsum", "path": "/1", "rating": 3.0},
    {"title": "Doc 2", "content": "Dolor sit amet", "path": "/2", "rating": 4.0},
    {"title": "Doc 3", "content": "Consectetur adipiscing elit", "path": "/3", "rating": 5.0},
]

with ix.writer() as writer:
    for doc in documents:
        writer.add_document(**doc)
    writer.commit()
```

## Update Document

```python
with ix.writer() as writer:
    writer.update_document(
        path="/1",
        title="Updated Title",
        content="Updated content",
        rating=4.8
    )
    writer.commit()
```

## Delete Document

```python
from whoosh.query import Term

with ix.writer() as writer:
    writer.delete_by_term("path", "/2")
    writer.delete_by_query(Term("path", "/3"))
    writer.commit()
```

## Buffered Writer for High Throughput

```python
from whoosh.writing import BufferedWriter

buffered = BufferedWriter(ix, period=60, limit=100)

try:
    for doc in large_dataset:
        with buffered:
            buffered.add_document(**doc)
finally:
    buffered.close()
```
