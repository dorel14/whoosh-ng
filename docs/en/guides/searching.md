---
title: "Searching"
nav_order: 24
parent: "Guides"
---

# Searching

This guide covers executing searches, working with results, scoring, sorting, and filtering.

## Basic Search

```python
from whoosh.qparser import QueryParser

qp = QueryParser("content", ix.schema)
query = qp.parse("hello world")

with ix.searcher() as searcher:
    results = searcher.search(query)
    for hit in results:
        print(hit["title"], hit.score)
```

## The Searcher

The `Searcher` is the main interface for reading the index. It is lightweight and supports context management:

```python
# Always use context manager when possible
with ix.searcher() as searcher:
    results = searcher.search(query)

# Or manage manually
searcher = ix.searcher()
try:
    results = searcher.search(query)
finally:
    searcher.close()
```

### Searcher Options

```python
searcher = ix.searcher(
    weighting=None,       # Custom weighting model
    childperm=None,       # Permutations for nested documents
    fromindex=None        # Source index for cached readers
)
```

## QueryParser

Convert query strings into query objects:

```python
from whoosh.qparser import QueryParser, OrGroup

# Default: AND between terms
qp = QueryParser("content", schema)
q = qp.parse("hello world")  # Equivalent to: content:hello AND content:world

# Change default operator
qp = QueryParser("content", schema, group=OrGroup)
q = qp.parse("hello world")  # Equivalent to: content:hello OR content:world
```

## Search Methods

### search()

```python
results = searcher.search(
    query,
    limit=10,           # Max results (None for all)
    sortedby=None,      # Sort key(s)
    reverse=False,      # Reverse sort order
    terms=False,        # Collect matched terms
    filter=None,        # Allow only these docnums
    mask=None,          # Exclude these docnums
    collapse=None,      # Collapse facet
    collapse_limit=1    # Max docs per collapse key
)
```

### search_page()

```python
# Get page 1, 10 results per page (default)
results = searcher.search_page(query, 1)

# Get page 3, 20 results per page
results = searcher.search_page(query, 3, pagelen=20)
```

### search_with_collector()

For advanced result collection:

```python
from whoosh.collectors import FacetCollector

collector = FacetCollector(facets=[sorting.FieldFacet("date")])
searcher.search_with_collector(query, collector)
```

## Results Object

`Results` acts like a list of matched documents:

```python
results = searcher.search(query)

# Slice support
first_five = results[0:5]

# Length (may trigger recount)
total = len(results)

# Scored length (usually what was actually returned)
scored = results.scored_length()

# Iteration
for hit in results:
    print(hit["title"], hit.score)
```

### Hit Object

```python
for hit in results:
    # Stored fields
    title = hit["title"]
    path = hit["path"]

    # Score
    print(hit.score)

    # Highlighting
    highlights = hit.highlights("content", top=3)

    # Matched terms (if terms=True was used)
    if results.has_matched_terms():
        print(hit.matched_terms())
```

## Scoring

The default scoring model is BM25F:

```python
from whoosh import scoring

with ix.searcher(weighting=scoring.BM25F()) as s:
    results = s.search(query)
```

### Custom Scoring

```python
class MyScorer(scoring.WeightingModel):
    def scorer(self, searcher, fieldname, text, qf=1):
        return MyCustomScorer(searcher, fieldname, text, qf)

with ix.searcher(weighting=MyScorer()) as s:
    results = s.search(query)
```

## Sorting

Sort by a field or facet:

```python
from whoosh import sorting

# Sort by a single field
results = searcher.search(query, sortedby="date")

# Reverse sort
results = searcher.search(query, sortedby="date", reverse=True)

# Multi-field sort
results = searcher.search(query, sortedby=[
    sorting.FieldFacet("category"),
    sorting.ScoreFacet()
])
```

## Faceting

Used for grouping results:

```python
from whoosh import sorting

facet = sorting.FieldFacet("category")
with searcher.all_features() as features:
    facets = features.facet(facet)
    for cat, count in facets.most_common():
        print(f"{cat}: {count}")
```

## Filtering and Masking

```python
# Only show documents matching a subquery
filter_q = Term("published", True)
results = searcher.search(query, filter=filter_q)

# Exclude documents
mask_q = Term("draft", True)
results = searcher.search(query, mask=mask_q)
```

## Collapsing

Remove duplicates or limit per-group:

```python
from whoosh import sorting

# Collapse by hostname, keep top 3 per host
results = searcher.search(
    query,
    collapse=sorting.FieldFacet("hostname"),
    collapse_limit=3
)

# Collapse ordering (keep highest rated per type)
results = searcher.search(
    query,
    sortedby=sorting.FieldFacet("price", reverse=True),
    collapse=sorting.FieldFacet("type"),
    collapse_order=sorting.FieldFacet("rating", reverse=True)
)
```

## Highlighting

Get highlighted snippets for query terms:

```python
results = searcher.search(query, terms=True)

for hit in results:
    print(hit.highlights("content", top=2))

# Custom fragmenter
from whoosh.highlight import highlight

fragments = hit.highlights(
    "content",
    top=3,
    fragmenter=...,
    formatter=...
)
```

## Time-Limited Searches

```python
from whoosh.collectors import TimeLimitCollector

with ix.searcher() as s:
    c = s.collector(limit=None)
    tlc = TimeLimitCollector(c, timelimit=5.0)
    try:
        s.search_with_collector(query, tlc)
    except TimeLimit:
        print("Search aborted: too slow")
    results = tlc.results()
```

## Combining Results

```python
# Run two queries
best_bet_results = s.search(best_bet_query, limit=5)
main_results = s.search(main_query, limit=10)

# Merge: duplicates go to top, then append rest
best_bet_results.upgrade_and_extend(main_results)
```
