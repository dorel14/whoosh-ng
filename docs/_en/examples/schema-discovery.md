---
title: "Schema Discovery"
nav_order: 241
---

# Schema Discovery

Schema discovery infers Whoosh `Schema` from data source results. It operates on **actual result metadata and sample documents**, not SQL syntax.

## How It Works

### From Result Sets

```python
from whoosh_modern.schema_discovery import SchemaDiscovery
import sqlite3

conn = sqlite3.connect("benchmark/benchmark_data.db")
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(reuters_articles)")
columns = [(row[1], row[2]) for row in cursor.fetchall()]
# [("id", "INTEGER"), ("article_date", "TEXT"), ("headline", "TEXT"), ...]

schema = SchemaDiscovery.from_result_set(columns)
```

### From Sample Documents

```python
from whoosh_modern.data_sources.sql import SQLSource

source = SQLSource(
    connection=conn,
    query="SELECT * FROM reuters_articles LIMIT 10",
)

# Get a few documents
docs = list(source.iter_documents())[:10]

# Infer schema from document values
schema = SchemaDiscovery.from_sample(docs)
```

### Detect ID Field

```python
id_field = SchemaDiscovery.detect_id_field(dict(schema))
# Returns "id" if an ID field is found, otherwise None
```

## SQL Type Mapping

| SQL Type | Whoosh Field |
|----------|-------------|
| `VARCHAR`, `TEXT`, `CHAR`, `STRING_AGG` | `TEXT` |
| `INTEGER`, `BIGINT`, `SMALLINT`, `COUNT`, `SUM`, `AVG`, `MIN`, `MAX` | `NUMERIC` |
| `FLOAT`, `DOUBLE`, `DECIMAL` | `NUMERIC` |
| `BOOLEAN` | `BOOLEAN` |
| `DATE`, `TIMESTAMP` | `DATETIME` |
| `UUID` | `ID` |
| `JSON`, `ENUM` | `KEYWORD` |

## Duplicate Column Detection

`from_result_set` raises `SchemaDiscoveryError` on duplicate column names.

```python
columns = [
    ("id", "INTEGER"),
    ("headline", "TEXT"),
    ("id", "INTEGER"),  # Duplicate!
]

try:
    schema = SchemaDiscovery.from_result_set(columns)
except SchemaDiscoveryError as e:
    print(f"Duplicate column: {e.field}")
```

Use explicit SQL aliases to avoid duplicates:

```sql
SELECT
    p.id AS product_id,
    c.id AS category_id
FROM products p
JOIN categories c ON p.category_id = c.id
```
