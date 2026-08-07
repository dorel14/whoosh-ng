---
title: "Démarrage rapide"
sidebar_position: 2
---

# Démarrage rapide

## Installation

```bash
pip install whoosh-ng
uv pip install whoosh-ng
```

## Exemple basique

```python
from whoosh import index
from whoosh.fields import Schema, TEXT, ID

schema = Schema(id=ID(stored=True), content=TEXT())
ix = index.create_in("indexdir", schema)

with ix.writer() as w:
    w.add_document(id="1", content="hello world")
    w.add_document(id="2", content="goodbye world")

with ix.searcher() as s:
    results = s.search("world")
    for hit in results:
        print(hit["id"], hit.score)
```

## Avec plugins

```bash
pip install whoosh-ng[vector,autocomplete,api]
```

```python
from whoosh.plugins.manager import PluginManager
from whoosh_modern.vector.plugin import VectorPlugin

PluginManager.load_plugins()
```

## Sources de données

```bash
pip install whoosh-ng
```

```python
import sqlite3
from whoosh_modern.data_sources import SQLSource
from whoosh_modern.views import SearchView

# Utiliser les données de benchmark existantes
conn = sqlite3.connect("benchmark/benchmark_data.db")
source = SQLSource(
    connection=conn,
    query="SELECT * FROM reuters_articles",
)

vue = SearchView(name="reuters", source=source)
ix = vue.build("indexdir")
```
