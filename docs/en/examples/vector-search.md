---
color_scheme: dark
title: "Vector Search"
parent: "Examples"
nav_order: 5
---

# Vector Search with Whoosh‑NG

This example shows how to enable **semantic/vector search** using the optional `vector` extra. We index document embeddings and perform k-nearest neighbour (k-NN) search.

## 1. Install Optional Dependencies

```bash
pip install "whoosh-ng[vector]" numpy
```

## 2. Schema with a Vector Field

```python
from whoosh.fields import Schema, TEXT, ID, VECTOR
from whoosh.vector import VectorField

schema = Schema(
    doc_id=ID(stored=True, unique=True),
    title=TEXT(stored=True),
    content=TEXT,
    embedding=VECTOR(stored=True, dim=128),  # 128-dimensional embedding
)
```

## 3. Indexing Vectors

```python
import numpy as np
from whoosh import index

shutil.rmtree("vector_index", ignore_errors=True)
ix = index.create_in("vector_index", schema)

# Simulate embeddings (in practice, use a model like SentenceTransformer)
documents = [
    {"doc_id": "doc1", "title": "Python Basics", "content": "Learn Python programming fundamentals."},
    {"doc_id": "doc2", "title": "Advanced Python", "content": "Deep dive into Python decorators and metaclasses."},
    {"doc_id": "doc3", "title": "Data Science", "content": "Pandas and NumPy for data analysis."},
]

# Generate random embeddings for demo
np.random.seed(42)
embeddings = {d["doc_id"]: np.random.rand(128).astype(np.float32) for d in documents}

with ix.writer() as w:
    for doc in documents:
        w.add_document(
            doc_id=doc["doc_id"],
            title=doc["title"],
            content=doc["content"],
            embedding=embeddings[doc["doc_id"]].tobytes(),
        )
    w.commit()
```

## 4. Vector Search with NumpyProvider

```python
from whoosh_modern.vector import VectorField
from whoosh_modern.vector.numpy_provider import NumpyProvider
from whoosh_modern.vector.plugin import VectorPlugin
from whoosh.plugins.manager import PluginManager

# Register the vector plugin
VectorPlugin().register(PluginManager())

# Create provider and add vectors
provider = NumpyProvider()
for doc_id, vec in embeddings.items():
    provider.add([(doc_id, vec.tolist())])

# Search: find 2 most similar docs to a query vector
query_vec = embeddings["doc1"]  # use doc1's embedding as query
hits = provider.search(query_vec, k=2)

for hit in hits:
    print(f"doc_id={hit.doc_id}, score={hit.score:.3f}")
```

## 5. Using VectorField for Serialization

```python
from whoosh.vector import VectorField

vf = VectorField(dimension=128, name="embedding")

# Convert list to bytes for storage
values = [0.1, 0.2, 0.3, 0.4] + [0.0] * 124  # 128 values
raw = vf.vector_to_bytes(values)

# Restore from bytes
restored = vf.bytes_to_vector(raw)
print(restored == tuple(values))  # True
```

## 6. Key Takeaways

- Install with `pip install whoosh-ng[vector]` to get `whoosh_modern.vector`.
- `VECTOR` field stores raw bytes; use `VectorField` to convert to/from Python lists.
- `NumpyProvider` implements cosine similarity via dot product.
- Register the plugin via `VectorPlugin().register(manager)` or use `PluginManager.load_plugins()`.
- Use `filter_ids` in `provider.search()` to restrict to a subset of documents.