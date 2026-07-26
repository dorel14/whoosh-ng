---
color_scheme: dark
title: "Searching API"
nav_order: 4
parent: "API Reference"
---

# Searching API

Execute queries and retrieve results.

## Searcher

```python
class whoosh.searching.Searcher
```

The Searcher is the primary interface for reading from the index.

### Methods

#### `search()`

```python
results = searcher.search(query, limit=10, **kwargs)
```

Execute a query and return Results.

**Args:**
- `query`: The query to run.
- `limit (int)`: Maximum number of results. Use `None` for all results.

**Returns:**
- `Results`: A Results object.

---

#### `search_page()`

```python
results = searcher.search_page(query, pagenum, pagelen=10)
```

Get a page of results.

---

#### `search_with_collector()`

```python
searcher.search_with_collector(query, collector)
```

Advanced search with custom collector.

---

#### `find()`

```python
results = searcher.find("field", "text")
```

Convenience method to search a single field.

---

#### `documents()`

```python
docs = list(searcher.documents(fieldname=value))
```

Get stored documents matching a term.

---

#### `document()`

```python
doc = searcher.document(fieldname=value)
```

Get a single stored document.

---

#### `lexicon()`

```python
terms = list(searcher.lexicon("fieldname"))
```

List all terms in a field.

---

#### `all_stored_fields()`

```python
for fields in searcher.all_stored_fields():
    print(fields)
```

Iterate over all stored fields.

---

#### `all_features()`

```python
with searcher.all_features() as features:
    facets = features.facet(facet)
```

Get facet counts across all documents.

## Results

```python
class whoosh.searching.Results
```

List-like container for matched documents.

### Methods

#### `__len__()`

```python
total = len(results)
```

Total matching documents (may recount).

#### `scored_length()`

```python
scored = results.scored_length()
```

Number of scored/sorted documents in this results object.

#### `__getitem__()`

```python
hit = results[0]
hits = results[0:10]
```

Get a hit by index or slice.

#### `has_matched_terms()`

```python
if results.has_matched_terms():
    print(results.matched_terms())
```

Check if matched terms were collected.

#### `iter_matched_terms()`

Iterate over (docnum, term) pairs.

#### `upgrade()`

Move docs from another Results to top.

#### `extend()`

Append docs from another Results.

#### `upgrade_and_extend()`

Upgrade docs and append rest.

#### `filtered_count`

Number of documents filtered out.

#### `collapsed_counts`

Dict of collapse keys to filtered counts.

## Hit

```python
class whoosh.searching.Hit
```

A single matched document.

### Attributes

- `hit["fieldname"]`: Stored field value
- `hit.score`: Relevance score
- `hit.docnum`: Internal document number

### Methods

#### `highlights()`

```python
snippets = hit.highlights("content", top=3)
```

Get highlighted snippets.

#### `matched_terms()`

```python
terms = hit.matched_terms()
```

Get terms that matched (if `terms=True`).

## Highlight

```python
from whoosh.highlight import highlight, Fragment

snippets = hit.highlights(
    "content",
    top=3,
    fragmenter=None,
    formatter=None
)
```

## Collectors

```python
from whoosh.collectors import Collector, FacetCollector, TimeLimitCollector
```

## Sorting and Facets

```python
from whoosh import sorting

facet = sorting.FieldFacet("category")
results = searcher.search(query, sortedby="date")
```
