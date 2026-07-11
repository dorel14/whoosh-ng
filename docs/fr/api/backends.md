---
title: "API Backends"
nav_order: 9
parent: "Référence API"
lang: fr
---

# API Backends

Architecture de stockage pliable via backends.

## FileBackend (défaut)

```python
class whoosh.backends.file.FileBackend
```

Backend par défaut stockant les segments comme fichiers sur disque.

### Options

| Paramètre | Description |
|-----------|-------------|
| `storage` | Instance de storage (FileStorage par défaut) |
| `limitmb` | Taille maximum des segments (MiB) |

**Exemple:**
```python
from whoosh import index

ix = index.create_in("indexdir", schema)
# Utilise FileBackend implicitement
```

## SQLiteBackend

```python
class whoosh.backends.sqlite.SQLiteBackend
```

Stocke l'index entier dans une base de données SQLite.

### Options

| Paramètre | Description |
|-----------|-------------|
| `storage` | `SQLiteStorage(path)` |
| `writethrough` | Écriture synchrone |

**Exemple:**
```python
from whoosh.backends.sqlite import SQLiteStorage, SQLiteBackend

storage = SQLiteStorage("mon_index.db")
backend = SQLiteBackend(storage=storage)

ix = backend.create_index(schema)
```

## MemoryBackend

```python
class whoosh.backends.memory.MemoryBackend
```

Backend en mémoire (tests uniquement, données perdues au redémarrage).

## Classes Storage

### FileStorage

```python
class whoosh.store.FileStorage
```

Gère les fichiers sur disque.

### SQLiteStorage

```python
class whoosh.store.SQLiteStorage(db_path)
```

Gère le stockage SQLite.

## ProviderRegistry

```python
class whoosh.registry.ProviderRegistry
```

Registre pour les providers de stockage:

```python
from whoosh.registry import ProviderRegistry

ProviderRegistry.register("sqlite", SQLiteBackend(), "mon_app")
```
