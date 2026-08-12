---
title: "Configuration Engine"
sidebar_position: 215
---

# Configuration Engine

Whoosh-NG includes a **Configuration Engine** (`ConfigEngine`) that loads,
validates, and merges application configuration from YAML or JSON files. It is
built on Pydantic models and supports hierarchical layering so that environment-
specific overrides can cleanly extend base settings.

## Core concepts

### Pydantic models

All configuration is expressed through typed Pydantic models:

- `WhooshNGConfig` — top-level application config
- `FieldConfig` — per-field indexing options
- `SearchConfig` / `FuzzyConfig` / `RankingConfig` / `AIConfig`
- `DataSourceConfigModel` — data source connection and sync settings
- `StorageConfigModel` — storage backend selection

### Loaders

Two loaders are provided:

- `load_yaml(path)` — parse a YAML file into a `dict`
- `load_json(path)` — parse a JSON file into a `dict`
- `load_config(path)` — auto-detect format from extension and return a validated
  `WhooshNGConfig`

### Hierarchical merging

`ConfigEngine.load(path, priority=...)` and `ConfigEngine.merge(overrides, priority=...)`
stack configuration sources with the following precedence (highest wins):

1. `runtime`
2. `instance`
3. `application`
4. `language`

Invalid ``priority`` values raise ``ValueError`` immediately, so misconfigured
layers cannot silently affect the merge order.

Merging is deep: nested dictionaries are merged recursively. Scalar values and
lists are **replaced entirely** by the override values; lists are NOT appended
or combined. For example, a base config with ``{"plugins": ["a", "b"]}``
overridden by ``{"plugins": ["c"]}`` produces ``{"plugins": ["c"]}``, not
``{"plugins": ["a", "b", "c"]}``. If additive list merging is required, handle
it at the application level before calling :meth:`ConfigEngine.merge`.

> [!WARNING]
> **List replacement behavior**: When merging configurations, lists are
> **completely overwritten** by higher-priority layers. They are not appended,
> concatenated, or deduplicated. This is an intentional design choice that
> ensures explicit control over list contents across layers and avoids
> unpredictable merged states. If you need additive behavior (e.g., extending
> a list of plugins or middlewares), perform the merge logic in your application
> code before passing the final dictionary to :meth:`ConfigEngine.merge`.

## Quick start

```python
from whoosh_modern.config import ConfigEngine

engine = ConfigEngine()
engine.load("whoosh-ng.yml", priority="application")
engine.load("whoosh-ng.local.yml", priority="instance")
engine.merge({"search": {"fuzzy": {"distance": 5}}}, priority="runtime")

config = engine.get_config()
print(config.index)
print(config.fields["title"].stemming)
print(config.search.fuzzy.distance)
```

## YAML example

```yaml
# whoosh-ng.yml
index: products
languages:
  default: fr
fields:
  title:
    type: text
    language: fr
    stemming: true
    stored: true
  price:
    type: numeric
    sortable: true
search:
  fuzzy:
    enabled: true
    distance: 2
storage:
  type: file
  path: ./index
```

## JSON example

```json
{
  "index": "products",
  "languages": {"default": "en"},
  "fields": {
    "title": {"type": "text", "language": "en", "stemming": true},
    "price": {"type": "numeric", "sortable": true}
  },
  "search": {"fuzzy": {"enabled": true, "distance": 2}},
  "storage": {"type": "file", "path": "./index"}
}
```

## Complete YAML examples

### Minimal config

```yaml
# whoosh-ng.yml
index: my_index
fields:
  title:
    type: text
    stored: true
storage:
  type: file
  path: ./index
```

### E-commerce catalog with CSV source

```yaml
# whoosh-ng.yml
index: products
fields:
  sku:
    type: text
    stored: true
    unique: true
  name:
    type: text
    language: fr
    stemming: true
    stored: true
  description:
    type: text
    language: fr
    stemming: true
  price:
    type: numeric
    sortable: true
    faceted: true
  category:
    type: text
    faceted: true
  published_at:
    type: datetime
    faceted: true
search:
  fuzzy:
    enabled: true
    distance: 2
data_source:
  type: csv
  path: Datas/products.csv
  delimiter: ","
  encoding: utf-8
  id_field: sku
storage:
  type: file
  path: ./index
```

### Layered configuration (base + instance + runtime)

```yaml
# whoosh-ng.yml  (application layer)
index: app
fields:
  title:
    type: text
    stemming: true
search:
  fuzzy:
    enabled: true
    distance: 2
storage:
  type: file
  path: ./index
```

```yaml
# whoosh-ng.local.yml  (instance layer)
index: app-staging
storage:
  type: file
  path: ./index-staging
```

```python
# runtime override in code
engine = ConfigEngine()
engine.load("whoosh-ng.yml", priority="application")
engine.load("whoosh-ng.local.yml", priority="instance")
engine.merge({"search": {"fuzzy": {"distance": 3}}}, priority="runtime")
app = engine.build()
```

## Complete JSON examples

### Minimal config

```json
{
  "index": "my_index",
  "fields": {
    "title": {"type": "text", "stored": true}
  },
  "storage": {"type": "file", "path": "./index"}
}
```

### Full-stack config with SQL source and hybrid storage

```json
{
  "index": "customers",
  "fields": {
    "customer_id": {"type": "numeric", "stored": true, "sortable": true},
    "first_name": {"type": "text", "language": "en", "stemming": true, "stored": true},
    "last_name": {"type": "text", "language": "en", "stemming": true, "stored": true},
    "city": {"type": "text", "language": "en", "stemming": true, "stored": true},
    "country": {"type": "text", "stored": true},
    "signup_date": {"type": "datetime", "faceted": true}
  },
  "search": {
    "fuzzy": {"enabled": true, "distance": 2},
    "highlight": {"enabled": true, "fragment_size": 200}
  },
  "data_source": {
    "type": "sql",
    "connection_string": "sqlite:///benchmark_data.db",
    "query": "SELECT * FROM customers",
    "id_field": "customer_id"
  },
  "storage": {
    "type": "hybrid",
    "local_path": "./index-cache",
    "remote": {
      "type": "s3",
      "bucket": "my-bucket",
      "prefix": "whoosh-indexes/"
    }
  }
}
```

## Using ConfigEngine.build() for zero-code setup

```python
from whoosh_modern.config import ConfigEngine

engine = ConfigEngine()
engine.load("whoosh-ng.yml")
app = engine.build()
app.build()

# Add documents through the index writer
writer = app.index.writer()
writer.add_document(title="Premier cours de Python", body="...")
writer.add_document(title="Whoosh-NG avancé", body="...")
writer.commit()

# Or use the source directly for streaming/batch indexing
for doc in app._source.iter_documents():
    with app.index.writer() as writer:
        writer.add_document(**doc)

results = app.search("python")
```

## Module reference

| Module | Purpose |
|---|---|
| `whoosh_modern.config.models` | Pydantic models for validation |
| `whoosh_modern.config.loader` | YAML / JSON file loaders |
| `whoosh_modern.config.engine` | `ConfigEngine` with hierarchical merging |

## See Also

- [Storage Providers](storage-providers.md) — Storage backends configurable via `StorageConfigModel`
- [Data Sources](data-sources.md) — `DataSourceConfigModel` and provider configuration
