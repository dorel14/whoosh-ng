---
title: "Sorting API"
nav_order: 140
---

# Sorting API

Classes and functions for faceting and sorting search results. The sorting
module is a refactored package exposing the same public API as the former
monolithic module.

## Overview

Sorting and faceting use `FacetType` objects to compute sort keys for documents.
A `FacetType` creates a `Categorizer` that computes a key for each document.
The key is used for sorting and grouping. `FacetMap` objects hold the
results of grouping documents by a facet.

## Facet Types

### `FacetType`

```python
class whoosh.sorting.FacetType
```

Base class for "facets" — aspects that can be sorted and/or faceted.

**Attributes:**
- `maptype`: Default `FacetMap` class to use for this facet.

**Methods:**

#### `categorizer(global_searcher)`

Returns a `Categorizer` corresponding to this facet.

- `global_searcher`: A parent searcher for global document ID references.

#### `map(default=None)`

Returns a `FacetMap` instance for holding facet results.

#### `default_name()`

Returns the default name for this facet (default `"facet"`).

### `Categorizer`

```python
class whoosh.sorting.Categorizer
```

Base class for objects that compute a key value for a document for sorting and
faceting. Created by `FacetType` objects via `categorizer()`.

**Attributes:**
- `allow_overlap (bool)`: If `True`, use `keys_for()` to allow overlapping
  groups. Default `False`.
- `needs_current (bool)`: If `True`, the categorizer needs the matcher to be
  in a valid state when `key_for()` is called. Default `False`.

**Methods:**

#### `set_searcher(segment_searcher, docoffset)`

Called when the collector moves to a new segment. Sets up segment-specific
data.

- `segment_searcher`: The atomic sub-searcher for the current segment.
- `docoffset`: Offset of the segment's docnums relative to the full index.

#### `key_for(matcher, segment_docnum)`

Returns a sort key for the current match.

- `matcher`: A `Matcher` object. If `needs_current` is `False`, do not use
  this object as it may be inconsistent.
- `segment_docnum`: Segment-relative document number.

#### `keys_for(matcher, segment_docnum)`

Yields multiple keys for the current match. Called instead of `key_for()`
when `allow_overlap` is `True`.

#### `key_to_name(key)`

Translates the sort key into a human-readable representation for facet
group names (e.g., converts an integer date sort key to a `datetime`).

### `FieldFacet`

```python
class whoosh.sorting.FieldFacet(
    fieldname,
    reverse=False,
    allow_overlap=False,
    maptype=None
)
```

Sorts/facets by the contents of a field.

**Constructor:**
- `fieldname`: Name of the field to sort/facet on.
- `reverse`: If `True`, reverse the sort order.
- `allow_overlap`: If `True`, allow documents to appear in multiple groups
  when they have multiple terms in the field.
- `maptype`: `FacetMap` class for holding results.

```python
paths = FieldFacet("path", reverse=True)
tags = FieldFacet("tag")
results = searcher.search(myquery, sortedby=paths, groupedby=tags)
```

### `ColumnCategorizer`

Categorizer that reads values from a column for sorting. Used when a field
has a column type.

### `ReversedColumnCategorizer`

Categorizer that reverses column values for fields that are not naturally
reversible.

### `OverlappingCategorizer`

```python
class whoosh.sorting.OverlappingCategorizer
```

Categorizer used when `allow_overlap=True`. A single document can belong to
multiple facet groups.

### `PostingCategorizer`

```python
class whoosh.sorting.PostingCategorizer
```

Categorizer for fields without column values. Builds an array caching the
order of all documents. Used as a fallback; prefer setting
`sortable=True` on fields.

### `QueryFacet`

```python
class whoosh.sorting.QueryFacet(
    querydict: dict,
    other=None,
    allow_overlap=False,
    maptype=None
)
```

Sorts/facets based on the results of a series of queries.

**Constructor:**
- `querydict`: Dictionary mapping keys to `Query` objects.
- `other`: Key to use for documents matching no queries.

### `RangeFacet`

```python
class whoosh.sorting.RangeFacet(
    fieldname,
    start,
    end,
    gap,
    hardend=False,
    maptype=None
)
```

Sorts/facets based on numeric ranges. Ranges are inclusive at the start and
exclusive at the end.

```python
prices = RangeFacet("price", 0, 1000, 100)
results = searcher.search(myquery, groupedby=prices)
```

- `fieldname`: The numeric field to facet on.
- `start`: Start of the entire range.
- `end`: End of the entire range.
- `gap`: Size of each bucket (can be a sequence for progressive gaps).
- `hardend`: If `True`, clamp the last bucket to `end`.

### `DateRangeFacet`

```python
class whoosh.sorting.DateRangeFacet(
    fieldname,
    startdate,
    enddate,
    gap,
    hardend=False,
    maptype=None
)
```

Sorts/facets based on date ranges. Extends `RangeFacet` but uses
`datetime` objects for start/end and `timedelta`/`relativedelta` for gaps.
Generates `DateRange` queries instead of `TermRange` queries.

```python
from datetime import datetime
from whoosh.support.relativedelta import relativedelta

startdate = datetime(1920, 1, 1)
enddate = datetime.now()
gap = relativedelta(years=5)
bdays = DateRangeFacet("birthday", startdate, enddate, gap)
```

### `ScoreFacet`

```python
class whoosh.sorting.ScoreFacet
```

Uses a document's relevance score as a sorting criterion.

