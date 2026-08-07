---
title: "SearchView"
nav_order: 250
lang: fr
---

# SearchView

`SearchView` intègre une source de données avec l'indexation Whoosh.

## Usage basique

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

# Créer l'index
ix = view.build("indexdir")
```

## Rafraîchissement incrémental

```python
# Réindexation complète
count = view.reindex()

# Rafraîchissement incrémental
count = view.refresh()
```

## Validation

```python
results = view.validate()
for result in results:
    print(f"Niveau {result.level}: {'PASS' if result.passed else 'FAIL'}")
```

## Mode strict

```python
view = SearchView(
    name="strict",
    source=source,
    strict=True,  # Lever ValidationError en cas d'échec
)
```
