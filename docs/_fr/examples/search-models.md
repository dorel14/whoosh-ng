---
title: "Modèles de recherche"
lang: fr
nav_order: 210
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

## Nettoyage

```python
shutil.rmtree(tmp)
```
