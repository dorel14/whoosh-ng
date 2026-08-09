---
title: "Recherche"
sidebar_position: 210
---

# Recherche

Exemples concrets d'interrogation d'un index Whoosh-NG.

> **Scénario** : Vous avez indexé un catalogue de livres (voir `basic-indexing.md`).
> Les exemples ci-dessous montrent les patterns de recherche produit.

## Prérequis

L'index `book_index/` contient ce schéma :

```python
from whoosh.fields import Schema, TEXT, ID, KEYWORD, NUMERIC

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

## 1. Recherche basique — « Livres sur Python »

```python
from whoosh import index
from whoosh.qparser import QueryParser

ix = index.open_dir("book_index")

with ix.searcher() as s:
    qp = QueryParser("content", ix.schema)
    q = qp.parse("python")

    results = s.search(q, limit=10)
    for hit in results:
        print(f"{hit['title']} par {hit['author']} — score={hit.score:.2f}")
```

## 2. Recherche multi-champs avec boosts

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

## 3. Pagination — « Page 3 des résultats »

```python
ix = index.open_dir("book_index")
qp = QueryParser("content", ix.schema)
q = qp.parse("machine learning")

with ix.searcher() as s:
    page = s.search_page(q, 3, pagelen=15)

    print(f"Page {page.number} / {page.pagecount} ({page.total} résultats)")
    for hit in page:
        print(f"  {hit['title']}")
```

## 4. Tri et filtres — « Sci-fi noté ≥4 après 2010 »

```python
from whoosh.query import Term, And, NumericRange
from whoosh.sorting import FieldFacet

ix = index.open_dir("book_index")
qp = QueryParser("content", ix.schema)
q = qp.parse("space")

with ix.searcher() as s:
    filters = And([
        Term("genre", "sci-fi"),
        NumericRange("published_year", 2010, None),
    ])

    results = s.search(
        q,
        filter=filters,
        sortedby=FieldFacet("rating", reverse=True),
        limit=20,
    )
    for hit in results:
        print(f"{hit['title']} ({hit['published_year']}) — note: {hit['rating']}")
```

## 5. Mise en évidence — « Où la requête correspond »

```python
ix = index.open_dir("book_index")
qp = QueryParser("content", ix.schema)
q = qp.parse("réseaux de neurones")

with ix.searcher() as s:
    results = s.search(q, limit=5)

    for hit in results:
        snippet = hit.highlights("content", top=2)
        print(f"{hit['title']}:")
        print(f"  {snippet}")
```

## 6. Recherche par plage — « Livres publiés en 2023 »

```python
from whoosh.query import NumericRange

ix = index.open_dir("book_index")

with ix.searcher() as s:
    q = NumericRange("published_year", 2023, 2023)
    results = s.search(q)
    print(f"{results.total} livres publiés en 2023")
```

## 7. Recherche par préfixe — « Titres commençant par "Deep" »

```python
from whoosh.query import Prefix

ix = index.open_dir("book_index")

with ix.searcher() as s:
    q = Prefix("title", "Deep")
    results = s.search(q)
    for hit in results:
        print(hit["title"])
```

## 8. Recherche facetée — « Grouper par genre »

```python
from whoosh.sorting import FieldFacet

ix = index.open_dir("book_index")
qp = QueryParser("content", ix.schema)
q = qp.parse("programming")

with ix.searcher() as s:
    results = s.search(q, groupedby=FieldFacet("genre"))

    for genre, group in results.groups("genre").items():
        print(f"{genre}: {len(group)} résultats")
```

## Points clés

- `QueryParser` analyse une chaîne en objet `Query`.
- `MultifieldParser` recherche plusieurs champs avec des boosts.
- `search_page()` gère la pagination.
- `filter` restreint les résultats sans affecter le score.
- `sortedby` trie par valeur de champ ou par score de pertinence.
- `hit.highlights()` renvoie des extraits mis en surbrillance.
