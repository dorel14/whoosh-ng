---
color_scheme: dark
title: "Modern API"
nav_order: 10
parent: "API Reference"
---

# Modern API

Vector search, autocomplete, and other advanced features.

## Vector API

### VectorField

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
