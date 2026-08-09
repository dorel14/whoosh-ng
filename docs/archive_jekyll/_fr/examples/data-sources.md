---
title: "Sources de données"
nav_order: 253
lang: fr
---

# Sources de données

Whoosh-NG fournit une couche de sources de données flexible pour l'indexation de documents à partir de bases de données SQL, d'API REST, d'API GraphQL, de fichiers et d'autres fournisseurs.

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

### Protocoles de capacités

| Protocole | Description |
|----------|-------------|
| `DataSource` | Protocole de base : nom, schéma, itération, métadonnées |
| `IncrementalDataSource` | Supporte `iter_changes(since)` |
| `AsyncDataSource` | Diffusion asynchrone via `aiter_documents()` |
| `RefreshableDataSource` | Support de `refresh()` |
| `CountableDataSource` | `document_count()` |
| `MetadataDataSource` | `metadata()` |
| `ObservableDataSource` | Callbacks d'observation pour les changements de documents |

---

## SQLSource

`SQLSource` se connecte aux bases de données SQL et restitue les documents depuis les résultats de requête, avec pooling de connexions automatique.

### Utilisation de base

```python
from whoosh_modern.data_sources.sql import SQLSource
import sqlite3

conn = sqlite3.connect("mydb.db")
source = SQLSource(
    connection=conn,
    query="SELECT * FROM products",
)

schema = source.discover_schema()
for doc in source.iter_documents():
    print(doc["title"], doc["price"])

count = source.document_count()
```

### Pooling de connexions

```python
from whoosh_modern.data_sources.sql import SQLSource

source = SQLSource(
    connection="sqlite:///mydb.db",
    query="SELECT * FROM products",
    pool_size=10,
    pool_recycle=3600,
)
```

### GROUP BY

```python
source = SQLSource(
    connection=conn,
    query="""
        SELECT category, COUNT(*) as doc_count,
               AVG(price) as avg_price
        FROM products GROUP BY category
    """,
)
```

### JOINs avec alias

```python
source = SQLSource(
    connection=conn,
    query="""
        SELECT p.id AS product_id, p.name AS product_name,
               c.name AS category_name
        FROM products p
        JOIN categories c ON p.category_id = c.id
    """,
)
```

### Synchronisation incrémentale

```python
from datetime import datetime

source = SQLSource(
    connection=conn,
    query="SELECT * FROM articles",
    incremental_field="updated_at",
    id_field="id",
)

for doc in source.iter_changes(since=datetime(2025, 1, 1)):
    print(doc["id"], doc["updated_at"])
```

### SQLAlchemySource

```python
from whoosh_modern.data_sources.sqlalchemy_ds import SQLAlchemySource
from sqlalchemy import create_engine

engine = create_engine("postgresql://user:pass@localhost/mydb")
source = SQLAlchemySource(
    engine=engine,
    query="SELECT * FROM articles",
    incremental_field="updated_at",
    id_field="id",
)
```

### PeeweeSource

```python
from whoosh_modern.data_sources.peewee_ds import PeeweeSource
from peewee import SqliteDatabase

db = SqliteDatabase("mydb.db")
source = PeeweeSource(
    database=db,
    model=MyArticleModel,
    fields=["id", "title", "content"],
)
```

### TortoiseSource (async)

```python
from whoosh_modern.data_sources.tortoise_ds import TortoiseSource

source = TortoiseSource(
    model="myapp.models.Article",
    fields=["id", "title", "content"],
)
```

---

## RESTSource

`RESTSource` récupère les documents depuis des API REST avec pagination et authentification.

### Utilisation de base

```python
from whoosh_modern.data_sources.rest import RESTSource

source = RESTSource(
    url="https://api.example.com/v2/products",
    method="GET",
    headers={"Authorization": "Bearer your_token"},
    pagination="page",
    page_size=50,
)

schema = source.discover_schema()
for doc in source.iter_documents():
    print(doc["name"], doc["price"])
```

