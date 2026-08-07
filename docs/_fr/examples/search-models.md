---
title: "Modèles de recherche"
lang: fr
nav_order: 211
---

# Modèles de recherche

Exemples de mapping automatique de modèles Python vers des schémas Whoosh.

## Dataclass

```python
from dataclasses import dataclass
from whoosh.fields import Schema, TEXT, NUMERIC
from whoosh_modern.models import ModelIndex
import tempfile
import shutil

@dataclass
class Book:
    title: str
    year: int
    tags: list[str] | None = None

idx = ModelIndex(Book)
print(idx.schema)
```

## Pydantic

```python
from pydantic import BaseModel
from whoosh_modern.models import register_model

class BookModel(BaseModel):
    title: str
    year: int
    tags: list[str] | None = None

idx = register_model(BookModel)
schema = idx.schema
```

## SQLAlchemy

```python
from sqlalchemy import Column, Integer, String
from whoosh_modern.models import register_model

class BookSQL:
    __tablename__ = "book"
    title = Column(String, info={"search": {"fulltext": True, "stored": True}})
    year = Column(Integer, info={"search": {"sortable": True}})

idx = register_model(BookSQL)
schema = idx.schema
```

## SQLModel

```python
from sqlmodel import SQLModel, Field
from whoosh_modern.models import register_model

class Book(SQLModel, table=True):
    id: int = Field(primary_key=True)
    title: str = Field(sa_column_kwargs={"info": {"search": {"fulltext": True}}})
    year: int

idx = register_model(Book)
schema = idx.schema
```

## msgspec

```python
import msgspec
from whoosh_modern.models import register_model

class Book(msgspec.Struct):
    title: str = msgspec.field(metadata={"search": {"fulltext": True}})
    year: int

idx = register_model(Book)
schema = idx.schema
```

## Indexation de documents

```python
from whoosh import index

tmp = tempfile.mkdtemp()
ix = index.create_in(tmp, schema)

with ix.writer() as w:
    book = Book(title="Guide Whoosh", year=2024, tags=["python", "recherche"])
    doc = idx.to_whoosh_document(book)
    w.add_document(**doc)
    w.commit()
```

## Auto-indexation avec AutoIndexer

```python
from whoosh_modern.models import AutoIndexer

auto = AutoIndexer(ix, on_error="raise")
auto.register(Book)

# Indexer une instance unique
book = Book(title="Nouveau livre", year=2024, tags=["python"])
auto.index(book)

# Supprimer par ID
auto.remove(book)

# Versions asynchrones
await auto.index_async(book)
await auto.remove_async(book)
```

Pour les modèles SQLAlchemy, `AutoIndexer` se connecte automatiquement aux événements `after_insert`, `after_update` et `after_delete`.

## Nettoyage

```python
shutil.rmtree(tmp)
```
