---
title: "Data Sources"
nav_order: 240
---

# Data Sources

Whoosh-NG provides a flexible data source layer for indexing documents from SQL databases, REST APIs, and custom data providers.

## DataSource Protocol

All data sources implement the `DataSource` protocol, which defines the interface for querying, schema discovery, and metadata retrieval.

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

### Capability Protocols

| Protocol | Description |
|----------|-------------|
| `DataSource` | Base protocol: name, schema, iteration, metadata |
| `IncrementalDataSource` | Supports `iter_changes(since)` |
| `AsyncDataSource` | Async document streaming via `aiter_documents()` |
| `RefreshableDataSource` | `refresh()` support |
| `CountableDataSource` | `document_count()` |
| `MetadataDataSource` | `metadata()` |

---

## SQLSource

`SQLSource` connects to SQL databases and yields documents from query results.

### Basic Usage

```python
from whoosh_modern.data_sources import SQLSource
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

SQLSource uses `PRAGMA table_info` for schema discovery. Always use column aliases in JOINs.

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

---

## RESTSource

`RESTSource` fetches documents from REST APIs with pagination and authentication.

### Basic Usage

```python
from whoosh_modern.data_sources import RESTSource

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