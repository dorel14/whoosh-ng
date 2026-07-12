---
color_scheme: dark
title: "Recherche de Films"
parent: "Exemples"
nav_order: 6
lang: fr
---

# Application de Recherche de Films

Exemple complet montrant comment créer une petite **application de recherche de films** avec Whoosh‑NG : conception du schéma, indexation à partir d’un fichier JSON, recherche facettée, mise en évidence et filtrage.

## 1. Schéma

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

## 2. Indexer les documents

```python
import json
import shutil
from whoosh import index

shutil.rmtree("movies", ignore_errors=True)
ix = index.create_in("movies", schema)

movies = json.load(open("movies.json"))

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

Fichier `movies.json` :

```json
[
  {
    "id": 1,
    "title": "Blade Runner",
    "director": "Ridley Scott",
    "genres": ["sci-fi", "thriller"],
    "year": 1982,
    "synopsis": "Un chasseur de replicants questionne l’humanité dans un futur pluvieux."
  }
]
```

## 3. Recherche avec facettes et mise en évidence

```python
from whoosh import index
from whoosh.qparser import MultifieldParser
from whoosh.sorting import FieldFacet

ix = index.open_dir("movies")

qp = MultifieldParser(["title", "synopsis", "director"], ix.schema)

with ix.searcher() as s:
    q = qp.parse("sci-fi")

    results = s.search(
        q,
        sortedby=FieldFacet("year", reverse=True),
        groupedby=FieldFacet("genre", allow_overlap=True),
        limit=20,
    )

    for hit in results:
        print(hit["title"], hit["year"], "|", round(hit.score, 2))
        print("  ", hit.highlights("synopsis"))

    print("\nGenres:", results.groups("genre"))
```

## 4. Filtrage

Filtrer les films de science-fiction après 1990 :

```python
from whoosh import index
from whoosh.qparser import QueryParser
from whoosh.query import Term, And, NumericRange

ix = index.open_dir("movies")
qp = QueryParser("synopsis", ix.schema)

with ix.searcher() as s:
    user_q = qp.parse("future")
    filters = And([
        Term("genre", "sci-fi"),
        NumericRange("year", 1990, None),
    ])
    results = s.search(user_q, filter=filters)
    for hit in results:
        print(hit["title"], hit["year"])
```

## Points clés

- `KEYWORD(commas=True)` stocke des champs multi-valeurs facetables.
- `MultifieldParser` recherche sur plusieurs champs avec des boosts optionnels.
- `FieldFacet` permet les facettes et le tri.
- `hit.highlights()` renvoie des fragments mis en évidence prêts à afficher.
