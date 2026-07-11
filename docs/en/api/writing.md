---
title: "Writing API"
nav_order: 3
parent: "API Reference"
---

# Writing API

Write, update, and delete documents using the `IndexWriter` interface.

## IndexWriter

```python
class whoosh.writing.IndexWriter
```

Base class for writing documents.

### Context Manager

```python
with ix.writer() as writer:
    writer.add_document(title="Hello", content="World")
    # commit() called automatically
```

### Methods

#### `add_document()`

```python
writer.add_document(**fields)
```

Add a document to the index.

**Special kwargs:**
- `_stored_<fieldname>`: Alternate stored value
- `_<fieldname>_boost`: Field-specific boost
- `_boost`: Document-wide boost

---

#### `update_document()`

```python
writer.update_document(**fields)
```

Update/replace a document. Uses `unique` fields to find existing documents.

---

#### `delete_document()`

```python
writer.delete_document(docnum: int, delete: bool = True)
```

Delete by document number.

---

#### `delete_by_term()`

```python
writer.delete_by_term(fieldname: str, text: str) -> int
```

Delete all documents with term in field.

**Returns:**
- `int`: Number of documents deleted.

---

#### `delete_by_query()`

```python
writer.delete_by_query(q: Query, searcher=None) -> int
```

Delete documents matching query.

---

#### `commit()`

```python
writer.commit(
    mergetype=None,
    optimize=False,
    merge=True
)
```

Commit changes to disk.

**Args:**
- `mergetype`: Custom merge function
- `optimize`: Merge all segments into one
- `merge`: If False, don't merge existing segments

---

#### `cancel()`

```python
writer.cancel()
```

Cancel pending changes and release lock.

---

#### `add_field()`

```python
writer.add_field(fieldname: str, fieldtype, **kwargs)
```

Add a field to schema (before adding documents).

---

#### `remove_field()`

```python
writer.remove_field(fieldname: str)
```

Remove a field from schema.

---

#### `searcher()`

```python
searcher = writer.searcher(**kwargs)
```

Return a searcher (for reading during write session).

---

#### `reader()`

```python
reader = writer.reader(**kwargs)
```

Return a reader for the current state.

---

#### `group()`

```python
with writer.group():
    writer.add_document(kind="class", name="MyClass")
    writer.add_document(kind="method", name="my_method")
```

Context manager for grouping documents into one segment.

## SegmentWriter

Concrete implementation of `IndexWriter`.

### Constructor

```python
SegmentWriter(
    ix,
    poolclass=None,
    timeout=0.0,
    delay=0.1,
    _lk=True,
    limitmb=128,
    docbase=0,
    codec=None,
    compound=True,
    **kwargs
)
```

## AsyncWriter

Threaded writer that automatically retries on lock contention.

```python
from whoosh.writing import AsyncWriter

writer = AsyncWriter(
    index,
    delay=0.25,
    writerargs={}
)
```

## BufferedWriter

Buffers documents in memory and commits periodically.

```python
from whoosh.writing import BufferedWriter

writer = BufferedWriter(
    index,
    period=60,       # Max seconds between commits
    limit=100,       # Max documents per commit
    writerargs={}    # Extra args for writer
)
```

The `BufferedWriter` also provides `reader()` and `searcher()` methods for quasi-real-time search.

## Merge Policies

```python
from whoosh.writing import NO_MERGE, MERGE_SMALL, OPTIMIZE, CLEAR

writer.commit(mergetype=NO_MERGE)     # No merging
writer.commit(mergetype=MERGE_SMALL) # Merge small segments
writer.commit(mergetype=OPTIMIZE)    # Merge all into one
writer.commit(mergetype=CLEAR)       # Delete all existing segments
```

## PostingPool

Internal pool for sorting postings. Typically not used directly.

```python
class whoosh.writing.PostingPool
```

## Exceptions

### IndexingError

```python
class whoosh.writing.IndexingError(Exception)
```

Raised when an indexing operation fails.
