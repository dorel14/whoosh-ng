---
title: "Modern API"
nav_order: 190
---

# Modern API

Vector search, autocomplete, model indexing, and other advanced features.

## VectorField

```python
class whoosh.fields.VectorField(
    dimensions: int,
    metric: str = "cosine",
    provider: str = "numpy",
    stored: bool = False
)
```

Embedding vector field.

---

### VectorProvider

```python
class whoosh.vector.base.VectorProvider
```

Base class for vector providers.

#### Methods

##### `add_vector()`

```python
provider.add_vector(doc_id, embedding: list[float])
```

Index a vector.

##### `search()`

```python
results = provider.search(query_embedding, limit=10)
```

Search vectors.

### Built-in Providers

#### NumpyProvider

```python
from whoosh.vector.numpy_provider import NumpyProvider

provider = NumpyProvider()
```

Pure NumPy cosine similarity. Best for small indexes.

---

#### HNSWProvider

```python
from whoosh.vector.hnsw_provider import HNSWProvider

provider = HNSWProvider(dimensions=384, metric="cosine")
```

Hierarchical Navigable Small World. Fast ANN for large indexes.

---

#### FaissProvider

```python
from whoosh.vector.faiss_provider import FaissProvider
```

Facebook AI Similarity Search. Very large indexes.

---

#### QdrantProvider

```python
from whoosh.vector.qdrant_provider import QdrantProvider
```

Distributed vector DB integration.

---

## Autocomplete API

### AutocompleteProvider

```python
class whoosh_modern.autocomplete.base.AutocompleteProvider
```

Base class for autocomplete providers.

#### Methods

##### `suggest()`

```python
suggestions = provider.suggest(
    prefix: str,
    limit: int = 5,
    fuzzy: int = 0
) -> list[str]
```

Get autocomplete suggestions.

---

### Built-in Providers

#### EdgeNgramProvider

```python
from whoosh_modern.autocomplete.edge_ngram import EdgeNgramProvider

provider = EdgeNgramProvider(searcher, fieldname)
```

Prefix completion using edge n-grams.

---

#### NgramProvider

```python
from whoosh_modern.autocomplete.ngram import NgramProvider

provider = NgramProvider(searcher, fieldname)
```

Infix completion using n-grams.

---

## Model Indexing API

### ModelIndex

```python
from whoosh_modern.models import ModelIndex

idx = ModelIndex(Book)
schema = idx.schema
doc = idx.to_whoosh_document(instance)
```

Auto-maps Python models to Whoosh schemas.

#### Supported model types

- Dataclasses (`dataclasses.is_dataclass`)
- Pydantic v2 (`BaseModel`)
- SQLAlchemy (`__mapper__`)
- SQLModel (`SQLModel` subclasses)
- msgspec (`msgspec.Struct`)
- Plain classes with `__annotations__`

#### Type mappings

| Python type | Whoosh field |
|-------------|--------------|
| `str` | `TEXT` |
| `int` / `float` | `NUMERIC` |
| `bool` | `BOOLEAN` |
| `datetime` / `date` | `DATETIME` |
| `Decimal` | `NUMERIC(int, decimal_places=2)` |
| `Enum` | `KEYWORD` |
| `bytes` | `KEYWORD` (hex-encoded) |
| `list[str]` | `KEYWORD` |

### SearchField and SearchOptions

```python
from whoosh_modern.models import SearchField, SearchOptions

class Book:
    title: str = SearchField(fulltext=True, stored=True, analyzer="Simple")
    count: int = SearchField(sortable=True)
```

### AutoIndexer

```python
from whoosh_modern.models import AutoIndexer

auto = AutoIndexer(ix, on_error="raise")
auto.register(Book)
auto.index(instance)
auto.remove(instance)
await auto.index_async(instance)
await auto.remove_async(instance)
```

Automatic indexing with SQLAlchemy event hooks.

---

## Plugins

### VectorPlugin

```python
from whoosh_modern.vector.plugin import VectorPlugin
```

Registers vector providers and adds vector_search to searcher.

### AutocompletePlugin

```python
from whoosh_modern.autocomplete.plugin import AutocompletePlugin
```

Registers autocomplete providers.
