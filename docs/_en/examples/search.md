---
title: "Search Examples"
nav_order: 210
---

# Search Examples

Real, runnable search examples with Whoosh‑NG. Each section is a self-contained
script you can copy into a `.py` file and run.

> **Real-world scenario**: You built a book‑catalogue index (see
> `docs/_en/examples/basic-indexing.md`). Below are the search patterns
> you'll need for a production‑ready book search page.

## Prerequisites

The examples assume an index exists at `book_index/` with this schema:

```python
from whoosh import index
from whoosh.fields import Schema, TEXT, ID, NUMERIC, DATETIME

schema = Schema(
    isbn=ID(stored=True, unique=True),
    title=TEXT(stored=True),
    author=TEXT(stored=True),
    content=TEXT,
    genre=KEYWORD(stored=True, commas=True),
    published_year=NUMERIC(int, stored=True, sortable=True),
    rating=NUMERIC(float, stored=True, sortable=True),
)
```

## 1. Basic Search — "Find books about Python"

```python
from whoosh import index
from whoosh.qparser import QueryParser

ix = index.open_dir("book_index")

with ix.searcher() as s:
    qp = QueryParser("content", ix.schema)
    q = qp.parse("python")

    results = s.search(q, limit=10)
    for hit in results:
        print(f"{hit['title']} by {hit['author']} (ISBN: {hit['isbn']}) — score={hit.score:.2f}")
```

## 2. Multi-field Search with Boosts

Search across `title`, `author`, and `content` simultaneously. Title matches
are boosted 3× so they rank higher:

```python
from whoosh.qparser import MultifieldParser

ix = index.open_dir("book_index")
qp = MultifieldParser(
    ["title", "author", "content"],
    ix.schema,
    fieldboosts={"title": 3.0, "author": 2.0, "content": 1.0},
)

q = qp.parse("clean code")

with ix.searcher() as s:
    results = s.search(q, limit=10)
    for hit in results:
        print(f"{hit['title']} — {hit['author']}")
```

## 3. Pagination — "Page 3 of search results"

```python
ix = index.open_dir("book_index")
qp = QueryParser("content", ix.schema)
q = qp.parse("machine learning")

with ix.searcher() as s:
    page = s.search_page(q, 3, pagelen=15)  # Page 3, 15 results per page

    print(f"Page {page.number} / {page.pagecount}  ({page.total} results total)")
    for hit in page:
        print(f"  {hit['title']}")
```

## 4. Sort and Filter — "High-rated sci-fi books after 2010"

```python
from whoosh.query import Term, And, NumericRange
from whoosh.sorting import FieldFacet, ScoreFacet

ix = index.open_dir("book_index")
qp = QueryParser("content", ix.schema)
q = qp.parse("space")

with ix.searcher() as s:
    # Filter: genre must be "sci-fi" AND year >= 2010
    filters = And([
        Term("genre", "sci-fi"),
        NumericRange("published_year", 2010, None),
    ])

    results = s.search(
        q,
        filter=filters,
        sortedby=FieldFacet("rating", reverse=True),  # highest-rated first
        limit=20,
    )
    for hit in results:
        print(f"{hit['title']} ({hit['published_year']}) — rating: {hit['rating']}")
```

## 5. Highlighting — "Show users where their query matched"

```python
ix = index.open_dir("book_index")
qp = QueryParser("content", ix.schema)
q = qp.parse("neural networks")

with ix.searcher() as s:
    results = s.search(q, limit=5)

    for hit in results:
        snippet = hit.highlights("content", top=2)  # show 2 best fragments
        print(f"{hit['title']}:")
        print(f"  {snippet}")
        print()
```

## 6. Date / Numeric Range Search — "Books published in 2023"

```python
from whoosh.query import NumericRange

ix = index.open_dir("book_index")

with ix.searcher() as s:
    q = NumericRange("published_year", 2023, 2023)
    results = s.search(q)
    print(f"{results.total} books published in 2023")
```

## 7. Prefix Search — "All books starting with 'Deep'"

```python
from whoosh.query import Prefix

ix = index.open_dir("book_index")

with ix.searcher() as s:
    q = Prefix("title", "Deep")  # titles starting with "Deep"
    results = s.search(q)
    for hit in results:
        print(hit["title"])
```

## 8. Faceted Search — "Group results by genre"

```python
from whoosh.sorting import FieldFacet

ix = index.open_dir("book_index")
qp = QueryParser("content", ix.schema)
q = qp.parse("programming")

with ix.searcher() as s:
    results = s.search(q, groupedby=FieldFacet("genre"))

    # Show top genres alongside results
    for genre, group in results.groups("genre").items():
        print(f"{genre}: {len(group)} hits")
```

## Key points

- `QueryParser` parses a string into a `Query` object.
- `MultifieldParser` searches multiple fields with optional per-field boosts.
- `search_page()` handles pagination automatically.
- `filter` restricts results without affecting relevance scores.
- `sortedby` sorts by field value or relevance score.
- `hit.highlights()` returns highlighted snippets ready for display.
- `groupedby` enables faceted result grouping.
