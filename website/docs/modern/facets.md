---
title: "Facets"
sidebar_position: 65
---

# Facets

Whoosh-NG provides a modern `FacetManager` that auto-discovers facetable
fields from a Whoosh `Schema` and supports manual overrides. All facets
produced are genuine core `FacetType` instances usable directly as
`groupedby=` arguments in `searcher.search()`.

> **Module:** `whoosh_modern.facets`
> **Version:** 3.0.0

## Quickstart

```python
from whoosh.fields import Schema, TEXT, NUMERIC, DATETIME
from whoosh_modern.facets import FacetManager

schema = Schema(
    title=TEXT(stored=True),
    category=TEXT(sortable=True),
    price=NUMERIC(),
    published=DATETIME(),
)

manager = FacetManager(schema)
facets = manager.get_facets()

# Use directly in search
with ix.searcher() as searcher:
    results = searcher.search("query", groupedby=facets)
```

## Auto-discovery rules

`FacetManager` inspects each field type and proposes a default facet:

| Whoosh field type | Facet produced |
|-------------------|----------------|
| `TEXT`, `KEYWORD`, `BOOLEAN`, `ID` | `TermsFacet` |
| `NUMERIC` | `RangeFacet` |
| `DATETIME` | `DateRangeFacet` |

Defaults:
- `TermsFacet` uses `limit=100`
- `RangeFacet` spans `0` to `1000` with `gap=100`
- `DateRangeFacet` spans `1970-01-01` to `2100-01-01` with `gap=365 days`

## TermsFacet

`TermsFacet` is a thin subclass of core `whoosh.sorting.FieldFacet` that
accepts the legacy `limit` and `name` keyword arguments for backward
compatibility.

```python
from whoosh_modern.facets import TermsFacet

facet = TermsFacet("category", limit=50, name="Category")
```

## Manual overrides

```python
manager.set_manual_override("price", {
    "type": "range",
    "start": 0,
    "end": 1000,
    "gap": 100,
})

manager.set_manual_override("category", {
    "type": "terms",
    "limit": 50,
})
```

Manual overrides take precedence over auto-discovered facets.

## Inspection

```python
manager.is_facetable("category")          # True
config = manager.get_facet_config("category")  # {"type": "terms", "limit": 50}
all_configs = manager.get_all_facet_configs()
stats = manager.get_facet_stats()
# {
#   "total_fields": 4,
#   "auto_discovered_facets": 2,
#   "manual_overrides": 1,
#   "total_facets_configured": 3,
#   "facet_fields": ["category", "price", ...]
# }
```

## See Also

- [Storage Providers](/modern/storage-providers) — Persisting faceted indexes
- [Provider Integration](/modern/provider-integration) — Full pipeline guide
