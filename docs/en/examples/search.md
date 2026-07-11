---
title: "Search Examples"
parent: "Exemples"
nav_order: 2
---

# Search Examples

Examples for querying and retrieving results.

## Basic Search

```python
from whoosh.qparser import QueryParser
from whoosh import index

ix = index.open_dir("indexdir")
with ix.searcher() as searcher:
    qp = QueryParser("content", ix.schema)
    q = qp.parse("hello python")
    results = searcher.search(q)

    for hit in results:
        print(hit["title"], hit.score)
```

## Pagination

```python
with ix.searcher() as searcher:
    page = 1
    results = searcher.search_page(q, page, pagelen=10)
    total = len(results)
    print(f"Total: {total} results")
```

## Multi-field Search

```python
from whoosh.qparser import MultifieldParser

ix = index.open_dir("indexdir")
qp = MultifieldParser(
    ["title", "content"],
    ix.schema,
    fieldboosts={"title": 2.0}
)
q = qp.parse("python")
```

## Sort and Filter

```python
from whoosh.query import Term

ix = index.open_dir("indexdir")
with ix.searcher() as searcher:
    qp = QueryParser("content", ix.schema)
    q = qp.parse("python")
    results = searcher.search(
        q,
        filter=Term("rating", 5.0),
        sortedby="rating",
        reverse=True
    )
```

## Highlighting

```python
with ix.searcher() as searcher:
    results = searcher.search_page(q, 1)
    for hit in results:
        highlights = hit.highlights("content", top=3)
        print(f"{hit['title']}: {highlights}")
```

## Time-Limited Search

```python
from whoosh.collectors import TimeLimitCollector

with ix.searcher() as searcher:
    c = searcher.collector(limit=50)
    tlc = TimeLimitCollector(c, timelimit=2.0)
    try:
        searcher.search_with_collector(q, tlc)
    except Exception as exc:
        print(f"Timed out or failed: {exc}")
    results = tlc.results()
```

## Facet and Group

```python
from whoosh import sorting

with ix.searcher() as searcher:
    facet = sorting.FieldFacet("rating")
    results = searcher.search(
        q,
        sortedby=[facet, sorting.ScoreFacet()]
    )
```
