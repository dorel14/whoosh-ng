---
title: "Vector Search"
sidebar_position: 60
---

# Vector Search

Module: `whoosh_modern.vector`
Version: 2.1.0

Whoosh-NG supports semantic search through vector embeddings. This guide covers setting up and using vector fields.

## Concept

Vector search lets you find documents based on semantic similarity rather than exact keyword matches. You embed documents and queries into a high-dimensional space, then find nearest neighbors.

```
Query embedding  ----\
                      >--- Cosine Similarity ---> Ranked results
Document embedding ---/
```

## Setup

### Define Schema

```python
from whoosh.fields import Schema, TEXT, VectorField

schema = Schema(
    title=TEXT(stored=True),
    content=TEXT,
    embedding=VectorField(dimensions=384)  # e.g., all-MiniLM-L6-v2
)
```

## Providers

Whoosh-NG includes multiple vector backends:

| Provider | Description | Use Case |
|----------|-------------|----------|
| `NumpyProvider` | Pure NumPy, cosine similarity | Small to medium indexes |
| `HNSWProvider` | Hierarchical navigable small world | Large indexes, fast ANN |
| `FaissProvider` | Facebook AI Similarity Search | Very large indexes |
| `QdrantProvider` | Qdrant vector DB | Distributed |

### NumpyProvider (Default)

```python
from whoosh.vector import NumpyProvider

provider = NumpyProvider()
provider.add_vector(doc_id, embedding)
results = provider.search(query_embedding, limit=10)
```

## Indexing with Vectors

### Generate Embeddings

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

embeddings = model.encode([
    "First document content",
    "Second document content"
])
```

### Write Documents

```python
with ix.writer() as writer:
    writer.add_document(
        title="Doc 1",
        content="Python is great",
        embedding=embeddings[0].tolist()
    )
    writer.commit()
```

## Searching with Vectors

### Hybrid Search (Keyword + Vector)

```python
from whoosh.searching import Searcher
from whoosh.vector import VectorProvider

with ix.searcher() as searcher:
    # Semantic search component
    query_embedding = model.encode(["Python tutorial"])[0]
    vector_results = searcher.vector_search(
        "embedding", query_embedding, limit=20
    )

    # Keyword search component
    keyword_query = QueryParser("content", schema).parse("Python")
    keyword_results = searcher.search(keyword_query, limit=20)

    # Combine (e.g., RRF fusion)
    final_results = fuse_results(vector_results, keyword_results)
```

### Pure Vector Search

```python
with ix.searcher() as searcher:
    query_embedding = model.encode(["search query"])[0]
    results = searcher.vector_search(
        "embedding",
        query_embedding,
        limit=10,
        metric="cosine"  # or "euclidean", "dot"
    )
```

## VectorField Options

```python
embedding_field = VectorField(
    dimensions=384,      # Required: embedding dimension
    metric="cosine",     # Similarity metric: cosine, euclidean, dot
    provider="hnsw"      # Provider name from registry
)
```

## Indexing Stream

```python
from whoosh.vector.indexing import VectorIndexer