### Stratégies de pagination

| Stratégie | Paramètres |
|----------|-----------|
| `page` | `?page=N&size=M` |
| `offset` | `?offset=N&limit=M` |
| `cursor` | `?cursor=XYZ&size=M` |

### Authentification

```python
# Bearer token
source = RESTSource(
    url="https://api.example.com/data",
    headers={"Authorization": "Bearer your_token"},
)

# API key
source = RESTSource(
    url="https://api.example.com/data",
    headers={"X-API-Key": "your_api_key"},
)

# Basic auth
import base64
creds = base64.b64encode(b"user:pass").decode()
source = RESTSource(
    url="https://api.example.com/data",
    headers={"Authorization": f"Basic {creds}"},
)
```

### Document Path

Pour les réponses API imbriquées :

```python
source = RESTSource(
    url="https://api.example.com/api/v2/products",
    document_path="data.results",
    pagination="page",
)
```

---

## GraphQLSource

```python
from whoosh_modern.data_sources.graphql import GraphQLSource

source = GraphQLSource(
    url="https://api.example.com/graphql",
    query="""
        query GetProducts($limit: Int!, $offset: Int!) {
            products(limit: $limit, offset: $offset) {
                id
                name
                price
            }
        }
    """,
    pagination="offset",
    page_size=100,
    headers={"Authorization": "Bearer your_token"},
)
```

---

## Sources de fichiers

### FastCSVSource

```python
from whoosh_modern.data_sources.fast_csv import FastCSVSource

source = FastCSVSource(
    file_path="data/products.csv",
    id_field="id",
    incremental_field="updated_at",
)
```

### JSONSource

```python
from whoosh_modern.data_sources.json import JSONSource

source = JSONSource(file_path="data/products.json")
# ou fichier JSONL
source = JSONSource(file_path="data/logs.jsonl", format="jsonl")
```

### ParquetSource

```python
from whoosh_modern.data_sources.parquet_ds import ParquetSource

source = ParquetSource(
    file_path="data/large_dataset.parquet",
    engine="pyarrow",
    batch_size=1000,
)
```

### PandasSource

```python
from whoosh_modern.data_sources.pandas_ds import PandasSource
import pandas as pd

df = pd.read_csv("data/products.csv")
source = PandasSource(dataframe=df)
```

### PolarsSource

```python
from whoosh_modern.data_sources.polars_ds import PolarsSource
import polars as pl

df = pl.read_csv("data/products.csv")
source = PolarsSource(dataframe=df)
```

---

## DataSourceConfig

Pour une configuration programmatique :

```python
from whoosh_modern.data_sources.config import DataSourceConfig

config = DataSourceConfig(
    source_type="sql",
    connection="sqlite:///mydb.db",
    query="SELECT * FROM products",
    id_field="id",
    incremental_field="updated_at",
    mapping={"db_title": "title"},
    exclude=["description_long"],
)

source = config.create_source()
```

### Sources de données disponibles

| Classe | Type | Dépendances |
|-------|------|-------------|
| `SQLSource` | Bases SQL | `sqlite3` (stdlib) |
| `SQLAlchemySource` | SQLAlchemy | `sqlalchemy` |
| `RESTSource` | API REST | aucune (stdlib `urllib`) |
| `GraphQLSource` | API GraphQL | aucune (stdlib `urllib`) |
| `FastCSVSource` | Fichiers CSV | aucune |
| `JSONSource` | JSON/JSONL | aucune |
| `ParquetSource` | Parquet | `pyarrow` ou `pandas` |
| `PandasSource` | DataFrames pandas | `pandas` |
| `PolarsSource` | DataFrames Polars | `polars` |
| `PeeweeSource` | ORM Peewee | `peewee` |
| `TortoiseSource` | ORM Tortoise | `tortoise-orm` |
| `PydanticSource` | Modèles Pydantic | `pydantic` |
