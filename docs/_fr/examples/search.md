---
color_scheme: dark
title: "Recherche"
parent: "Exemples"
nav_order: 2
lang: fr
---

# Recherche

Exemples d’interrogation de l’index avec Whoosh‑NG.

## 1. Recherche basique

```python
from whoosh import index
from whoosh.qparser import QueryParser

ix = index.open_dir("indexdir")

with ix.searcher() as s:
    qp = QueryParser("content", ix.schema)
    q = qp.parse("python recherche")

    results = s.search(q, limit=10)
    for hit in results:
        print(f"{hit['title']}: {hit.score:.2f}")
```

## 2. Recherche multi-champs

```python
from whoosh.qparser import MultifieldParser

ix = index.open_dir("indexdir")
qp = MultifieldParser(
    ["title", "content", "tags"],
    ix.schema,
    fieldboosts={"title": 2.0, "tags": 1.5}
)

q = qp.parse("fastapi")
results = s.search(q)
```

## 3. Pagination

```python
with ix.searcher() as s:
    page = s.search_page(q, 2, pagelen=10)  # Page 2, 10 results/page

    print(f"Page {page.number} / {page.pagecount}")
    for hit in page:
        print(hit["title"])
```

## 4. Tri et filtres

```python
from whoosh.query import Term, And, NumericRange
from whoosh.sorting import FieldFacet, ScoreFacet

with ix.searcher() as s:
    # Filtrer par tags et année
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

## 5. Mise en évidence (highlighting)

```python
with ix.searcher() as s:
    results = s.search(q, limit=5)

    for hit in results:
        snippet = hit.highlights("content", top=2)
        print(f"{hit['title']}:")
        print(f"  {snippet}")
```

## 6. Recherche avec plage de dates

```python
from whoosh.query import DateRange
from datetime import datetime, timedelta

ix = index.open_dir("indexdir")
with ix.searcher() as s:
    start = datetime(2024, 1, 1)
    end = datetime(2024, 12, 31)
    q = DateRange("published", start, end)

    results = s.search(q)
```

## 7. Recherche par préfixe

```python
from whoosh.query import Prefix

with ix.searcher() as s:
    q = Prefix("title", "Py")  # Tous les titres commençant par "Py"
    results = s.search(q)
```

## Points clés

- `QueryParser` analyse la chaîne de requête en objet `Query`.
- `MultifieldParser` recherche sur plusieurs champs avec des boosts.
- `search_page()` pour la pagination.
- `filter` pour les filtres (ne pas inclure dans le score).
- `sortedby` pour trier par champ ou score.
