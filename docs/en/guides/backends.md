---
title: "Backends"
nav_order: 28
parent: "Guides"
---

# Backends

Whoosh-NG supports pluggable storage backends through the Provider Architecture. The default backend stores data as files on disk, but you can use SQLite, PostgreSQL, S3, and more.

## Built-in Backends

| Backend | Class | Description |
|---------|-------|-------------|
| File (default) | `FileBackend` | Stores index as files on disk |
| SQLite | `SQLiteBackend` | Stores index in SQLite database |
| Memory | `MemoryBackend` | In-memory backend (testing only) |

## File Backend (Default)

```python
from whoosh.index import create_in

# Uses FileBackend by default
ix = create_in("indexdir", schema)
```

### Configuration

```python
from whoosh.backends.file import FileBackend

backend = FileBackend(
    storage=FileStorage("indexdir"),
    compound=True  # Use compound files
)
```

## SQLite Backend

```python
from whoosh.backends.sqlite import SQLiteBackend
from whoosh.store.sqlite import SQLiteStorage

storage = SQLiteStorage("index.db")
backend = SQLiteBackend(storage=storage)
```

### Advantages

- Single file index
- Better for transactional workloads
- Easier backups
- Supports concurrent reads

### Disadvantages

- Slower for large indexes
- Limited by SQLite performance

## Memory Backend

```python
from whoosh.backends.memory import MemoryBackend

backend = MemoryBackend()
# Useful for testing
```

## Custom Backend

Create a custom backend by subclassing `Backend`:

```python
from whoosh.backends.abc import Backend

class MyBackend(Backend):
    def create(self):
        """Create a new segment."""
        pass

    def open(self):
        """Open existing segment."""
        pass

    def close(self):
        """Close the backend."""
        pass

    def commit(self):
        """Commit changes."""
        pass
```

## Registering a Backend

```python
from whoosh.registry import BackendRegistry

BackendRegistry.register("my_backend", MyBackend, "my_package")
```

## Backend Selection

Choose a backend based on your use case:

| Use Case | Recommended Backend |
|----------|---------------------|
| Small to medium indexes | File (default) |
| Single-file deployment | SQLite |
| Testing | Memory |
| Distributed systems | Object storage (S3, MinIO) |
| High concurrency | SQLite or custom |

## Best Practices

1. **File backend for production**: Most battle-tested
2. **SQLite for single-file**: Easier deployment
3. **Memory for tests**: Fast, no cleanup needed
4. **Compound files**: Enable for reduced file count
5. **Backup strategy**: File backend = copy directory; SQLite = copy file