---
title: "Modern API"
nav_order: 190
---

# Modern API

Data sources, schema discovery, facets, validation, middleware, and search view.

## DataSource Protocol

```python
from whoosh_modern.data_sources import DataSource, SQLSource, RESTSource
```

### SQLSource

```python
source = SQLSource(
    connection=conn,
    query="SELECT * FROM reuters_articles",
    incremental_field="article_date",
    id_field="id",
)
schema = source.discover_schema()
docs = list(source.iter_documents())
count = source.document_count()
meta = source.metadata()
```

### RESTSource

```python
source = RESTSource(
    url="https://api.example.com/v2/products",
    pagination="page",
    page_size=50,
    headers={"Authorization": "Bearer token"},
)
schema = source.discover_schema()
docs = list(source.iter_documents())
```

## SchemaDiscovery

```python
from whoosh_modern.schema_discovery import SchemaDiscovery

# From column metadata
columns = [("id", "INTEGER"), ("title", "TEXT")]
schema = SchemaDiscovery.from_result_set(columns)

# From sample documents
schema = SchemaDiscovery.from_sample(docs)

# Detect ID field
id_field = SchemaDiscovery.detect_id_field(dict(schema))
```

## FacetManager

```python
from whoosh_modern.facets import FacetManager, TermsFacet, RangeFacet

manager = FacetManager(schema)
facets = manager.get_facets()
config = manager.get_facet_config("category")
stats = manager.get_facet_stats()
manager.set_manual_override("price", {"type": "range", "buckets": [...]})
```

## ValidationFramework

```python
from whoosh_modern.validation import ValidationFramework, ValidationResult

validator = ValidationFramework()
results = validator.validate(source)
```

## Middleware Pipeline

```python
from whoosh_modern.middleware import Middleware, MiddlewarePipeline, RetryMiddleware, LoggingMiddleware

pipeline = MiddlewarePipeline(
    RetryMiddleware(attempts=3, backoff="exponential"),
    LoggingMiddleware(),
)
result = pipeline.execute(operation)
```

## SearchView

```python
from whoosh_modern.views import SearchView

view = SearchView(name="reuters", source=source)
ix = view.build("indexdir")
count = view.reindex()
count = view.refresh()
results = view.validate()
```
