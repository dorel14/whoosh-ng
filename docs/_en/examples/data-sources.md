---
title: "Data Sources"
nav_order: 240
---

# Data Sources

Whoosh-NG provides a flexible data source layer for indexing documents from SQL databases, REST APIs, GraphQL APIs, file-based formats, and custom data providers.

## DataSource Protocol

All data sources implement the `DataSource` protocol, which defines the interface for querying, schema discovery, and metadata retrieval.

```python
from whoosh_modern.data_sources import DataSource

class DataSource(Protocol):
    @property
    def name(self) -> str: ...

    def discover_schema(self) -> Schema: ...
    def iter_documents(self) -> Iterator[Document]: ...
    def stream_batches(self, batch_size: int = 1000) -> Iterator[list[dict[str, Any]]]: ...
    def health_check(self) -> bool: ...
```

### Capability Protocols

| Protocol | Description |
|----------|-------------|
| `DataSource` | Base protocol: name, schema, iteration, metadata |
| `IncrementalDataSource` | Supports `iter_changes(since)` |
| `AsyncDataSource` | Async document streaming via `aiter_documents()` |
| `RefreshableDataSource` | `refresh()` support |
| `CountableDataSource` | `document_count()` |
| `MetadataDataSource` | `metadata()` |
| `ObservableDataSource` | Observer callbacks for document changes |

---

## SQLSource

`SQLSource` connects to SQL databases and yields documents from query results with automatic connection pooling.

### Basic Usage

```python
from whoosh_modern.data_sources.sql import SQLSource
import sqlite3

conn = sqlite3.connect("mydb.db")
source = SQLSource(
    connection=conn,
    query="SELECT * FROM products",
)

# Discover schema from result-set metadata
schema = source.discover_schema()

# Iterate documents
for doc in source.iter_documents():
    print(doc["title"], doc["price"])

# Get metadata
meta = source.metadata()
# {"type": "sql", "query": "SELECT * FROM products", ...}

# Get document count
count = source.document_count()
```

### Connection Pooling (SQLSource)

Connection pooling is supported via `pool_size` for long-running processes:

```python
from whoosh_modern.data_sources.sql import SQLSource

source = SQLSource(
    connection="sqlite:///mydb.db",  # URL or connection object
    query="SELECT * FROM products",
    pool_size=10,          # Max connections in pool
)
```

### GROUP BY Aggregation

```python
source = SQLSource(
    connection=conn,
    query="""
        SELECT category, COUNT(*) as doc_count,
               AVG(price) as avg_price
        FROM products
        GROUP BY category
    """,
)

# Each aggregated row becomes a document
for doc in source.iter_documents():
    print(doc["category"], doc["doc_count"], doc["avg_price"])
```

### JOINs with Column Aliases

`SQLSource` uses result-set metadata for schema discovery. Always use column aliases in JOINs.

```python
source = SQLSource(
    connection=conn,
    query="""
        SELECT
            p.id AS product_id,
            p.name AS product_name,
            c.name AS category_name
        FROM products p
        JOIN categories c ON p.category_id = c.id
    """,
)
```

### Incremental Sync

```python
from datetime import datetime

source = SQLSource(
    connection=conn,
    query="SELECT * FROM articles",
    incremental_field="updated_at",
    id_field="id",
)

# Get documents changed since a timestamp
for doc in source.iter_changes(since=datetime(2025, 1, 1)):
    print(doc["id"], doc["updated_at"])
```

### SQLAlchemySource

For SQLAlchemy users, use `SQLAlchemySource` which supports engine-based connection management:

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

schema = source.discover_schema()
```

### PeeweeSource

For Peewee ORM users:

```python
from whoosh_modern.data_sources.peewee_ds import PeeweeSource
from peewee import SqliteDatabase

db = SqliteDatabase("mydb.db")
source = PeeweeSource(
    database=db,
    model=MyArticleModel,
    fields=["id", "title", "content"],
)

schema = source.discover_schema()
```

### TortoiseSource

For Tortoise ORM users (async):

```python
from whoosh_modern.data_sources.tortoise_ds import TortoiseSource

source = TortoiseSource(
    model="myapp.models.Article",
    fields=["id", "title", "content"],
)

schema = source.discover_schema()
count = source.document_count()
```

---

## RESTSource

`RESTSource` fetches documents from REST APIs with pagination and authentication.

### Basic Usage

```python
from whoosh_modern.data_sources.rest import RESTSource

source = RESTSource(
    url="https://api.example.com/v2/products",
    method="GET",
    headers={"Authorization": "Bearer your_token"},
    pagination="page",
    page_size=50,
)

# Discover schema from first page
schema = source.discover_schema()

# Iterate all documents (handles pagination automatically)
for doc in source.iter_documents():
    print(doc["name"], doc["price"])

# Get document count
count = source.document_count()
```

### Pagination Strategies

| Strategy | Parameters | Behavior |
|----------|-----------|----------|
| `page` | `?page=N&size=M` | Fetches page N with M items per page |
| `offset` | `?offset=N&limit=M` | Fetches M items starting at N |
| `cursor` | `?cursor=XYZ&size=M` | Follows `next_cursor` in response |

```python
# Page-based pagination
source = RESTSource(
    url="https://api.example.com/articles",
    pagination="page",
    page_size=50,
)

