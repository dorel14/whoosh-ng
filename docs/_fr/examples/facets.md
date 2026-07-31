---
title: "Gestionnaire de facettes"
nav_order: 242
lang: fr
---

# Gestionnaire de facettes

`FacetManager` gère la configuration des facettes pour un schéma Whoosh.

## Usage basique

```python
from whoosh.fields import Schema, TEXT, NUMERIC, BOOLEAN
from whoosh_modern.facets import FacetManager, TermsFacet, RangeFacet

schema = Schema(
    title=TEXT(stored=True),
    category=TEXT(sortable=True),
    price=NUMERIC(),
    active=BOOLEAN(),
)

manager = FacetManager(schema)
```

## Auto-découverte

| Type Whoosh | Facette auto-découverte |
|-------------|-------------------------|
| `KEYWORD`, `BOOLEAN`, `ID` | `TermsFacet` |
| `NUMERIC` | `RangeFacet` |
| `DATETIME` | `DateRangeFacet` |

```python
facets = manager.get_facets()
manager.is_facetable("category")  # True
manager.is_facetable("title")     # False
```

## Remplacement manuel

```python
manager.set_manual_override("category", {"type": "terms", "limit": 50})
manager.set_manual_override("price", {"type": "range", "buckets": ["0-10", "10-50"]})
```

## Statistiques

```python
stats = manager.get_facet_stats()
# {"total_fields": 4, "auto_discovered_facets": 2, ...}
```