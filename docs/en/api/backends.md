---
title: "Backends API"
nav_order: 9
parent: "API Reference"
---

# Backends API

Storage backend abstractions.

## Backend (ABC)

```python
class whoosh.backends.abc.Backend
```

Abstract base class for storage backends.

### Methods

#### `create()`

Create a new segment.

#### `open()`

Open an existing segment.

#### `close()`

Close the backend.

#### `commit()`

Commit changes.

#### `startup()`

Called on backend startup.

#### `shutdown()`

Called on backend shutdown.

---

## FileBackend

```python
class whoosh.backends.file.FileBackend
```

Default backend storing index as files.

```python
from whoosh.backends.file import FileBackend
from whoosh.store.filestore import FileStorage

storage = FileStorage("indexdir")
backend = FileBackend(storage=storage)
```

---

## SQLiteBackend

```python
class whoosh.backends.sqlite.SQLiteBackend
```

Stores index in SQLite database.

```python
from whoosh.backends.sqlite import SQLiteBackend
from whoosh.store.sqlite import SQLiteStorage

storage = SQLiteStorage("index.db")
backend = SQLiteBackend(storage=storage)
```

---

## MemoryBackend

```python
class whoosh.backends.memory.MemoryBackend
```

In-memory backend for testing.

```python
from whoosh.backends.memory import MemoryBackend

backend = MemoryBackend()
```

---

## BackendRegistry

```python
class whoosh.registry.BackendRegistry
```

Register backends:

```python
BackendRegistry.register("my_backend", MyBackendClass, "my_package")
backend = BackendRegistry.get("my_backend")
```
