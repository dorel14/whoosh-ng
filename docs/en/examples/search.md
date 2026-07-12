---
color_scheme: dark
title: "Search Examples"
parent: "Examples"
nav_order: 2
---

# Search Examples

Real, runnable examples for querying and retrieving results with Whoosh‑NG.

## 1. Basic Search

```python
from whoosh import index
from whoosh.qparser import QueryParser

ix = index.open_dir("indexdir")

with ix.searcher() as s:
    qp = QueryParser("content", ix.schema)
    q = qp.parse("python search")

    results = s.search(q, limit=10)
    for hit in results:
        print(f"{hit['title']}: score={hit.score:.2f}")
```

## 2. Multi-field Search

```python
from whoosh.qparser import MultifieldParser

ix = index.open_dir("indexdir")
qp = MultifieldParser(
    ["title", "content", "tags"],
    ix.schema,
    fieldboosts={"title": 2.0, "tags": 1.5}
)

q = qp.parse("fastapi")
with ix.searcher() as s:
    results = s.search(q)
    for hit in results:
        print(hit["title"])
```

## 3. Pagination

```python
with ix.searcher() as s:
    page = s.search_page(q, 2, pagelen=10)  # Page 2, 10 per page

    print(f"Page {page.number} / {page.pagecount}")
    for hit in page:
        print(hit["title"])
```

## 4. Sort and Filter

```python
from whoosh.query import Term, And, NumericRange
from whoosh.sorting import FieldFacet, ScoreFacet

with ix.searcher() as s:
    filters = And([
        Term("tags", "python"),
        NumericRange("year", 2020, None),
    ])

    results = s.search(
        q,
        filter=filters,
        sortedby=[FieldFacet("year", reverse=True), ScoreFacet()],
        limit=20
    )
```

## 5. Highlighting

```python
with ix.searcher() as s:
    results = s.search(q, limit=5)

    for hit in results:
        snippet = hit.highlights("content", top=2)
        print(f"{hit['title']}:")
        print(f"  {snippet}")
```

## 6. Date Range Search

```python
from whoosh.query import DateRange
from datetime import datetime

with ix.searcher() as s:
    start = datetime(2024, 1, 1)
    end = datetime(2024, 12, 31)
    q = DateRange("published", start, end)

    results = s.search(q)
```

## 7. Prefix Search

```python
from whoosh.query import Prefix

with ix.searcher() as s:
    q = Prefix("title", "Py")  # All titles starting with "Py"
    results = s.search(q)
```

## Key points

- `QueryParser` parses a string into a `Query` object.
- `MultifieldParser` searches multiple fields with optional boosts.
- `search_page()` handles pagination.
- `filter` restricts results without affecting scores.
- `sortedby` sorts by field value or relevance score.