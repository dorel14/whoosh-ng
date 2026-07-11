---
title: "Indexing"
nav_order: 23
parent: "Guides"
---

# Indexing

This guide covers adding, updating, and deleting documents in your Whoosh-NG index.

## Opening a Writer

```python
from whoosh import index

ix = index.open_dir("indexdir")

# Basic writer
writer = ix.writer()

# Writer with custom options
writer = ix.writer(
    timeout=10.0,      # Lock acquisition timeout (seconds)
    delay=0.1,         # Delay between lock retries (seconds)
    limitmb=128,       # Posting pool run size (MiB)
    compound=True      # Use compound files
)
```

## Adding Documents

```python
with ix.writer() as writer:
    writer.add_document(
        title="First document",
        content="Hello world",
        path="/doc1",
        tags=["python", "search"]
    )
    writer.add_document(
        title="Second document",
        content="Goodbye world",
        path="/doc2",
        tags=["python", "tutorial"]
    )
    # commit() is called automatically on exit
```

### Multi-value Fields

Pass lists to add multiple values for multi-valued fields:

```python
writer.add_document(
    title="Document with multiple tags",
    content="Content here",
    tags=["python", "whoosh", "search", "tutorial"]
)
```

### Stored vs Indexed Values

For fields that are both indexed and stored, you can store a different value:

```python
writer.add_document(
    title="Title to be indexed",
    _stored_title="Display title to show in results"
)
```

### Field Boosts

Boost individual fields at document level:

```python
writer.add_document(
    title="Important title",
    _title_boost=2.0,   # Double weight for title terms
    content="Body content"
)
```

## Updating Documents

Use `update_document` to replace documents with matching unique fields:

```python
schema = Schema(path=ID(unique=True, stored=True), content=TEXT)
ix = index.create_in("indexdir", schema)

with ix.writer() as writer:
    writer.add_document(path="/doc1", content="Original content")
    writer.commit()

with ix.writer() as writer:
    # Replaces any document with path="/doc1"
    writer.update_document(path="/doc1", content="Updated content")
    writer.commit()
```

## Deleting Documents

```python
# Delete by document number
writer.delete_document(docnum=42)

# Delete by term in a field
writer.delete_by_term("path", "/doc1")

# Delete by query
from whoosh.query import Term
q = Term("tags", "deprecated")
writer.delete_by_query(q)

writer.commit()
```

## Commit and Merge Policies

### Basic Commit

```python
writer.commit()
```

### Optimize (Merge All)

```python
writer.commit(optimize=True)
```

### No Merge

```python
writer.commit(merge=False)
```

### Custom Merge Policy

```python
from whoosh.writing import NO_MERGE, MERGE_SMALL, OPTIMIZE

writer.commit(mergetype=NO_MERGE)
writer.commit(mergetype=MERGE_SMALL)
writer.commit(mergetype=OPTIMIZE)

# Custom function
def my_merge(writer, segments):
    # Custom merge logic
    return segments

writer.commit(mergetype=my_merge)
```

## BufferedWriter

For high-throughput scenarios where documents arrive one at a time:

```python
from whoosh.writing import BufferedWriter

# Buffers documents and commits periodically
buffered = BufferedWriter(
    ix,
    period=60,    # Max seconds between commits
    limit=100,    # Max documents per commit
    writerargs={} # Extra args for underlying writer
)

with buffered:
    buffered.add_document(title="Doc 1", content="Content")
    buffered.add_document(title="Doc 2", content="More")
# commit() called automatically on close
```

## AsyncWriter

For web applications where multiple processes may write:

```python
from whoosh.writing import AsyncWriter

# Automatically retries on lock contention
async_writer = AsyncWriter(ix, delay=0.25)

async_writer.add_document(title="Async doc", content="Content")
async_writer.commit()
```

## Middleware Integration

```python
from whoosh.middleware import MiddlewareChain, MetricsMiddleware, CacheMiddleware
from whoosh.middleware.integration import apply_middleware_to_writer

chain = MiddlewareChain([
    MetricsMiddleware(),
    CacheMiddleware()
])

with apply_middleware_to_writer(ix.writer(), chain.middlewares) as writer:
    writer.add_document(title="Tracked", content="Content")
```

## Best Practices

1. **Use context managers**: `with ix.writer() as w:` ensures proper cleanup
2. **Batch commits**: Group many documents per commit for better performance
3. **Choose merge policy wisely**: `MERGE_SMALL` is usually fine; use `NO_MERGE` for bulk loads followed by `OPTIMIZE`
4. **Handle locks**: Use `BufferedWriter` or `AsyncWriter` in multi-process environments
5. **Don't forget to close**: Always call `commit()` or `cancel()` to release the write lock