# Offset-based pagination
source = RESTSource(
    url="https://api.example.com/records",
    pagination="offset",
    page_size=100,
)

# Cursor-based pagination
source = RESTSource(
    url="https://api.example.com/feed",
    pagination="cursor",
    page_size=100,
)
```

### Authentication

```python
# Bearer token via headers
source = RESTSource(
    url="https://api.example.com/data",
    headers={"Authorization": "Bearer your_token"},
)

# API key via headers
source = RESTSource(
    url="https://api.example.com/data",
    headers={"X-API-Key": "your_api_key"},
)

# Basic auth via headers
import base64
creds = base64.b64encode(b"user:pass").decode()
source = RESTSource(
    url="https://api.example.com/data",
    headers={"Authorization": f"Basic {creds}"},
)
```

### Document Path

For nested API responses, use `document_path` to extract documents:

```python
# API returns: {"data": {"results": [...]}}
source = RESTSource(
    url="https://api.example.com/api/v2/products",
    document_path="data.results",
    pagination="page",
)
```

---

## GraphQLSource

`GraphQLSource` fetches documents from a GraphQL API endpoint:

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
                description
            }
        }
    """,
    pagination="offset",
    page_size=100,
    headers={"Authorization": "Bearer your_token"},
)

schema = source.discover_schema()
for doc in source.iter_documents():
    print(doc["id"], doc["name"])
```

---

## File-Based Data Sources

Whoosh-NG supports indexing from various file formats with optimized readers.

### FastCSVSource

High-performance CSV reader with configurable encoding and delimiter:

```python
from whoosh_modern.data_sources.fast_csv import FastCSVSource

source = FastCSVSource(
    file_path="data/products.csv",
    id_field="id",
    incremental_field="updated_at",
    delimiter=",",
    encoding="utf-8",
)

schema = source.discover_schema()
count = source.document_count()
for doc in source.iter_documents():
    print(doc)
```

### JSONSource

Index from JSON files or JSON Lines (.jsonl) files:

```python
from whoosh_modern.data_sources.json import JSONSource

# JSON array file
source = JSONSource(file_path="data/products.json")

# JSON Lines file (one JSON object per line)
source = JSONSource(
    file_path="data/logs.jsonl",
    format="jsonl",
)

schema = source.discover_schema()
```

### ParquetSource

Index from Parquet files using pyarrow or pandas backend:

```python
from whoosh_modern.data_sources.parquet_ds import ParquetSource

source = ParquetSource(
    file_path="data/large_dataset.parquet",
    engine="pyarrow",  # or "pandas"
    batch_size=1000,
)

schema = source.discover_schema()
```

### PandasSource

Index directly from a pandas DataFrame:

```python
from whoosh_modern.data_sources.pandas_ds import PandasSource
import pandas as pd

df = pd.read_csv("data/products.csv")
source = PandasSource(dataframe=df)

schema = source.discover_schema()
```

### PolarsSource

Index from a Polars DataFrame (faster, lazy evaluation):

```python
from whoosh_modern.data_sources.polars_ds import PolarsSource
import polars as pl

df = pl.read_csv("data/products.csv")
source = PolarsSource(dataframe=df)

schema = source.discover_schema()
```

---

## DataSourceConfig

For programmatic configuration, use `DataSourceConfig` to define data source properties:

```python
from whoosh_modern.data_sources.config import DataSourceConfig

config = DataSourceConfig(
    type="sql",
    connection=conn,
    query="SELECT * FROM products",
    id_field="id",
    incremental_field="updated_at",
)

source = config.create()
schema = source.discover_schema()
```

### Config File Support

Data source configurations can be loaded from dictionaries:

```python
from whoosh_modern.data_sources.config import DataSourceConfig

# From dict
config = DataSourceConfig.from_dict({
    "type": "rest",
    "url": "https://api.example.com/v2/products",
    "pagination": "page",
    "page_size": 50,
})
source = config.create()
```

Supported `type` values: `sql`, `sqlalchemy`, `rest`, `csv`, `json`, `graphql`,
`pydantic`, `pandas`, `polars`, `parquet`, `peewee`, `tortoise`.

### Available Data Sources

| Class | Source Type | Dependencies |
|-------|------------|--------------|
| `SQLSource` | SQLite, PostgreSQL, MySQL | `sqlite3` (stdlib) |
| `SQLAlchemySource` | Any SQLAlchemy-supported DB | `sqlalchemy` |
| `RESTSource` | REST APIs | none (stdlib `urllib`) |
| `GraphQLSource` | GraphQL APIs | none (stdlib `urllib`) |
| `FastCSVSource` | CSV files | none |
| `JSONSource` | JSON/JSONL files | none |
| `ParquetSource` | Parquet files | `pyarrow` or `pandas` |
| `PandasSource` | pandas DataFrames | `pandas` |
| `PolarsSource` | Polars DataFrames | `polars` |
| `PeeweeSource` | Peewee ORM | `peewee` |
| `TortoiseSource` | Tortoise ORM | `tortoise-orm` |
| `PydanticSource` | Pydantic models | `pydantic` |
