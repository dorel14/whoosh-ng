---
color_scheme: dark
title: "Core API"
nav_order: 1
parent: "API Reference"
---

# Core API

The core module provides the main `Index` class and related functions for managing indexes.

## Functions

### create_in

```python
whoosh.index.create_in(
    dirname: str,
    schema: Schema,
    indexname: str = "MAIN",
    create: bool = True,
    **kwargs
) -> FileIndex
```

Create a new index in the given directory.

**Args:**
- `dirname (str)`: Path to the directory where the index will be stored.
- `schema (Schema)`: The `Schema` object defining the index fields.
- `indexname (str)`: Name of the index. Allows multiple indexes in the same directory.
- `create (bool)`: If True, create the index even if it already exists (clears existing).

**Returns:**
- `FileIndex`: A new index object.

**Example:**
```python
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT

schema = Schema(title=TEXT(stored=True), content=TEXT)
index = create_in("indexdir", schema)
```

---

### open_dir

```python
whoosh.index.open_dir(
    dirname: str,
    indexname: str = "MAIN",
    readonly: bool = False,
    **kwargs
) -> FileIndex
```

Open an existing index.

**Args:**
- `dirname (str)`: Path to the index directory.
- `indexname (str)`: Name of the index to open.
- `readonly (bool)`: If True, open in read-only mode.

**Returns:**
- `FileIndex`: An index object.

**Example:**
```python
from whoosh.index import open_dir
index = open_dir("indexdir")
```

---

### exists_in

```python
whoosh.index.exists_in(
    dirname: str,
    indexname: str = "MAIN",
    **kwargs
) -> bool
```

Check if a valid index exists in the given directory.

**Returns:**
- `bool`: True if the index exists.

---

### create_index

```python
whoosh.index.create_index(
    schema: Schema,
    storage: Storage,
    indexname: str = "MAIN",
    create: bool = True,
    **kwargs
) -> Index
```

Low-level index creation. Use `create_in` instead unless you need custom storage.

---

### open_index

```python
whoosh.index.open_index(
    storage: Storage,
    indexname: str = "MAIN",
    readonly: bool = False,
    **kwargs
) -> Index
```

Low-level index opening. Use `open_dir` instead unless you need custom storage.

## Classes

### Index (Base Class)

```python
class whoosh.index.Index
```

Abstract base class for index objects. Provides common methods for reading and writing.

**Methods:**

#### `writer()`

```python
writer = ix.writer(
    timeout: float = 0.0,
    delay: float = 0.1,
    limitmb: int = 128,
    **kwargs
) -> IndexWriter
```

Return a writer for this index.

**Args:**
- `timeout (float)`: Max seconds to wait for write lock.
- `delay (float)`: Seconds between lock retries.
- `limitmb (int)`: Maximum size of posting pool runs.

**Returns:**
- `IndexWriter`: A writer object.

**Example:**
```python
writer = ix.writer()
writer.add_document(title="Hello", content="World")
writer.commit()
```

---

#### `searcher()`

```python
searcher = ix.searcher(
    weighting: WeightingModel = None,
    **kwargs
) -> Searcher
```

Return a searcher for the current index state.

**Returns:**
- `Searcher`: A searcher object.

**Example:**
```python
with ix.searcher() as searcher:
    results = searcher.search("query")
```

---

#### `reader()`

```python
reader = ix.reader() -> IndexReader
```

Return a reader for the current index state.

---

#### `commit()`

```python
ix.commit(mergetype=None, optimize=None, merge=None)
```

Convenience method: create a writer, call commit, and close.

---

#### `optimize()`

```python
ix.optimize()
```

Merge all segments into a single segment.

---

#### `add_field()`

```python
ix.add_field(fieldname: str, fieldtype, **kwargs)
```

Add a field to the index schema.

---

#### `remove_field()`

```python
ix.remove_field(fieldname: str, **kwargs)
```

Remove a field from the index schema.

---

#### `doc_count()`

```python
count = ix.doc_count() -> int
```

Return the number of documents in the index.

---

#### `doc_count_all()`

```python
count = ix.doc_count_all() -> int
```

Return the total number of documents (including deleted).

---

#### `lock()`

```python
lock = ix.lock(name: str) -> Lock
```

Acquire a named lock on the index.

## FileIndex

The concrete implementation returned by `create_in` and `open_dir`.

All `Index` methods are available. Additional methods:

### `_read_toc()`

Read the table of contents.

### `_write_toc()`

Write the table of contents.

## Exceptions

### LockError

Raised when the index is locked by another writer.

```python
from whoosh.index import LockError

try:
    writer = ix.writer(timeout=5.0)
except LockError:
    print("Index is locked, try again later")
```

### IndexMissingError

Raised when trying to open a non-existent index.

## Constants

### IndexVersion

Current index format version.

---

# Index API

## Index

```python
class whoosh.index.Index
```

Base index class providing reading and writing access.

### Methods

- `writer(**kwargs)` -> `IndexWriter`
- `searcher(**kwargs)` -> `Searcher`
- `reader()` -> `IndexReader`
- `commit(mergetype=None, optimize=None, merge=None)`
- `optimize()`
- `add_field(fieldname, fieldtype, **kwargs)`
- `remove_field(fieldname, **kwargs)`
- `doc_count() -> int`
- `doc_count_all() -> int`
- `lock(name) -> Lock`

## IndexingError

```python
class whoosh.writing.IndexingError(Exception)
```

Raised when an indexing operation fails.

## Exceptions

```python
class whoosh.index.LockError(Exception)
class whoosh.index.IndexMissingError(Exception)
```
