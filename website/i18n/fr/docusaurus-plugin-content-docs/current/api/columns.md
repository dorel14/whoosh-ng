---
title: 'Columns API'
sidebar_position: 0
---

> **Note de traduction** : Cette page n'est pas encore traduite en français.
> Le contenu anglais est affiché ci-dessous en attendant la traduction.

<!-- Creez une version francaise de ce fichier et supprimez ce message. -->


# Columns API

Classes for storing per-document values (column-oriented storage) used for
fast sorting, faceting, and filtering. Columns are the mechanism by which
Whoosh stores field values alongside the inverted index, in a column-oriented
layout for efficient range access.

The default column type for most fields is `VarBytesColumn`, although numeric
and date fields use `NumericColumn`. Expert users may use other column types
that may be faster or more storage-efficient based on the field contents.

A `Column` object stores configuration information and provides two important
methods: `writer()` to return a `ColumnWriter` and `reader()` to return a
`ColumnReader`.

## Module Functions

### `bytes_column`

```python
whoosh.columns.bytes_column
```

A default `VarBytesColumn` instance used as the column type for string fields.

### `numeric_column`

```python
whoosh.columns.numeric_column
```

A default `NumericColumn` instance used as the column type for numeric fields.

## Base Classes

### `Column`

```python
class whoosh.columns.Column
```

Base class for all column types.

**Class Attributes:**
- `reversible (bool)`: Whether values can be reversed for descending sort.
  Default `False`.

**Methods:**
- `writer(dbfile)`: Returns a `ColumnWriter` for this column type.
- `reader(dbfile, basepos, length, doccount)`: Returns a `ColumnReader` for
  this column type.
- `default_value(reverse=False)`: Returns the default value for documents
  without a column value at index time.
- `stores_lists()`: Returns `True` if the column stores a list of values per
  document instead of a single value.

### `ColumnWriter`

```python
class whoosh.columns.ColumnWriter(dbfile)
```

Base class for writing column values to disk.

**Constructor:**
- `dbfile`: The `StructFile` to write to.

**Methods:**
- `fill(docnum)`: Fills any gap in docnums up to `docnum` with default values.
- `add(docnum, value)`: Adds a value for the given docnum.
- `finish(docnum)`: Called when done writing. Default does nothing.

### `ColumnReader`

```python
class whoosh.columns.ColumnReader(dbfile, basepos, length, doccount)
```

Base class for reading column values from disk.

**Constructor:**
- `dbfile`: The `StructFile` to read from.
- `basepos`: The offset within the file at which the column starts.
- `length`: The length in bytes the column occupies in the file.
- `doccount`: The number of rows (documents) in the column.

**Methods:**
- `__getitem__(docnum)`: Returns the value for the given docnum.
- `sort_key(docnum)`: Returns the value for sorting (defaults to
  `__getitem__`).
- `__iter__()`: Yields values for all documents.
- `load()`: Returns a list of all values.
- `set_reverse()`: Prepares the reader for reverse iteration.

## Concrete Column Types

### `VarBytesColumn`

```python
class whoosh.columns.VarBytesColumn(
    allow_offsets=True,
    write_offsets_cutoff=2**15
)
```

Stores variable-length byte strings. The default value for documents without
a value is `b''` (empty bytes).

**Constructor:**
- `allow_offsets`: Whether to write offsets for faster lookup when there are
  many rows. Default `True`.
- `write_offsets_cutoff`: Write offsets when there are more than this many
  rows (default `2**15`).

### `FixedBytesColumn`

```python
class whoosh.columns.FixedBytesColumn(blocksize, default=emptybytes)
```

Stores fixed-length byte strings, saving space by not storing the length of
each value.

**Constructor:**
- `blocksize`: Fixed size of each value in bytes.
- `default`: Default value for documents without a value.

### `RefBytesColumn`

```python
class whoosh.columns.RefBytesColumn(
    cachesize=1000,
    stable=True,
    default=emptybytes
)
```

