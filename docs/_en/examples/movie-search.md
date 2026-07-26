---
color_scheme: dark
title: "Movie Search App"
parent: "Examples"
nav_order: 6
---

# Movie Search Application

A complete, runnable example showing how to build a small **movie search** application with Whoosh‑NG: schema design, indexing from a JSON dataset, faceted search, highlighting, and filtering.

## 1. Schema

```python
from whoosh.fields import Schema, TEXT, ID, KEYWORD, NUMERIC

schema = Schema(
    id=ID(stored=True, unique=True),
    title=TEXT(stored=True),
    director=TEXT(stored=True),
    genre=KEYWORD(stored=True, commas=True, scorable=True),
    year=NUMERIC(int, stored=True),
    synopsis=TEXT,
)
```

## 2. Index the dataset

```python
import json
import shutil
from whoosh import index
from whoosh.fields import Schema, TEXT, ID, KEYWORD, NUMERIC

schema = Schema(
    id=ID(stored=True, unique=True),
    title=TEXT(stored=True),
    director=TEXT(stored=True),
    genre=KEYWORD(stored=True, commas=True, scorable=True),
    year=NUMERIC(int, stored=True),
    synopsis=TEXT,
)

# Clean and create new index
shutil.rmtree("movies", ignore_errors=True)
ix = index.create_in("movies", schema)

movies = json.load(open("movies.json"))  # list of dicts

with ix.writer() as w:
    for m in movies:
        w.add_document(
            id=str(m["id"]),
            title=m["title"],
            director=m["director"],
            genre=",".join(m["genres"]),
            year=m["year"],
            synopsis=m["synopsis"],
        )
    w.commit()
```

Example `movies.json`:

```json
[
  {
    "id": 1,
    "title": "Blade Runner",
    "director": "Ridley Scott",
    "genres": ["sci-fi", "thriller"],
    "year": 1982,
    "synopsis": "A replicant hunter questions humanity in a rain-soaked future."
  },
  {
    "id": 2,
    "title": "Inception",
    "director": "Christopher Nolan",
    "genres": ["sci-fi", "action"],
    "year": 2010,
    "synopsis": "A thief who steals corporate secrets through dream-sharing technology."
  }
]
```

## 3. Search with facets and highlighting

```python
from whoosh import index
from whoosh.qparser import MultifieldParser
from whoosh.sorting import FieldFacet

ix = index.open_dir("movies")

qp = MultifieldParser(["title", "synopsis", "director"], ix.schema)

with ix.searcher() as s:
    q = qp.parse("future")

    # Search with sorting by year descending, grouped by genre
    results = s.search(
        q,
        sortedby=FieldFacet("year", reverse=True),
        groupedby=FieldFacet("genre", allow_overlap=True),
        limit=20,
    )

    for hit in results:
        print(hit["title"], hit["year"], "|", round(hit.score, 2))
        print("  ", hit.highlights("synopsis"))

    # Show genre facets
    print("\nGenres:", results.groups("genre"))
```

## 4. Filtering

Find sci-fi movies after 1990:

```python
from whoosh import index
from whoosh.qparser import QueryParser
from whoosh.query import Term, And, NumericRange

ix = index.open_dir("movies")
qp = QueryParser("synopsis", ix.schema)

with ix.searcher() as s:
    user_q = qp.parse("dream")
    filters = And([
        Term("genre", "sci-fi"),
        NumericRange("year", 1990, None),
    ])
    results = s.search(user_q, filter=filters)
    for hit in results:
        print(hit["title"], hit["year"])
```

## 5. Key takeaways

- `KEYWORD(commas=True)` stores multi-value fields that can be faceted.
- `MultifieldParser` searches multiple fields with optional boosts.
- `FieldFacet` enables faceted grouping and sorting.
- `hit.highlights()` returns highlighted snippets ready for display.
