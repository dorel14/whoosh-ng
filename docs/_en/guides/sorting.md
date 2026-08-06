---
title: "Sorting and Faceting"
nav_order: 30
---

# Sorting and Faceting

This guide covers how to sort search results by field values and how to
group (facet) results by categories.

## Basic Sorting

By default, Whoosh returns results sorted by relevance score (descending).
You can sort by field values instead using the `sortedby` argument:

```python
from whoosh.sorting import FieldFacet

# Sort by date field, most recent first
results = searcher.search(query, sortedby="date")

# Sort ascending
results = searcher.search(query, sortedby=FieldFacet("date", reverse=True))
```

## Multi-Level Sorting

Sort by multiple fields by combining facets in a `MultiFacet`:

```python
from whoosh.sorting import FieldFacet, ScoreFacet, MultiFacet

# Sort by tag, then by score
facet = MultiFacet(["tag", ScoreFacet()])
results = searcher.search(query, sortedby=facet)

# Or build incrementally
facet = MultiFacet()
facet.add_field("tag")
facet.add_field("date", reverse=True)
facet.add_score()
results = searcher.search(query, sortedby=facet)
```

## Custom Sorting

### Function-Based Sorting

Use a custom function for sort keys:

```python
from whoosh.sorting import FunctionFacet

# Sort by document length (shortest first)
fn = lambda s, docid: s.doc_field_length(docid, "content")
lengths = FunctionFacet(fn)
results = searcher.search(query, sortedby=lengths)
```

### Stored Field Sorting

Sort by a stored (unindexed) field value:

```python
from whoosh.sorting import StoredFieldFacet

# Sort by a stored "category" field
facet = StoredFieldFacet("category", allow_overlap=True)
results = searcher.search(query, sortedby=facet)
```

## Range Faceting

Group results into numeric ranges:

```python
from whoosh.sorting import RangeFacet

prices = RangeFacet("price", 0, 1000, 100)
results = searcher.search(query, groupedby=prices)

for priceframe, docnums in results.groups("price").items():
    print(f"Price ${priceframe}: {len(docnums)} results")
```

## Date Range Faceting

Group results by date ranges:

```python
from datetime import datetime
from whoosh.sorting import DateRangeFacet

start = datetime(2020, 1, 1)
end = datetime(2026, 1, 1)
birthdays = DateRangeFacet("birthday", start, end, relativedelta(years=5))
results = searcher.search(query, groupedby=birthdays)
```

## Collapsing / Deduplication

Return at most one result per value of a facet:

```python
results = searcher.search(query, collapse=FieldFacet("domain"))

# Get counts of collapsed results
for key, count in results.collapsed_counts.items():
    print(key, count)
```

## Unicode Sorting

For locale-aware sorting, use a collation-based approach:

```python
from pyuca import Collator
from whoosh.sorting import FieldFacet, TranslateFacet

c = Collator("allkeys.txt")
facet = FieldFacet("name")
facet = TranslateFacet(c.sort_key, facet)
results = searcher.search(query, sortedby=facet)
```

## Making Fields Sortable After Index Creation

If a field was created without `sortable=True`, you can add sortable columns
to an existing index:

```python
from whoosh import index, sorting

ix = index.open_dir("indexdir")
with ix.writer() as w:
    facet = sorting.FieldFacet("price")
    sorting.add_sortable(w, "price", facet)
```
