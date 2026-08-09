---
title: "Sorting"
sidebar_position: 26
---

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
