---
title: "API Moderne"
nav_order: 190
lang: fr
---

# API Moderne

Sources de données, découverte de schéma, facettes, validation, middleware et SearchView.

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
```

### RESTSource

```python
source = RESTSource(
    url="https://api.example.com/v2/products",
    pagination="page",
    page_size=50,
)
schema = source.discover_schema()
docs = list(source.iter_documents())
```

## SchemaDiscovery

```python
from whoosh_modern.schema_discovery import SchemaDiscovery

schema = SchemaDiscovery.from_result_set(columns)
schema = SchemaDiscovery.from_sample(docs)
id_field = SchemaDiscovery.detect_id_field(dict(schema))
```

## FacetManager

```python
from whoosh_modern.facets import FacetManager

manager = FacetManager(schema)
facets = manager.get_facets()
manager.set_manual_override("price", {"type": "range"})
```

## ValidationFramework

```python
from whoosh_modern.validation import ValidationFramework, ValidationResult

validator = ValidationFramework()
results = validator.validate(source)
```

## Middleware Pipeline

```python
from whoosh_modern.middleware import MiddlewarePipeline, RetryMiddleware, LoggingMiddleware

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
results = view.validate()
```
