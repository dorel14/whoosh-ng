---
title: "SearchView"
nav_order: 244
---

# SearchView

`SearchView` integrates a `DataSource` with Whoosh indexing. It discovers
schema, validates the source, builds the index, and supports incremental
refresh and schema evolution.

## Basic Usage

```python
from whoosh_modern.views import SearchView
from whoosh_modern.data_sources.sql import SQLSource
import sqlite3

conn = sqlite3.connect("data/articles.db")
source = SQLSource(
    connection=conn,
    query="SELECT * FROM articles",
    incremental_field="updated_at",
    id_field="id",
)

view = SearchView(
    name="articles",
    source=source,
)

# Build index (discovers schema, validates, populates)
ix = view.build("indexdir")
```

## Full Reindex vs Incremental Refresh

```python
# Full reindex (clears and rebuilds the entire index)
count = view.reindex()

# Incremental refresh (only changed documents since last sync)
count = view.refresh()
```

## Validation

```python
# Run validation before building
results = view.validate()
for result in results:
    print(f"Level {result.level}: {'PASS' if result.passed else 'FAIL'}")
    for error in result.errors:
        print(f"  ERROR: {error}")
    for warning in result.warnings:
        print(f"  WARNING: {warning}")
```

Validation levels:
1. **Structural** — DataSource availability, schema detection
2. **Search** — Indexable fields, term vectors, searchable analyzers
3. **Performance** — Performance warnings (e.g., TEXT fields on large datasets)
4. **Runtime** — Sample iteration, type conformance

## Field Overrides

Customize field types after schema discovery:

```python
from whoosh.fields import TEXT, NUMERIC, DATETIME

view = SearchView(
    name="custom",
    source=source,
    fields={
        "title": TEXT(stored=True, phrase=False),
        "price": NUMERIC(int, sortable=True),
        "published": DATETIME(sortable=True),
    },
)
```

## Facets

Configure facet settings:

```python
view = SearchView(
    name="faceted",
    source=source,
    facets={
        "category": {"type": "terms", "limit": 50},
        "price": {"type": "range", "buckets": ["0-100", "100-500", "500+"]},
    },
)
```

## Middleware

Attach middleware to the search pipeline:

```python
from whoosh_modern.views import SearchView
from whoosh_modern.middleware import LoggingMiddleware, RetryMiddleware

view = SearchView(
    name="with_middleware",
    source=source,
    middleware=[
        RetryMiddleware(attempts=3, backoff="exponential"),
        LoggingMiddleware(),
    ],
)
```

## Strict Mode

```python
view = SearchView(
    name="strict",
    source=source,
    strict=True,  # Raise ValidationError on any validation failure
)
```

## Schema Evolution

Add new fields to an existing index without a full reindex:

```python
view = SearchView(name="articles", source=source)
view.build("indexdir")

# Add a new field
view.evolve_schema({
    "new_field": TEXT(stored=True),
})
```

### Schema Version Checking

```python
view = SearchView(name="articles", source=source, schema_version="2.1")
view.build("indexdir")

# Check if the stored schema version matches
if not view.check_schema_version():
    print("Schema version mismatch, consider reindexing")
```
