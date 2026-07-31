---
title: "Auto-Indexing"
nav_order: 31
---

# Auto-Indexing

Whoosh-NG provides `AutoIndexer` to automatically keep a Whoosh index in sync with your data models.

## Overview

`AutoIndexer` maintains a registry of models and their corresponding Whoosh schemas. It can:

- **Index** model instances into a Whoosh index
- **Remove** instances by their ID field
- **Hook** into SQLAlchemy events for automatic sync
- **Handle errors** with configurable strategies

## Basic usage

```python
from whoosh_modern.models import AutoIndexer, ModelIndex
from whoosh.filedb.filestore import RamStorage

# Create a Whoosh index
storage = RamStorage()
schema = ModelIndex(Book).schema
ix = storage.create_index(schema)

# Create auto-indexer
auto = AutoIndexer(ix, on_error="raise")

# Register a model
auto.register(Book)

# Index an instance
book = Book(title="Hello", year=2024)
auto.index(book)

# Remove by ID
auto.remove(book)
```

## Error handling

The `on_error` parameter controls what happens when indexing fails:

- `"raise"` (default): re-raise the exception
- `"log"`: log the error and continue
- `"skip"`: silently skip the error

```python
auto = AutoIndexer(ix, on_error="log")
```

## SQLAlchemy integration

For SQLAlchemy models, `AutoIndexer` automatically registers event listeners:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from whoosh_modern.models import register_sqlalchemy_model

engine = create_engine("sqlite:///app.db")
Base = DeclarativeBase()

class Book(Base):
    __tablename__ = "books"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]

Base.metadata.create_all(engine)

# Register with AutoIndexer
auto = AutoIndexer(ix)
auto.register(Book)

# Now any SQLAlchemy session operation automatically syncs:
# - after_insert -> index.document()
# - after_update -> index.document()
# - after_delete -> remove.document()
```

## Async support

For async applications, use `index_async` and `remove_async`:

```python
import asyncio

async def main():
    book = Book(title="Async", year=2024)
    await auto.index_async(book)
    await auto.remove_async(book)

asyncio.run(main())
```

These methods run the synchronous indexing in a worker thread via `asyncio.to_thread()` to avoid blocking the event loop.

## API reference

### `AutoIndexer(index, on_error="raise")`

- `index`: a Whoosh `Index` instance
- `on_error`: error handling strategy (`"raise"`, `"log"`, `"skip"`)

### Methods

- `register(model) -> ModelIndex`: register a model class and return its `ModelIndex`
- `index(instance)`: index a model instance
- `remove(instance)`: remove a model instance by its ID field
- `index_async(instance)`: async version of `index`
- `remove_async(instance)`: async version of `remove`

### Helper functions

```python
from whoosh_modern.models import index_document, remove_document

# One-off indexing without creating an AutoIndexer
index_document(ix, book_instance, on_error="raise")
remove_document(ix, book_instance, on_error="raise")
```
