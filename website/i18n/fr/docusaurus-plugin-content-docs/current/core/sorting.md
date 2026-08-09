---
title: 'Sorting'
sidebar_position: 26
---

> **Note de traduction** : Cette page n'est pas encore traduite en français.
> Le contenu anglais est affiché ci-dessous en attendant la traduction.

<!-- Creez une version francaise de ce fichier et supprimez ce message. -->


# Sorting

The `whoosh.sorting` module provides facets and sort-key computation for ordering and grouping search results.

## Quick start

```python
from whoosh import sorting

# Sort by a field
results = searcher.search(query, sortedby="date")

# Sort descending
results = searcher.search(query, sortedby=sorting.FieldFacet("price", reverse=True))
```

For the full API reference, see [Sorting API](/api/sorting).
