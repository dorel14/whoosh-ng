---
title: "API Recherche"
nav_order: 4
parent: "Référence API"
lang: fr
---

# API Recherche

Exécuter des requêtes et récupérer les résultats.

## Searcher

```python
class whoosh.searching.Searcher
```

Interface principale pour lire l'index.

### Méthodes

| Méthode | Description |
|---------|-------------|
| `search(query, limit=10)` | Exécute une requête |
| `search_page(query, pagenum, pagelen=10)` | Récupère une page de résultats |
| `search_with_collector(query, collector)` | Recherche avancée avec collector |
| `find(fieldname, text)` | Recherche dans un champ |
| `documents(**kwargs)` | Documents stockés correspondants |
| `document(**kwargs)` | Un document stocké |
| `lexicon(fieldname)` | Liste des termes d'un champ |
| `all_stored_fields()` | Itère sur tous les champs stockés |

## Results

```python
class whoosh.searching.Results
```

Conteneur de résultats (semblable à une liste).

### Méthodes

| Méthode/attribut | Description |
|------------------|-------------|
| `len(results)` | Nombre total de correspondances |
| `results.scored_length()` | Nombre de résultats scorés |
| `results[0]` | Premier résultat |
| `results[0:10]` | Slice de résultats |
| `results.has_matched_terms()` | Vérifie si les termes matchés sont collectés |
| `results.filtered_count` | Nombre de documents filtrés |
| `results.collapsed_counts` | Comptage par clé d'effondrement |

## Hit

```python
class whoosh.searching.Hit
```

Un document matché.

### Attributs

- `hit["champ"]`: Valeur du champ stocké
- `hit.score`: Score de pertinence
- `hit.docnum`: Numéro interne du document

### Méthodes

| Méthode | Description |
|---------|-------------|
| `hit.highlights("content", top=3)` | Extrait surlignés |
| `hit.matched_terms()` | Termes matchés (si `terms=True`) |

## Highlight

```python
from whoosh.highlight import highlight, Fragment

snippets = hit.highlights("content", top=3)
```

## Collectors

```python
from whoosh.collectors import FacetCollector, TimeLimitCollector
```

## Tri et facettes

```python
from whoosh import sorting

facet = sorting.FieldFacet("categorie")
results = searcher.search(query, sortedby="date")
```
