---
title: "Facet Manager"
sidebar_position: 248
---

# Facet Manager

`FacetManager` manages facet configuration for a Whoosh `Schema`. It auto-discovers facetable fields and supports manual overrides.

## Basic Usage

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

## Auto-Discovery

FacetManager automatically identifies facetable fields:

| Whoosh Field Type | Facet Type |
|-------------------|------------|
| `TEXT`, `KEYWORD`, `BOOLEAN`, `ID` | `TermsFacet` |
| `NUMERIC` | `RangeFacet` |
| `DATETIME` | `DateRangeFacet` |

```python
# Auto-discovered facets
facets = manager.get_facets()
# {"title": TermsFacet(limit=100), "category": TermsFacet(limit=100),
#  "price": RangeFacet("price", 0, 1000, 100), "active": TermsFacet(limit=100)}
```

> `RangeFacet` and `DateRangeFacet` are re-exports of the core
> `whoosh.sorting.RangeFacet` / `whoosh.sorting.DateRangeFacet`, so the facet objects
> returned by `FacetManager` can be passed directly to `searcher.search(..., groupedby=...)`.

## Manual Override

```python
from whoosh_modern.facets import TermsFacet

manager.set_manual_override("category", {
    "type": "terms",
    "limit": 50,
})
manager.set_manual_override("price", {
    "type": "range",
    "buckets": ["0-10", "10-50", "50-100", "100+"],
})
```

## Inspection

```python
# Is a field facetable?
manager.is_facetable("category")   # True
manager.is_facetable("title")      # False

# Get config for a field
config = manager.get_facet_config("category")
# {"type": "terms", "limit": 50}

# Get all configs
all_configs = manager.get_all_facet_configs()

# Get statistics
stats = manager.get_facet_stats()
# {
#     "total_fields": 4,
#     "auto_discovered_facets": 2,
#     "manual_overrides": 1,
#     "total_facets_configured": 3,
#     "facet_fields": ["category", "price", ...]
# }
```
