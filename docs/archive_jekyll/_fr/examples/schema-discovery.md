---
title: "Découverte de schéma"
nav_order: 247
lang: fr
---

# Découverte de schéma

La découverte de schéma infère un schéma Whoosh à partir des métadonnées de résultats ou d'échantillons de documents.

## Depuis les métadonnées de colonnes

```python
from whoosh_modern.schema_discovery import SchemaDiscovery
import sqlite3

conn = sqlite3.connect("benchmark/benchmark_data.db")
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(reuters_articles)")
columns = [(row[1], row[2]) for row in cursor.fetchall()]

schema = SchemaDiscovery.from_result_set(columns)
```

## Depuis des échantillons de documents

```python
from whoosh_modern.data_sources.sql import SQLSource

source = SQLSource(connection=conn, query="SELECT * FROM reuters_articles LIMIT 10")
docs = list(source.iter_documents())[:10]
schema = SchemaDiscovery.from_sample(docs)
```

## Détection du champ ID

```python
id_field = SchemaDiscovery.detect_id_field(dict(schema))
```

## Détection des doublons

`from_result_set` lève `SchemaDiscoveryError` sur les noms de colonnes dupliqués.
