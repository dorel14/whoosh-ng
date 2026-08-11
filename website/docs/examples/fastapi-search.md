---
title: "FastAPI Integration"
sidebar_position: 255
---

# FastAPI Integration

A complete, runnable FastAPI service exposing Whoosh‑NG search via HTTP.

## 1. Install

```bash
pip install whoosh-ng[api] fastapi uvicorn
```

## 2. Create the index

```python
# setup_index.py
import json
from whoosh import index
from whoosh.fields import Schema, TEXT, ID

schema = Schema(
    id=ID(stored=True, unique=True),
    title=TEXT(stored=True),
    content=TEXT,
)

ix = index.create_in("docs_index", schema)

with ix.writer() as w:
    for doc in json.load(open("documents.json")):
        w.add_document(
            id=doc["id"],
            title=doc["title"],
            content=doc["content"],
        )
    w.commit()
```

## 3. REST API Service

```python
# main.py
from fastapi import FastAPI, Query
from typing import Optional
from whoosh import index
from whoosh.qparser import QueryParser
from whoosh_fastapi import create_app

ix = index.open_dir("docs_index")

# Option A: Use the helper
app = create_app(ix, prefix="/api/v1")

# Option B: Manual endpoints
# app = FastAPI(title="Document Search API", version="1.0.0")
#
# @app.get("/api/v1/health")
# async def health():
#     return {"status": "ok"}
#
# @app.post("/api/v1/search")
# async def search(q: str = Query(...), limit: int = 10):
#     with ix.searcher() as s:
#         parser = QueryParser("content", ix.schema)
#         results = s.search(parser.parse(q), limit=limit)
#         return {"hits": [dict(h) for h in results], "total": len(results)}
#
# @app.get("/api/v1/documents/{doc_id}")
# async def get_doc(doc_id: str):
#     with ix.searcher() as s:
#         from whoosh.query import Term
#         results = s.search(Term("id", doc_id))
#         if results:
#             return dict(results[0])
#         return {"error": "not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 4. Run the server

```bash
uvicorn main:app --reload --port 8000
```

## 5. Test the API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Search
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"q": "python search"}'

# Get document by ID
curl http://localhost:8000/api/v1/documents/doc1
```

## 6. Bulk Indexing Endpoint

```python
# Add to main.py for dynamic indexing
from fastapi import FastAPI
from whoosh.writing import BufferedWriter

@app.post("/api/v1/index")
async def index_docs(docs: list[dict]):
    with BufferedWriter(ix, period=30, limit=50) as w:
        for doc in docs:
            w.add_document(**doc)
    return {"indexed": len(docs)}
```

## 7. Alternative: WhooshFastAPI Class

For more control, use the `WhooshFastAPI` class directly:

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

## Key points

- `create_app()` from `whoosh_fastapi` provides `/health`, `/search`, `/autocomplete`, and `/suggest` endpoints.
- All blocking calls run off the event loop via `run_sync`.
- Use `BufferedWriter` for high-throughput indexing via POST.
- `WhooshFastAPI` class offers per-endpoint registration for custom integrations.

## WebSocket autocomplete

Pass an ``AutocompleteProvider`` to ``create_app`` to enable the WebSocket
autocomplete endpoint. The client sends JSON messages with a ``q`` key and
receives ``{"suggestions": [...]}`` responses over a persistent connection.

```python
from whoosh_modern.autocomplete import EdgeNgramAutocomplete
from whoosh_fastapi import create_app

autocomplete = EdgeNgramAutocomplete(ix)
app = create_app(ix, prefix="/api/v1", autocomplete=autocomplete)
```

Client example using JavaScript:

```javascript
const ws = new WebSocket("ws://localhost:8000/api/v1/autocomplete/ws");
ws.onmessage = (event) => console.log(JSON.parse(event.data));
ws.send(JSON.stringify({ q: "pyth" }));
// {"suggestions": ["python", "pythagorean"]}
```

When no autocomplete provider is configured, the endpoint returns an empty
suggestions list instead of raising.
