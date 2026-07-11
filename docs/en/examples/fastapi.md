---
title: "FastAPI Integration"
parent: "Exemples"
nav_order: 4
---

# FastAPI Integration

Minimal working FastAPI service backed by Whoosh-NG.

## Installation

```bash
pip install whoosh-ng[api] fastapi uvicorn
```

## App

```python
from fastapi import FastAPI
from whoosh import index
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser
from whoosh_fastapi import WhooshFastAPI

app = FastAPI()

schema = Schema(title=TEXT(stored=True), content=TEXT)
ix = index.create_in("indexdir", schema)

api = WhooshFastAPI(ix)
api.register_search_endpoint("/search", "content")
api.register_index_endpoint("/documents", schema)
```

## Scripted Bulk Load

```python
from fastapi import FastAPI
from whoosh import index
from whoosh.fields import Schema, TEXT, ID
from whoosh.writing import BufferedWriter

app = FastAPI()
ix = index.open_dir("indexdir")

@app.post("/load")
def load_documents(docs: list[dict]):
    with BufferedWriter(ix, period=30, limit=50) as w:
        for doc in docs:
            w.add_document(**doc)
    return {"loaded": len(docs)}
```

## Query Endpoint

```python
from fastapi import FastAPI
from whoosh import index
from whoosh.qparser import QueryParser

app = FastAPI()
ix = index.open_dir("indexdir")

@app.get("/search")
def search(q: str):
    with ix.searcher() as searcher:
        parser = QueryParser("content", ix.schema)
        parsed = parser.parse(q)
        results = searcher.search(parsed)
        return [hit.fields() for hit in results]
```
