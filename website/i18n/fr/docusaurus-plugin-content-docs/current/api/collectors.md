---
title: 'Collectors API'
sidebar_position: 0
---

> **Note de traduction** : Cette page n'est pas encore traduite en français.
> Le contenu anglais est affiché ci-dessous en attendant la traduction.

<!-- Creez une version francaise de ce fichier et supprimez ce message. -->


# Collectors API

Classes and functions for gathering search results. Collectors are used
internally by `Searcher.search()` to collect matching documents and build
`Results` objects. The collectors module is a refactored package exposing the
same public API as the former monolithic module.

## Overview

A `Collector` iterates over matching documents in an index, collects
information about them, and produces a `Results` object. The base `Collector`
class defines the interface; specialized subclasses implement different
collection strategies (top-N, unlimited, sorting, filtering, faceting, etc.).

## Core Classes

### `Collector`

```python
class whoosh.collectors.Collector
```

Abstract base class for all collectors. Subclasses must implement `collect()`
and `results()`.

**Methods:**

#### `prepare(top_searcher, q, context)`

Called before a search begins. Sets up `self.top_searcher`, `self.q`,
`self.context`, `self.starttime`, and `self.docset`.

#### `run()`

Iterates over sub-searchers, calling `set_subsearcher()` and
`collect_matches()` for each, then calls `finish()`.

#### `set_subsearcher(subsearcher, offset)`

Called when moving to a new sub-searcher. Sets `self.subsearcher`,
`self.offset`, and `self.matcher`.

#### `collect(sub_docnum)`

Called for every matched document. Must add the document to results and
return a sort key. Subclasses must implement this.

- `sub_docnum`: Segment-relative document number. Add `self.offset` to get
  the top-level document number.

#### `sort_key(sub_docnum)`

Returns a sort key for the current match without the side effect of adding
the document to results. Subclasses must implement this.

#### `collect_matches()`

Calls `matches()` and then `collect()` for each matched document.

#### `matches()`

Yields segment-relative document numbers for matches in the current
sub-searcher.

#### `count()`

Returns the total number of matching documents.

#### `all_ids()`

Returns a sequence of docnums matched in this collector.

#### `computes_count()`

Returns `True` if the collector naturally computes the exact count of
matching documents.

#### `finish()`

Called after the search completes. Sets `self.runtime`.

#### `remove(global_docnum)`

Removes a document from the collector using its global docnum.

#### `results()`

Returns a `Results` object. Subclasses must implement this.

### `ilen`

```python
whoosh.collectors.ilen(iterator) -> int
```

Counts the number of items in an iterator without loading it all into memory.

## Scored Collectors

### `ScoredCollector`

```python
class whoosh.collectors.ScoredCollector(replace=10)
```

Base class for collectors that sort by document score.

**Constructor:**
- `replace`: Number of matches between attempts to replace the matcher with
  a more efficient version.

### `TopCollector`

```python
class whoosh.collectors.TopCollector(
    limit=10,
    usequality=True,
    **kwargs
)
```

A collector that returns only the top N scored results.

**Constructor:**
- `limit`: Maximum number of results to return.
- `usequality`: Whether to use block-quality optimizations for faster
  search. Can be set to `False` for debugging.

**Notes:**
- When `usequality=True`, `computes_count()` returns `False` and
  `all_ids()` requires re-searching.
- Uses a min-heap to efficiently track the top N documents.

### `UnlimitedCollector`

```python
class whoosh.collectors.UnlimitedCollector(reverse=False)
```

A collector that returns **all** scored results. Sorts by score (descending
by default).

**Constructor:**
- `reverse`: If `True`, sort results in ascending order (lowest scores first).

### `UnsortedCollector`

```python
class whoosh.collectors.UnsortedCollector
```

A collector that returns results in document order (no sorting). Used when
the search weighting is `None`.

## Wrapping Collectors

### `WrappingCollector`

```python
class whoosh.collectors.WrappingCollector(child)
```

Base class for collectors that wrap other collectors. Delegates most
operations to the child collector while adding additional behavior.

**Constructor:**
- `child`: The collector to wrap.

