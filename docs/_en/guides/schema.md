---
title: "Schema Design"
nav_order: 30
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

## Search Models

Whoosh-NG can auto-map Python models (dataclasses, Pydantic, SQLAlchemy, SQLModel, msgspec) to a Whoosh `Schema` using `ModelIndex`.

### Level 1: Auto-mapping

```python
from dataclasses import dataclass
from whoosh_modern.models import ModelIndex

@dataclass
class Book:
    title: str
    count: int
    tag: str | None = None

idx = ModelIndex(Book)
schema = idx.schema
```

### Level 2: Explicit options

```python
from whoosh_modern.models import SearchField, SearchOptions

class Book:
    title: str = SearchField(fulltext=True, stored=True)
    count: int = SearchField(sortable=True)
    tag: str = SearchField(multi=True)
```

### Integrations

```python
# Pydantic
from whoosh_modern.models import register_model
from pydantic import BaseModel

class BookModel(BaseModel):
    title: str
    year: int

idx = register_model(BookModel)

# SQLAlchemy
from sqlalchemy import Column, Integer, String
from whoosh_modern.models import register_model

class BookSQL:
    __tablename__ = "book"
    title = Column(String, info={"search": {"fulltext": True}})
    year = Column(Integer, info={"search": {"sortable": True}})

idx = register_model(BookSQL)
```

### Converting instances

```python
doc = idx.to_whoosh_document(book_instance)
writer.add_document(**doc)
```

## Best practices

1. **Minimal**: Only index what you search
2. **STORED sparingly**: Increases index size
3. **Unique fields**: Use `unique=True` for identifiers
4. **Field boost**: Boost important fields at schema level
5. **TEXT options**: Disable `phrase` if you don't need phrase search

