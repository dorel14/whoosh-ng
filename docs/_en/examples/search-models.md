---
title: "Search Models"
nav_order: 210
---

# Search Models

Examples for auto-mapping Python models to Whoosh schemas.

## Dataclass

```python
from dataclasses import dataclass
from whoosh.fields import Schema, TEXT, NUMERIC
from whoosh_modern.models import register_dataclass_model
import tempfile
import shutil

@dataclass
class Book:
    title: str
    year: int
    tags: list[str] | None = None

idx = register_dataclass_model(Book)
print(idx.schema)
```

## Pydantic

```python
from pydantic import BaseModel
from whoosh_modern.models import register_pydantic_model

class BookModel(BaseModel):
    title: str
    year: int
    tags: list[str] | None = None

idx = register_pydantic_model(BookModel)
schema = idx.schema
```

## SQLAlchemy

```python
from sqlalchemy import Column, Integer, String
from whoosh_modern.models import register_sqlalchemy_model

class BookSQL:
    __tablename__ = "book"
    title = Column(String, info={"search": {"fulltext": True, "stored": True}})
    year = Column(Integer, info={"search": {"sortable": True}})

idx = register_sqlalchemy_model(BookSQL)
schema = idx.schema
```

## SQLModel

```python
from sqlmodel import SQLModel, Field
from whoosh_modern.models import register_sqlmodel_model

class Book(SQLModel, table=True):
    id: int = Field(primary_key=True)
    title: str = Field(sa_column_kwargs={"info": {"search": {"fulltext": True}}})
    year: int

idx = register_sqlmodel_model(Book)
schema = idx.schema
```

## msgspec

```python
import msgspec
from whoosh_modern.models import register_msgspec_model

class Book(msgspec.Struct):
    title: str = msgspec.field(metadata={"search": {"fulltext": True}})
    year: int

idx = register_msgspec_model(Book)
schema = idx.schema
```

## Indexing documents

```python
from whoosh import index

tmp = tempfile.mkdtemp()
ix = index.create_in(tmp, schema)

with ix.writer() as w:
    book = Book(title="Whoosh Guide", year=2024, tags=["python", "search"])
    doc = idx.to_whoosh_document(book)
    w.add_document(**doc)
    w.commit()
```

## Auto-indexing with AutoIndexer

```python
from whoosh_modern.models import AutoIndexer

auto = AutoIndexer(ix, on_error="raise")
auto.register(Book)

# Index a single instance
book = Book(title="New Book", year=2024, tags=["python"])
auto.index(book)

# Remove by ID
auto.remove(book)

# Async versions
await auto.index_async(book)
await auto.remove_async(book)
```

For SQLAlchemy models, `AutoIndexer` automatically hooks into `after_insert`, `after_update`, and `after_delete` events.

## Cleanup

```python
shutil.rmtree(tmp)
```
