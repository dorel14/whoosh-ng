---
title: "Recherche"
parent: "Exemples"
lang: fr
nav_order: 2
---

# Recherche

Exemples d'interrogation de l'index avec Whoosh-NG.

## Recherche basique

```python
from whoosh.qparser import QueryParser
from whoosh import index

ix = index.open_dir("indexdir")
with ix.searcher() as searcher:
    qp = QueryParser("content", ix.schema)
    q = qp.parse("bonjour qui")
    results = searcher.search(q)
    for hit in results:
        print(hit["title"], hit.score)
```

## MultifieldParser

```python
from whoosh.qparser import MultifieldParser, OrGroup

ix = index.open_dir("indexdir")
qp = MultifieldParser(
    ["title", "content"],
    ix.schema,
    fieldboosts={"title": 2.0}
)
q = qp.parse("python recherche")
```

## Pagination

```python
with ix.searcher() as searcher:
    results = searcher.search_page(q, 1, pagelen=10)
    total = len(results)
    print(f"Total: {total} résultats")
```

## Tri et filtre

```python
from whoosh.query import Term
from whoosh import sorting

with ix.searcher() as searcher:
    q = qp.parse("python")
    results = searcher.search(
        q,
        filter=Term("published", True),
        sortedby=sorting.FieldFacet("date")
    )
```

## Surbrillance

```python
with ix.searcher() as searcher:
    results = searcher.search_page(q, 1)
    for hit in results:
        print(hit.highlights("content", top=3))
```
