---
title: "Vector Search"
nav_order: 29
parent: "Guides"
---

# Vector Search

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
2. **Choose provider wisely**: Numpy for <100k vectors, HNSW/Faiss for larger
3. **Hybrid search**: Combine vector and keyword search for best results
4. **Cache embeddings**: Pre-compute and store to avoid recomputation
5. **Batch indexing**: Index vectors in batches for efficiency