**Methods** (all delegated to child):
`top_searcher`, `context`, `prepare`, `set_subsearcher`, `all_ids`,
`count`, `collect_matches`, `sort_key`, `collect`, `remove`, `matches`,
`finish`, `results()`

### `SortingCollector`

```python
class whoosh.collectors.SortingCollector(
    sortedby,
    limit=10,
    reverse=False
)
```

A collector that returns results sorted by a `FacetType` object.

**Constructor:**
- `sortedby`: A `FacetType` or field name to sort by.
- `limit`: Maximum number of results (0 for no limit).
- `reverse`: If `True`, reverse the overall sort order.

### `FilterCollector`

```python
class whoosh.collectors.FilterCollector(
    child,
    allow=None,
    restrict=None
)
```

A collector that allows and/or restricts certain document numbers in
results.

A document is discarded if:
- `allow` is set and the docnum is not in the allowed set, or
- `restrict` is set and the docnum is in the restricted set.

**Constructor:**
- `child`: The collector to wrap.
- `allow`: A query, `Results` object, or set-like of allowed docnums.
  `None` means everything is allowed.
- `restrict`: A query, `Results` object, or set-like of disallowed docnums.
  `None` means nothing is disallowed.

**Attributes:**
- `filtered_count`: Number of documents filtered out.

### `FacetCollector`

```python
class whoosh.collectors.FacetCollector(child, groupedby, maptype=None)
```

A collector that creates groups of documents based on facet objects. Used
when `groupedby` is specified in `Searcher.search()`.

**Constructor:**
- `child`: The collector to wrap.
- `groupedby`: A field name, `FacetType`, dict, or `Facets` object.
- `maptype`: Default `FacetMap` class for facets that don't specify one.

**Attributes:**
- `facetmaps`: Dictionary of facet name to `FacetMap` objects.

### `CollapseCollector`

```python
class whoosh.collectors.CollapseCollector(
    child,
    keyfacet,
    limit=1,
    order=None
)
```

A collector that eliminates all but the top N results sharing the same facet
key. Useful for "dedup" or grouped result views.

**Constructor:**
- `child`: The collector to wrap.
- `keyfacet`: A `FacetType` to collapse on. All but the top N documents
  sharing a key are eliminated.
- `limit`: Maximum documents to keep per key (default `1`).
- `order`: Optional `FacetType` to determine which documents are "top" within
  each group. Defaults to the results order (e.g., highest score).

**Attributes:**
- `collapsed_counts`: Dictionary mapping keys to the number of documents
  eliminated.

### `TimeLimitCollector`

```python
class whoosh.collectors.TimeLimitCollector(
    child,
    timelimit,
    greedy=False,
    use_alarm=True
)
```

A collector that raises a `TimeLimit` exception if the search exceeds a
time limit. Partial results are still available via `results()`.

**Constructor:**
- `child`: The collector to wrap.
- `timelimit`: Maximum search time in seconds.
- `greedy`: If `True`, finish adding the current hit before raising.
- `use_alarm`: If `True` (default), use `signal.SIGALRM` on Unix for
  immediate interruption. On Windows, time is only checked between
  documents.

```python
from whoosh.searching import TimeLimit

uc = collectors.UnlimitedCollector()
tlc = TimeLimitCollector(uc, timelimit=5.8)
try:
    searcher.search_with_collector(myquery, tlc)
except TimeLimit:
    print("Search timed out!")
# Still get partial results:
print(tlc.results())
```

### `TermsCollector`

```python
class whoosh.collectors.TermsCollector(child, settype=set)
```

A collector that records which terms appeared in which matched documents.
Used when `terms=True` in `Searcher.search()`.

**Constructor:**
- `child`: The collector to wrap.
- `settype`: Set type to use for docnum collections (default `set`).

**Attributes:**
- `termdocs`: Dict mapping `(fieldname, text)` tuples to arrays of docnums.
- `docterms`: Dict mapping docnums to lists of `(fieldname, text)` tuples.

## Exceptions

### `TimeLimit`

```python
from whoosh.searching import TimeLimit
```

Raised by `TimeLimitCollector` when the search exceeds the time limit.
Partial results are still available from the collector.