indexer = VectorIndexer(ix)
indexer.add_document(
    title="Doc",
    content="Content",
    embedding=embedding.tolist()
)
indexer.commit()
```

## Similarity Metrics

| Metric | Description | Range |
|--------|-------------|-------|
| `cosine` | Cosine similarity | [0, 1] (higher is more similar) |
| `euclidean` | Euclidean distance | [0, inf) (lower is more similar) |
| `dot` | Dot product | [-inf, inf] (higher is more similar) |

## Best Practices

1. **Normalize embeddings**: Use cosine similarity with normalized vectors
2. **Choose provider wisely**: Numpy for &lt;100k vectors, HNSW/Faiss for larger
3. **Hybrid search**: Combine vector and keyword search for best results
4. **Cache embeddings**: Pre-compute and store to avoid recomputation
5. **Batch indexing**: Index vectors in batches for efficiency

## Vector Provider Integration in the Pipeline

The vector search system integrates through Whoosh's plugin registry and segment
format. The provider is stored in the index segment and resolved at search time.

### Architecture

```text
┌─────────────────────────────────────────────────────────────────────┐
│  Registration (startup)                                            │
│                                                                     │
│  VectorPlugin.register(PluginManager)                              │
│    └── VectorRegistry.register("numpy", NumpyProvider(), owner)     │
│                                                                     │
│  The provider is now available for any VECTOR field                │
│  that specifies provider="numpy"                                   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Indexation                                                         │
│                                                                     │
│  VECTOR(dimensions=384, provider="numpy")                          │
│       │                                                             │
│       ▼                                                             │
│  PerDocWriter.add_vector_items(fieldname, field, items)            │
│       │                                                             │
│       ▼                                                             │
│  Segment file contains:                                            │
│    - vector bytes (raw)                                            │
│    - provider name ("numpy")                                        │
│    - metric ("cosine")                                              │
│       │                                                             │
│       ▼                                                             │
│  writer.commit() → segments written to disk                        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Search                                                          │
│                                                                     │
│  searcher.vector_search("embedding", query_vec, k=10)              │
│       │                                                             │
│       ▼                                                             │
│  Whoosh core reads segment                                         │
│    └── retrieves provider name ("numpy")                            │
│       │                                                             │
│       ▼                                                             │
│  VectorRegistry.get("numpy")                                        │
│       │                                                             │
│       ▼                                                             │
│  NumpyProvider.search(query_vec, k, filter_ids)                    │
│       │                                                             │
│       ▼                                                             │
│  VectorHit[] sorted by cosine similarity                           │
└─────────────────────────────────────────────────────────────────────┘
```

### Full indexing flow

```python
from whoosh import index, fields
from whoosh_modern.vector.plugin import VectorPlugin
from whoosh.plugins.manager import PluginManager
from whoosh_modern.storage import FileStorage
import numpy as np

# 1. Register vector plugin (startup)
manager = PluginManager()
VectorPlugin().register(manager)

# 2. Define schema with VECTOR field
schema = fields.Schema(
    title=fields.TEXT(stored=True),
    embedding=fields.VECTOR(dimensions=384, provider="numpy", stored=True),
)

# 3. Create index (storage determines where segments live)
ix = index.create_in("indexdir", schema)

# 4. Index documents with vectors
np.random.seed(42)
embeddings = {
    "doc1": np.random.rand(384).astype(np.float32).tolist(),
    "doc2": np.random.rand(384).astype(np.float32).tolist(),
}

with ix.writer() as writer:
    for doc_id, vec in embeddings.items():
        writer.add_document(
            title=f"Document {doc_id}",
            embedding=vec,
        )
    writer.commit()
    # Whoosh core serializes vectors to segment files
    # Provider name "numpy" is stored in the segment
```

### Full search flow

```python
from whoosh.qparser import QueryParser
import numpy as np

with ix.searcher() as searcher:
    # 1. Keyword search
    qp = QueryParser("title", schema)
    keyword_results = searcher.search(qp.parse("Document"))

    # 2. Vector search
    query_vec = np.random.rand(384).astype(np.float32).tolist()
    vector_results = searcher.vector_search(
        "embedding",
        query_vec,
        limit=10,
    )

    # 3. Hybrid: combine both
    # Example: Reciprocal Rank Fusion (RRF)
    def rrf(results_list, k=60):
        scores = {}
        for results in results_list:
            for rank, hit in enumerate(results):
                doc_id = hit.doc_id if hasattr(hit, "doc_id") else hit["doc_id"]
                scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)

    combined = rrf([keyword_results, vector_results])
```

### Standalone usage (no schema)

```python
from whoosh_modern.vector import NumpyProvider

# Create provider directly
provider = NumpyProvider()

# Add vectors
provider.add([
    ("doc1", [0.1, 0.2, 0.3]),
    ("doc2", [0.4, 0.5, 0.6]),
])

# Search
query_vec = [0.1, 0.2, 0.3]
hits = provider.search(query_vec, k=5)

for hit in hits:
    print(f"doc_id={hit.doc_id}, score={hit.score:.4f}")
```

### Provider resolution chain

When `searcher.vector_search()` is called, Whoosh core:

1. Reads the `VECTOR` field configuration from the schema
2. Opens the segment file containing the vector data
3. Extracts the provider name stored in the segment (e.g., `"numpy"`)
4. Looks up the provider in `VectorRegistry`
5. Calls `provider.search(query_vector, k, filter_ids)`
6. Returns `list[VectorHit]`

If the provider is not registered, the search fails with a registry miss. This
is why `VectorPlugin().register(manager)` (or manual registration) is required
at startup.

## See Also

- [Provider Integration Guide](provider-integration.md) — Complete pipeline guide for all providers
- [Middleware Guide](middleware-pipeline.md) — Pipeline hooks and provider adapters
