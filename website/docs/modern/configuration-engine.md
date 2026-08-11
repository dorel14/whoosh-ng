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

Merging is deep: nested dictionaries are merged recursively, while scalar values
and lists are replaced entirely.

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

## Using ConfigEngine with SearchApplication

```python
from whoosh_modern import SearchApplication
from whoosh_modern.config import ConfigEngine
from whoosh_modern.data_sources import CSVSource

engine = ConfigEngine()
engine.load("whoosh-ng.yml")
config = engine.get_config()

source = CSVSource(
    path="products.csv",
    delimiter=",",
    encoding=config.data_source.encoding if config.data_source else "utf-8",
)

app = SearchApplication(
    source=source,
    index_name=config.index,
)
app.build()
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
