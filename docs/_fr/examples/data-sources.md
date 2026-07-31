---
title: "Sources de données"
nav_order: 240
lang: fr
---

# Sources de données

Whoosh-NG fournit une couche de sources de données flexible pour l'indexation de documents à partir de bases de données SQL, d'API REST et de fournisseurs personnalisés.

## Protocole DataSource

Toutes les sources implémentent le protocole `DataSource` :

```python
from whoosh_modern.data_sources import DataSource

class DataSource(Protocol):
    @property
    def name(self) -> str: ...

    def discover_schema(self) -> Schema: ...
    def iter_documents(self) -> Iterator[Document]: ...
    def document_count(self) -> int: ...
    def metadata(self) -> Mapping[str, Any]: ...
```

## SQLSource

```python
from whoosh_modern.data_sources import SQLSource
import sqlite3

conn = sqlite3.connect("mydb.db")
source = SQLSource(
    connection=conn,
    query="SELECT * FROM products",
    incremental_field="updated_at",
    id_field="id",
)

schema = source.discover_schema()
count = source.document_count()
docs = list(source.iter_documents())
```

### GROUP BY

```python
source = SQLSource(
    connection=conn,
    query="""
        SELECT category, COUNT(*) as doc_count
        FROM products
        GROUP BY category
    """,
)
```

### JOINs avec alias

```python
source = SQLSource(
    connection=conn,
    query="""
        SELECT p.id AS product_id, c.name AS category_name
        FROM products p
        JOIN categories c ON p.category_id = c.id
    """,
)
```

### Synchronisation incrémentale

```python
from datetime import datetime

for doc in source.iter_changes(since=datetime(2025, 1, 1)):
    print(doc["id"], doc["updated_at"])
```

## RESTSource

```python
from whoosh_modern.data_sources import RESTSource

source = RESTSource(
    url="https://api.example.com/v2/products",
    pagination="page",
    page_size=50,
    headers={"Authorization": "Bearer token"},
)

schema = source.discover_schema()
docs = list(source.iter_documents())
```

### Stratégies de pagination

| Stratégie | Paramètres |
|----------|-----------|
| `page` | `?page=N&size=M` |
| `offset` | `?offset=N&limit=M` |
| `cursor` | `?cursor=XYZ&size=M` |

```python
source = RESTSource(
    url="https://api.example.com/data",
    pagination="cursor",
    page_size=100,
)
```
