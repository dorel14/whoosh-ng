---
title: "Idsets API"
nav_order: 210
---

# Idsets API

Specialized set implementations for storing sorted lists of positive
integers (document IDs). These are more memory-efficient than the built-in
`set` for certain use cases, though they are slower for most operations since
they are pure Python.

## Overview

The `DocIdSet` class is the abstract base class. Concrete implementations
include `BitSet`, `OnDiskBitSet`, `SortedIntSet`, `RoaringIdSet`, and
`MultiIdSet`. The `AutoIdSet` function selects the best implementation
based on the contents.

## Module Functions

### `autoset`

```python
whoosh.idsets.autoset
```

A factory that creates an appropriate `DocIdSet` subclass based on the
contents of a given iterable. If all integers in the set are below 10,000,
returns a `BitSet`; otherwise returns a `SortedIntSet`.

## `DocIdSet`

```python
class whoosh.idsets.DocIdSet
```

Abstract base class for set implementations specialized toward storing sorted
lists of positive integers.

**Inheritance:** Inherits from `set`-like interface.

**Methods:**
- `__eq__(other)`: Compares two `DocIdSet` instances by iterating.
- `__len__()`: Returns the number of elements. Override in subclasses.
- `__iter__()`: Yields elements in sorted order. Override in subclasses.
- `__contains__(i)`: Returns `True` if `i` is in the set.
- `__or__(other)`: Returns `self.union(other)`.
- `__and__(other)`: Returns `self.intersection(other)`.
- `__sub__(other)`: Returns `self.difference(other)`.
- `copy()`: Returns a copy of this set.
- `add(n)`: Adds `n` to the set.
- `discard(n)`: Removes `n` from the set (no error if absent).
- `update(other)`: Adds all elements from `other`.
- `intersection_update(other)`: Removes elements not in `other`.
- `difference_update(other)`: Removes all elements in `other`.
- `invert_update(size)`: In-place inversion over the range `[0, size)`.
- `intersection(other)`: Returns a new set with elements in both.
- `union(other)`: Returns a new set with elements from both.
- `difference(other)`: Returns a new set with elements in self but not other.
- `invert(size)`: Returns a new set that is the inversion over `[0, size)`.
- `isdisjoint(other)`: Returns `True` if no elements are shared.
- `before(i)`: Returns the previous integer in the set before `i`, or `None`.
- `after(i)`: Returns the next integer in the set after `i`, or `None`.
- `first()`: Returns the first (lowest) integer.
- `last()`: Returns the last (highest) integer.

## `BaseBitSet`

```python
class whoosh.idsets.BaseBitSet(DocIdSet)
```

Base class for bitmap-backed `DocIdSet` implementations. Uses a bytes-based
bitmap where each bit represents membership of an integer.

**Abstract Methods to Override:**
- `byte_count()`: Returns the number of bytes in the bitmap.
- `_get_byte(i)`: Returns the byte at index `i`.
- `_iter_bytes()`: Yields all bytes in the bitmap.

**Inherited Methods:** All `DocIdSet` methods with efficient bitmap
implementations of `__len__`, `__iter__`, `__contains__`, `first`, and
`last`.

## `OnDiskBitSet`

```python
class whoosh.idsets.OnDiskBitSet(file, doc_count)
```

A `BaseBitSet` that reads the bitmap from a file on disk, using `mmap` for
memory efficiency.

**Constructor:**
- `file`: A file-like object (opened in binary mode) containing the bitmap.
- `doc_count`: Total number of documents (bits) represented.

```python
from whoosh.idsets import OnDiskBitSet

with open("deletions.dat", "rb") as f:
    bs = OnDiskBitSet(f, doc_count=10000)
    if 42 in bs:
        print("Document 42 is deleted")
```

## `BitSet`

```python
class whoosh.idsets.BitSet
```

A `BaseBitSet` that stores the bitmap in memory as a `bytearray`. Fast for
membership tests and set operations on small ranges of integers.

**Constructor:**
- Optional initial iterable of integers.

```python
from whoosh.idsets import BitSet

bs = BitSet([0, 5, 10, 15])
print(5 in bs)  # True
print(bs.first())  # 0
print(len(bs))   # 4
```

**Methods:**
- `from_blob(data)`: Create a `BitSet` from raw bytes.
- `tostring()`: Returns the bitmap as a `bytes` string.
- `set_reverse()`: Prepares the set for reverse iteration.

## `SortedIntSet`

```python
class whoosh.idsets.SortedIntSet
```

A `DocIdSet` that stores integers as a sorted list of Python `int` objects.
More memory-efficient than `BitSet` for sparse sets but slower for membership
tests.

**Constructor:**
- Optional initial iterable of integers.

```python
from whoosh.idsets import SortedIntSet

sis = SortedIntSet([100, 500, 999])
print(500 in sis)  # True
print(sis.after(200))  # 500
```

## `ReverseIdSet`

```python
class whoosh.idsets.ReverseIdSet(child)
```

Wraps another `DocIdSet` to reverse the interpretation of integers. Instead
of representing membership directly, the set represents the *complement* of
the inner set. Useful for representing deleted documents.

**Constructor:**
- `child`: The `DocIdSet` to reverse.

**Example:** If `child` represents documents `{3, 7, 9}`, then
`ReverseIdSet(child)` represents all documents *except* `{3, 7, 9}`.

## `RoaringIdSet`

```python
class whoosh.idsets.RoaringIdSet
```

A `DocIdSet` that partitions integers into 16-bit buckets and uses `BitSet`
within each bucket. More memory-efficient than a single flat `BitSet` for
large, sparse sets of integers.

**Constructor:**
- Optional initial iterable of integers.

**Methods:**
- `from_bytes(data)`: Deserialize from bytes.
- `to_bytes()`: Serialize to bytes.
- `to_bytes_list()`: Returns a list of `(bucket, bytes)` pairs.

## `MultiIdSet`

```python
class whoosh.idsets.MultiIdSet(readers, offsets=None)
```

Combines multiple `DocIdSet` instances into one, handling document ID offsets
automatically. Used for combining deletions across multiple segments.

**Constructor:**
- `readers`: List of `DocIdSet` instances (one per segment).
- `offsets`: Optional list of base docnum offsets for each reader. If
  omitted, offsets are computed automatically.

**Methods:**
- `__contains__(i)`: Checks the appropriate sub-set based on offsets.
- `__iter__()`: Iterates over all integers in all sub-sets.
- `__len__()`: Returns the total count across all sub-sets.
