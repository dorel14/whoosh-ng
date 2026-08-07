---
title: "Schema Design"
sidebar_position: 30
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
writer.add_document(
    title="Multi-tag post",
    tags=["whoosh", "python", "search"],
    content="..."
)
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

`ModelIndex` inspects type annotations and maps them to Whoosh fields:

| Python type | Whoosh field |
|-------------|--------------|
| `str` | `TEXT` |
| `int` / `float` | `NUMERIC` |
| `bool` | `BOOLEAN` |
| `datetime` / `date` | `DATETIME` |
| `Decimal` | `NUMERIC(int, decimal_places=2)` |
| `Enum` | `KEYWORD` |
| `bytes` | `KEYWORD` (hex-encoded) |
| `list[str]` | `KEYWORD` |
| `Optional[T]` | mapped type or `STORED` |

ID fields are auto-detected: explicit `SearchOptions(id=True)` > field named `id`/`ID`/`_id` > first `str` field.

### Level 2: Explicit options

Use `SearchField` to override defaults:

```python
from whoosh_modern.models import SearchField, SearchOptions

class Book:
    title: str = SearchField(fulltext=True, stored=True, analyzer="Simple")
    count: int = SearchField(sortable=True)
    tags: list[str] = SearchField(multi=True)
```

### Level 3: Annotated types

Use `Annotated` to attach metadata directly to annotations:

```python
from typing import Annotated
from whoosh_modern.models import SearchField

class Book:
    title: Annotated[str, SearchField(fulltext=True, stored=True)]
```

### Integrations

#### Dataclass

```python
from dataclasses import dataclass
from whoosh_modern.models import ModelIndex

@dataclass
class Article:
    title: str
    body: str
    published: datetime.datetime

idx = ModelIndex(Article)
```

#### Pydantic v2

```python
from pydantic import BaseModel
from whoosh_modern.models import register_model

class Article(BaseModel):
    title: str
    body: str
    published: datetime.datetime

    # Per-field search metadata via json_schema_extra
    model_config = {"json_schema_extra": {"search": {"fulltext": True}}}

idx = register_model(Article)
```

#### SQLAlchemy

```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import DeclarativeBase
from whoosh_modern.models import register_model

class Base(DeclarativeBase):
    pass

class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True)
    title = Column(String, info={"search": {"fulltext": True, "stored": True}})
    published = Column(DateTime, info={"search": {"sortable": True}})

idx = register_model(Article)
```

#### SQLModel

```python
from sqlmodel import SQLModel, Field
from whoosh_modern.models import register_model

class Article(SQLModel, table=True):
    id: int = Field(primary_key=True)
    title: str = Field(sa_column_kwargs={"info": {"search": {"fulltext": True}}})
    published: datetime.datetime

idx = register_model(Article)
```

#### msgspec

```python
import msgspec
from whoosh_modern.models import register_model

class Article(msgspec.Struct):
    title: str = msgspec.field(metadata={"search": {"fulltext": True}})
    published: datetime.datetime

idx = register_model(Article)
```

### Converting instances

```python
doc = idx.to_whoosh_document(book_instance)
writer.add_document(**doc)
```

`to_whoosh_document` handles:
- dataclass: `dataclasses.fields()` iteration
- Pydantic/SQLModel: `model_fields` iteration
- SQLAlchemy: `__mapper__.columns` iteration
- Enum values converted to `.value`
- `bytes` converted to hex string

## Best practices

1. **Minimal**: Only index what you search
2. **STORED sparingly**: Increases index size
3. **Unique fields**: Use `unique=True` for identifiers
4. **Field boost**: Boost important fields at schema level
5. **TEXT options**: Disable `phrase` if you don't need phrase search
6. **ID field**: Let `ModelIndex` auto-detect or explicitly mark with `SearchOptions(id=True)`