Stores references to unique values rather than the values themselves, saving
space when the field has few unique values. Uses a `DocIdSet` to track which
documents contain each value.

**Constructor:**
- `cachesize`: Size of the LRU cache for value lookups (default `1000`).
- `stable`: Whether to use a stable sort of references (default `True`).
- `default`: Default value for missing documents.

### `NumericColumn`

```python
class whoosh.columns.NumericColumn(
    typecode,
    default=None,
    nullable=False
)
```

Stores numbers (int, float, datetime) encoded as binary values. Extends
`FixedBytesColumn`.

**Constructor:**
- `typecode`: A `struct` typecode string (e.g., `"I"` for unsigned int,
  `"q"` for long, `"d"` for float).
- `default`: Default numeric value (None for the type's zero value).
- `nullable`: Whether `None` values are allowed.

### `BitColumn`

```python
class whoosh.columns.BitColumn
```

Stores boolean values as a bitmap. Each value is either `True` (1) or
`False` (0). Uses a `BitSet` internally.

### `CompressedBytesColumn`

```python
class whoosh.columns.CompressedBytesColumn(default=emptybytes)
```

Wraps a `VarBytesColumn` with zlib compression for the value bytes.

### `CompressedBlockColumn`

```python
class whoosh.columns.CompressedBlockColumn
```

Stores values with block-level zlib compression. More efficient for large
columns.

### `StructColumn`

```python
class whoosh.columns.StructColumn(struct, name)
```

Wraps a `FixedBytesColumn` to store structured binary data (e.g., tuples
encoded with `struct`).

**Constructor:**
- `struct`: A `struct.Struct` object defining the format.
- `name`: Field name for error messages.

### `EmptyColumnReader`

```python
class whoosh.columns.EmptyColumnReader(default, doccount)
```

A `ColumnReader` that returns a constant default value for every document.
Used when a field has no column.

### `MultiColumnReader`

```python
class whoosh.columns.MultiColumnReader(readers)
```

Combines multiple `ColumnReader` instances into one for multi-segment indices.

**Constructor:**
- `readers`: List of `ColumnReader` instances (one per segment).

### `TranslatingColumnReader`

```python
class whoosh.columns.TranslatingColumnReader(child, translator)
```

Wraps a `ColumnReader` to apply a translation function to the values.

**Constructor:**
- `child`: The underlying `ColumnReader`.
- `translator`: Function that maps sort keys to human-readable values.

### `WrappedColumn`

```python
class whoosh.columns.WrappedColumn(child)
```

Base class for column wrappers that adapt another column type.

### `WrappedColumnWriter`

```python
class whoosh.columns.WrappedColumnWriter(child)
```

Base class for column writer wrappers.

### `WrappedColumnReader`

```python
class whoosh.columns.WrappedColumnReader(child)
```

Base class for column reader wrappers.

### `ClampedNumericColumn`

```python
class whoosh.columns.ClampedNumericColumn(child, clampfn)
```

Wraps a `NumericColumn` to clamp values to a valid range before sorting.

**Constructor:**
- `child`: The wrapped `NumericColumn`.
- `clampfn`: Function that clamps a value to the valid range.

### `PickleColumn`

```python
class whoosh.columns.PickleColumn(child, ...)
```

Wraps another column to store pickled Python objects.

### `ListColumn`

```python
class whoosh.columns.ListColumn(child)
```

Base class for columns that store multiple values per document.

### `ListColumnReader`

```python
class whoosh.columns.ListColumnReader(child)
```

Reader for list-valued columns.

### `VarBytesListColumn`

```python
class whoosh.columns.VarBytesListColumn
```

A `ListColumn` variant of `VarBytesColumn` that stores lists of byte strings.

### `FixedBytesListColumn`

```python
class whoosh.columns.FixedBytesListColumn(blocksize)
```

A `ListColumn` variant of `FixedBytesColumn` that stores lists of fixed-size
byte strings.

