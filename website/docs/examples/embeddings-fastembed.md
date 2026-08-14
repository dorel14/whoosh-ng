---
title: "Embeddings with FastEmbed"
sidebar_position: 260
---

# Embeddings with FastEmbed

This example shows how to use **FastEmbed** for dense vector embeddings in Whoosh‑NG.

## 1. Install Dependencies

```bash
pip install "whoosh-ng[embeddings]"
```

## 2. Single-Field Vectorization

```python
from whoosh.fields import Schema, TEXT
from whoosh.index import create_in
from whoosh_modern import SearchApplication
from whoosh_modern.data_sources.in_memory import InMemorySource
from whoosh_modern.embeddings import FastEmbedProvider
from whoosh_modern.middleware.embedding import EmbeddingMiddleware

provider = FastEmbedProvider(model_name="BAAI/bge-small-en-v1.5")
source = InMemorySource(
    documents=[
        {"title": "Whoosh-NG", "body": "Modern Python full-text search."},
        {"title": "FastEmbed", "body": "Lightweight embedding models."},
    ],
    schema=Schema(title=TEXT(stored=True), body=TEXT),
)

app = SearchApplication(
    source=source,
    embedding_provider=provider,
    source_field="body",
    target_field="body_vector",
)
app.build("indexdir")
```

## 3. Multi-Field Vectorization

```python
app = SearchApplication(
    source=source,
    embedding_provider=provider,
    embedding_fields=[
        {"source_field": "title", "target_field": "title_vector"},
        {"source_field": "body", "target_field": "body_vector"},
    ],
)
app.build("indexdir")
```

## 4. Inspect Stored Vectors

```python
with app.index.searcher() as searcher:
    for stored in searcher.all_stored_fields():
        print(stored.get("title_vector"))
        print(stored.get("body_vector"))
```

## Notes

- The target vector fields are added to the schema automatically as `VECTOR` fields.
- If a source field is missing or not a string, it is skipped silently.
- Provider errors are swallowed to avoid breaking the indexing pipeline.
