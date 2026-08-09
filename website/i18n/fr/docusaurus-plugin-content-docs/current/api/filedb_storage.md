---
title: 'File DB / Storage API'
sidebar_position: 0
---

> **Note de traduction** : Cette page n'est pas encore traduite en français.
> Le contenu anglais est affiché ci-dessous en attendant la traduction.

<!-- Creez une version francaise de ce fichier et supprimez ce message. -->


# File DB / Storage API

Classes for storing and retrieving index data on disk or in memory. The
`Storage` class is the main entry point for persisting an index.

## Storage Classes

### `Storage`

```python
class whoosh.filedb.filestore.Storage(path=None)
```

Abstract base class for storage backends. A `Storage` manages a filesystem-
or memory-based location where index files can be created, read, and
manipulated.

**Constructor:**
- `path`: Optional path string. Subclasses may use this to set the storage
  location.

**Methods:**

#### `create_file(name, **kwargs)`

Creates and returns a file object for writing.

#### `open_file(name, **kwargs)`

Opens and returns a file object for reading.

#### `list()`

Returns a list of all filenames in this storage.

#### `exists(name)`

Returns `True` if a file/named item exists in the storage.

#### `file_exists(name)`

Alias for `exists()`.

#### `file_length(name)`

Returns the length of file `name` in bytes.

#### `rename(src, dst)`

Renames a file from `src` to `dst`.

#### `delete_file(name)`

Deletes file `name` from storage.

#### `destroy()`

Deletes all files and the storage itself.

#### `temp_storage()`

Creates and returns a temporary isolated `Storage` for scratch space.

#### `supports_mmap`

Returns `True` if this storage supports memory-mapped file access.

**Properties:**
- `schema`: The `Schema` for this storage (if it holds an index).
- `lock`: The lock object used for this storage.

### `FileStorage`

```python
class whoosh.filedb.filestore.FileStorage(
    path,
    cachesize_limit=40,
    supports_mmap=None,
    **kwargs
)
```

A `Storage` subclass that uses the operating system's filesystem.

**Constructor:**
- `path`: A `Path` (or string path) to the directory where files are stored.
- `cachesize_limit`: Maximum number of open file handles to cache.
- `supports_mmap`: If `None`, auto-detected; otherwise force enable/disable.

**Methods:** All `Storage` methods plus:
- `create_index(schema, indexname="index", ...)`: Creates and returns a new
  `Index` object.
- `open_index(indexname="index", ...)`: Opens an existing `Index`.
- `lock(name)`: Returns a lock object for the given lock name.

### `RamStorage`

```python
class whoosh.filedb.filestore.RamStorage(cachesize_limit=10)
```

A `Storage` subclass that keeps all files in memory as bytes. Useful for
testing and small indexes.

**Constructor:**
- `cachesize_limit`: Maximum number of files to cache as decoded objects.

**Methods:** All `Storage` methods plus:
- `create_index(schema, ...)`: Creates an in-memory `Index`.
- `save_to_file(filename, ...)`: Saves the entire storage to a file.
- `load_from_file(filename, ...)`: Loads storage contents from a file.

### `OverlayStorage`

```python
class whoosh.filedb.filestore.OverlayStorage(base, overlay)
```

A `Storage` wrapper that presents two storage layers: a base and an overlay.
Files in the overlay take precedence over the base.

**Constructor:**
- `base`: The base `Storage` (e.g., read-only original).
- `overlay`: The overlay `Storage` (e.g., writable copy).

## Storage Exceptions

### `StorageError`

```python
class whoosh.filedb.filestore.StorageError
```

Base exception for storage-related errors.

### `ReadOnlyError`

```python
class whoosh.filedb.filestore.ReadOnlyError(StorageError)
```

Raised when attempting to write to a read-only storage.

## File Tables

### `HashWriter`

```python
class whoosh.filedb.filetables.HashWriter(dbfile, keycoder=None, keydecoder=None, data_encoder=None, data_decoder=None, **kwargs)
```

Writes key-value pairs to a file, with optional indexing by key.

**Constructor:**
- `dbfile`: The `StructFile` to write to.
- `keycoder`: Function to encode keys for storage.
- `keydecoder`: Function to decode keys from storage.
- `data_encoder`: Function to encode values.
- `data_decoder`: Function to decode values.

### `HashReader`

```python
class whoosh.filedb.filetables.HashReader(dbfile, length, keycoder=None, keydecoder=None, data_decoder=None, **kwargs)
```

