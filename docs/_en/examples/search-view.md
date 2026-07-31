---
title: "SearchView"
nav_order: 244
---

# SearchView

`SearchView` integrates a `DataSource` with Whoosh indexing. It discovers schema, validates the source, builds the index, and supports incremental refresh.

## Basic Usage

```python
from whoosh_modern.views import SearchView
from whoosh_modern.data_sources.sql import SQLSource
import sqlite3

conn = sqlite3.connect("benchmark/benchmark_data.db")
source = SQLSource(
    connection=conn,
    query="SELECT * FROM reuters_articles",
    incremental_field="article_date",
    id_field="id",
)

view = SearchView(
    name="reuters",
    source=source,
)

# Build index (discovers schema, validates, populates)
ix = view.build("indexdir")
```

## Incremental Refresh

```python
# Rebuild from scratch
count = view.reindex()

# Incremental refresh (only changed docs)
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
```

## Field Overrides

```python
from whoosh.fields import TEXT, NUMERIC

view = SearchView(
    name="custom",
    source=source,
    fields={
        "title": TEXT(stored=True),
        "price": NUMERIC(sortable=True),
    },
)
```

## Strict Mode

```python
view = SearchView(
    name="strict",
    source=source,
    strict=True,  # Raise ValidationError on any failure
)
```
