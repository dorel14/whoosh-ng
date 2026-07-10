---
title: "Intégration FastAPI"
parent: "Exemples"
lang: fr
nav_order: 4
---

# Intégration FastAPI

Exemple de service REST indexé par Whoosh-NG.

## Dépendances

```bash
pip install whoosh-ng[api] fastapi uvicorn
```

## Application minimale

```python
from fastapi import FastAPI
from whoosh import index
from whoosh.fields import Schema, TEXT, ID
from whoosh_fastapi import WhooshFastAPI

app = FastAPI()

schema = Schema(title=TEXT(stored=True), content=TEXT)
ix = index.create_in("indexdir", schema)
api = WhooshFastAPI(ix)
api.register_search_endpoint("/search", "content")
```

## Endpoint manuel

```python
from fastapi import FastAPI
from whoosh.qparser import QueryParser

@app.get("/search")
def search(q: str):
    with ix.searcher() as searcher:
        parser = QueryParser("content", ix.schema)
        results = searcher.search(parser.parse(q))
        return [hit.fields() for hit in results]
```

## Chargement en masse

```python
from fastapi import FastAPI
from whoosh.writing import BufferedWriter

@app.post("/load")
def load(docs: list[dict]):
    with BufferedWriter(ix, period=30, limit=50) as w:
        for doc in docs:
            w.add_document(**doc)
    return {"loaded": len(docs)}
```