Reads key-value pairs from a file written by `HashWriter`.

**Constructor:**
- `dbfile`: The `StructFile` to read from.
- `length`: Length of the data section.
- `keycoder`/`keydecoder`/`data_decoder`: Same as `HashWriter`.

**Methods:**
- `__getitem__(key)`: Returns the value for `key`.
- `keys()`: Yields all keys.
- `values()`: Yields all values.
- `items()`: Yields `(key, value)` pairs.
- `keys_from(prefixbytes)`: Yields keys starting at `prefixbytes`.
- `items_from(prefixbytes)`: Yields `(key, value)` pairs starting at prefix.
- `closest_key_pos(key)`: Returns the position of the closest matching key.
- `range_for_key(key)`: Returns `(startpos, endpos)` for a key range.

### `OrderedHashWriter`

```python
class whoosh.filedb.filetables.OrderedHashWriter(HashWriter)
```

A `HashWriter` that maintains keys in sorted order.

### `OrderedHashReader`

```python
class whoosh.filedb.filetables.OrderedHashReader(HashReader)`

A `HashReader` for reading data written by `OrderedHashWriter`. Preserves
key ordering for efficient prefix iteration.

### `FieldedOrderedHashWriter`

```python
class whoosh.filedb.filetables.FieldedOrderedHashWriter(HashWriter)
```

An `OrderedHashWriter` that stores an extra "fieldmap" in the extras dict,
mapping field names to numeric IDs.

### `FieldedOrderedHashReader`

```python
class whoosh.filedb.filetables.FieldedOrderedHashReader(HashReader)
```

Reader for data written by `FieldedOrderedHashWriter`.

## Struct File

### `StructFile`

```python
class whoosh.filedb.structfile.StructFile(name, source, cachesize_limit=40)
```

Wraps a file object and adds methods for reading/writing packed binary
values, arrays, varints, and pickle objects.

**Methods include:**
- `read_int()`, `write_int(n)`: Read/write a 4-byte signed integer.
- `read_long()`, `write_long(n)`: Read/write a 8-byte signed integer.
- `read_uint()`, `write_uint(n)`: Read/write unsigned int.
- `read_ulong()`, `write_ulong(n)`: Read/write unsigned long.
- `read_float()`, `write_float(n)`: Read/write a float.
- `read_ushort()`, `write_ushort(n)`: Read/write unsigned short.
- `read_byte()`, `write_byte(b)`: Read/write a single byte.
- `write_array(arr)`: Write an array of values.
- `get_array(offset, typecode, length)`: Read an array from offset.
- `write_pickle(obj)`: Pickle and write an object.
- `read_pickle()`: Read and unpickle an object.
- `get(offset, length)`: Read `length` bytes from `offset`.
- `get_int()`, `get_uint()`, `get_long()`, `get_float()`, `get_byte()`:
  Read a single value from the given offset.

### `BufferFile`

```python
class whoosh.filedb.structfile.BufferFile
```

A `StructFile` that wraps an in-memory byte buffer.

### `ChecksumFile`

```python
class whoosh.filedb.structfile.ChecksumFile(dbfile)
```

A `StructFile` wrapper that computes a checksum as data is written, for
integrity verification.

## Compound Storage

### `CompoundStorage`

```python
class whoosh.filedb.compound.CompoundStorage(dbfile, use_mmap=True)
```

Treats a single file as a container for multiple sub-files. Used for compound
segment files.

**Methods:**
- `create_file(name)`: Create a sub-file within the compound file.
- `open_file(name)`: Open a sub-file for reading.
- `list()`: List all sub-file names.
- `close()`: Close the compound storage.

### `SubFile`

```python
class whoosh.filedb.compound.SubFile
```

A file-like object representing a sub-file within a `CompoundStorage`.

### `CompoundWriter`

```python
class whoosh.filedb.compound.CompoundWriter(storage)
```

Writes a compound file by assembling multiple files from a storage.

**Methods:**
- `create_file(name)`: Reserve a filename in the compound file.
- `save_as_files(dest_storage, fn_generator)`: Assemble the compound file
  from source files into the destination storage.

## Storage Utility Functions

### `copy_storage`

```python
whoosh.filedb.filestore.copy_storage(sourcestore, deststore)
```

Copies all files from one storage to another.

### `copy_to_ram`

```python
whoosh.filedb.filestore.copy_to_ram(storage)
```

Reads all files from a storage into a `RamStorage` and returns it.