```python
tag_score = MultiFacet(["tag", ScoreFacet()])
results = searcher.search(myquery, sortedby=tag_score)
```

### `FunctionFacet`

```python
class whoosh.sorting.FunctionFacet(fn)
```

Lets you pass an arbitrary function that computes the sort key. The function
is called with `(searcher, docid)` where `docid` is an absolute index
document number.

```python
fn = lambda s, docid: s.doc_field_length(docid, "content")
lengths = FunctionFacet(fn)
```

### `TranslateFacet`

```python
class whoosh.sorting.TranslateFacet(fn, *facets)
```

Applies a custom function to the key generated by one or more wrapped facets.
Useful for custom collation, such as Unicode Collation Algorithm (UCA) sorting.

```python
from pyuca import Collator

c = Collator("allkeys.txt")
facet = FieldFacet("name")
facet = TranslateFacet(c.sort_key, facet)
results = searcher.search(myquery, sortedby=facet)
```

**Constructor:**
- `fn`: Function applied to the computed key values.
- `*facets`: One or more `FacetType` objects whose keys are passed to `fn`.

### `StoredFieldFacet`

```python
class whoosh.sorting.StoredFieldFacet(
    fieldname,
    allow_overlap=False,
    split_fn=None,
    maptype=None
)
```

Sorts/groups using the value in an unindexed, stored field (e.g., `STORED`).
Usually slower than using an indexed field.

**Constructor:**
- `fieldname`: Name of the stored field.
- `allow_overlap`: If `True`, when grouping, allow documents to appear in
  multiple groups when they have multiple values (split by `split_fn` or
  `string.split()`).
- `split_fn`: Custom function to split a stored field value into multiple
  facet values (only used when `allow_overlap=True`).

### `MultiFacet`

```python
class whoosh.sorting.MultiFacet(items=None, maptype=None)
```

Sorts/facets by the combination of multiple sub-facets.

```python
facet = MultiFacet([FieldFacet("tag"), FieldFacet("path")])
results = searcher.search(myquery, sortedby=facet)
```

Strings in the items list are treated as field names:

```python
facet = MultiFacet(["tag", "path"])
```

**Methods:**
- `from_sortedby(sortedby)`: Class method that creates a `MultiFacet` from
  a field name, facet, or list thereof.
- `add_field(fieldname, reverse=False)`: Add a `FieldFacet`.
- `add_query(querydict, other=None, allow_overlap=False)`: Add a `QueryFacet`.
- `add_score()`: Add a `ScoreFacet`.
- `add_facet(facet)`: Add an arbitrary `FacetType`.

### `Facets`

```python
class whoosh.sorting.Facets(x=None)
```

Maps facet names to `FacetType` objects for creating multiple independent
groupings of documents.

```python
facets = Facets()
facets.add_field("tag")
facets.add_facet("price", RangeFacet("price", 0, 1000, 100))
results = searcher.search(myquery, groupedby=facets)

tag_groups = results.groups("tag")
price_groups = results.groups("price")
```

**Class Methods:**
- `from_groupedby(groupedby)`: Creates a `Facets` object from a field name,
  `FacetType`, dict, list, or another `Facets` object.

**Methods:**
- `names()`: Returns an iterator of facet names.
- `items()`: Returns a list of `(name, facet)` tuples.
- `add_field(fieldname, **kwargs)`: Adds a `FieldFacet`.
- `add_query(name, querydict, **kwargs)`: Adds a `QueryFacet`.
- `add_facet(name, facet)`: Adds a `FacetType` under the given name.
- `add_facets(facets, replace=True)`: Adds the contents of a `Facets` or
  `dict` to this object.

## Facet Maps

### `FacetMap`

```python
class whoosh.sorting.FacetMap
```

Base class for objects holding the results of grouping search results by a
facet. Use `as_dict()` to access results.

```python
myfacet = FieldFacet("size", maptype=OrderedList)
myfacet = FieldFacet("size", maptype=Count)
```

**Methods:**
- `add(groupname, docid, sortkey)`: Adds a document to the facet results.
- `as_dict()`: Returns a dictionary mapping group names to values.

### `OrderedList`

```python
class whoosh.sorting.OrderedList
```

Stores a list of document numbers for each group, in sorted order.

### `UnorderedList`

```python
class whoosh.sorting.UnorderedList
```

Stores a list of document numbers for each group in arbitrary order. Slightly
faster and more memory-efficient than `OrderedList` when ordering doesn't
matter.

### `Count`

```python
class whoosh.sorting.Count
```

Stores the count of documents in each group.

### `Best`

```python
class whoosh.sorting.Best
```

Stores the "best" (highest sort key) document in each group.

## Sorting Utilities

### `add_sortable`

```python
whoosh.sorting.add_sortable(
    writer,
    fieldname,
    facet,
    column=None
)
```

Adds a per-document value column to an existing field, making it sortable.
Useful for retrofitting fields that were created without `sortable=True`.

**Example:**
```python
from whoosh import index, sorting

ix = index.open_dir("indexdir")
with ix.writer() as w:
    facet = sorting.FieldFacet("price")
    sorting.add_sortable(w, "price", facet)
```

**Parameters:**
- `writer`: An `IndexWriter` object.
- `fieldname`: Name of the field to add sortable values to.
- `facet`: A `FacetType` object to generate per-document values.
- `column`: Optional `ColumnType` to store the values. If omitted, uses the
  field's default column type.
