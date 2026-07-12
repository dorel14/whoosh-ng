---
color_scheme: dark
title: "Schema Design"
parent: "Guides"
nav_order: 22
---

# Schema Design

How to model documents with Whoosh-NG fields.

## Field types

| Type | Searchable | Stored |
|------|------------|--------|
| TEXT | Yes | Optional |
| ID | Yes | Optional |
| KEYWORD | Yes | Optional |
| STORED | No | Yes |
| NUMERIC | Yes | Optional |
| DATETIME | Yes | Optional |
| BOOLEAN | Yes | Optional |
| VectorField | Provider | Optional |

## Building a schema

```python
from whoosh.fields import Schema, TEXT, ID, KEYWORD, STORED, NUMERIC, BOOLEAN, VectorField

schema = Schema(
    title=TEXT(stored=True),
    slug=ID(stored=True, unique=True),
    content=TEXT,
    tags=KEYWORD(lowercase=True, commas=True),
    published=NUMERIC(int, stored=True),
    featured=BOOLEAN(stored=True),
    embedding=VectorField(dimensions=384, metric="cosine")
)
```

## Multi-value fields

Pass lists for multiple values.

```python
writer.add_document(
    title="Multi-tag post",
    tags=["whoosh", "python", "search"],
    content="..."
)
```

## Per-field boost

Boost fields at write time.

```python
writer.add_document(
    title="Breaking News",
    title_boost=3.0,
    content="..."
)
```

## SchemaBuilder

```python
from whoosh.fields import SchemaBuilder, TEXT, ID, NUMERIC

schema = (
    SchemaBuilder()
    .field("title", TEXT(stored=True))
    .field("path", ID(stored=True, unique=True))
    .field("rating", NUMERIC(float, stored=True))
    .build()
)
```

## Modifying fields

```python
writer.add_field("summary", TEXT(stored=True))
writer.remove_field("legacy_field")
```
