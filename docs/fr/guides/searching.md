---
title: "Recherche"
nav_order: 24
parent: "Guides"
lang: fr
---

# Recherche

Guide pour exécuter des recherches, travailler avec les résultats, le scoring et le tri.

## Recherche basique

```python
from whoosh.qparser import QueryParser

with ix.searcher() as searcher:
    qp = QueryParser("content", ix.schema)
    q = qp.parse("bonjour monde")
    results = searcher.search(q)
    for hit in results:
        print(hit["title"], hit.score)
```

## Le Searcher

Le `Searcher` est l'interface principale pour lire l'index.

```python
# Toujours utiliser le context manager
with ix.searcher() as searcher:
    results = searcher.search(query)

# Ou gestion manuelle
searcher = ix.searcher()
try:
    results = searcher.search(query)
finally:
    searcher.close()
```

## QueryParser

Convertit une chaîne de requête en objet Query :

```python
from whoosh.qparser import QueryParser, OrGroup

# AND par défaut entre termes
qp = QueryParser("content", schema)
q = qp.parse("bonjour monde")  # content:bonjour AND content:monde

# Changer l'opérateur par défaut
qp = QueryParser("content", schema, group=OrGroup)
q = qp.parse("bonjour monde")  # content:bonjour OR content:monde
```

## Méthodes de recherche

### search()

```python
results = searcher.search(
    query,
    limit=10,           # Max résultats (None pour tout)
    sortedby=None,      # Clé(s) de tri
    reverse=False,      # Tri inversé
    terms=False,        # Collecter les termes matchés
    filter=None,        # Autoriser seulement ces docnums
    mask=None,          # Exclure ces docnums
    collapse=None       # Facette d'effondrement
)
```

### search_page()

```python
# Page 1, 10 résultats par page (défaut)
results = searcher.search_page(query, 1)

# Page 3, 20 résultats par page
results = searcher.search_page(query, 3, pagelen=20)
```

## Résultats

`Results` agit comme une liste de documents matchés :

```python
results = searcher.search(query)

# Support de slice
first_five = results[0:5]

# Longueur (peut déclencher un recompte)
total = len(results)

# Longueur scorée (ce qui est réellement retourné)
scored = results.scored_length()
```

### Objet Hit

```python
for hit in results:
    # Champs stockés
    title = hit["title"]
    path = hit["path"]

    # Score
    print(hit.score)

    # Surbrillance
    highlights = hit.highlights("content", top=3)
```

## Scoring

Le modèle de scoring par défaut est BM25F :

```python
from whoosh import scoring

with ix.searcher(weighting=scoring.BM25F()) as s:
    results = s.search(query)
```

### Scoring personnalisé

```python
class MyScorer(scoring.WeightingModel):
    def scorer(self, searcher, fieldname, text, qf=1):
        return MyCustomScorer(searcher, fieldname, text, qf)

with ix.searcher(weighting=MyScorer()) as s:
    results = s.search(query)
```

## Tri

```python
from whoosh import sorting

# Tri par champ unique
results = searcher.search(query, sortedby="date")

# Tri inversé
results = searcher.search(query, sortedby="date", reverse=True)

# Tri multi-champs
results = searcher.search(query, sortedby=[
    sorting.FieldFacet("category"),
    sorting.ScoreFacet()
])
```

## Facettes

```python
from whoosh import sorting

facet = sorting.FieldFacet("category")
with searcher.all_features() as features:
    facets = features.facet(facet)
    for cat, count in facets.most_common():
        print(f"{cat}: {count}")
```

## Filtrage et masquage

```python
from whoosh.query import Term

# Autoriser seulement les documents publiés
filter_q = Term("published", True)
results = searcher.search(query, filter=filter_q)

# Exclure les brouillons
mask_q = Term("draft", True)
results = searcher.search(query, mask=mask_q)
```

## Surbrillance

```python
results = searcher.search(query, terms=True)

for hit in results:
    print(hit.highlights("content", top=2))
```

## Recherches à temps limité

```python
from whoosh.collectors import TimeLimitCollector

with ix.searcher() as s:
    c = s.collector(limit=None)
    tlc = TimeLimitCollector(c, timelimit=5.0)
    try:
        s.search_with_collector(query, tlc)
    except TimeLimit:
        print("Recherche annulée: trop lente")
    results = tlc.results()
```
