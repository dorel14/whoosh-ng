---
color_scheme: dark
title: "Intégration FastAPI"
parent: "Exemples"
nav_order: 4
lang: fr
---

# Intégration FastAPI

Un service FastAPI complet exposant la recherche Whoosh‑NG via HTTP.

## 1. Installation

```bash
pip install "whoosh-ng[api]" fastapi uvicorn
```

## 2. Créer l’index

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

## 3. Service REST

```python
# main.py
from fastapi import FastAPI, Query
from typing import Optional
from whoosh import index
from whoosh.qparser import QueryParser
from whoosh_fastapi import create_app

ix = index.open_dir("docs_index")

# Utiliser l’aide
app = create_app(ix, prefix="/api/v1")

# Option B: endpoints manuels
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 4. Démarrer le serveur

```bash
uvicorn main:app --reload --port 8000
```

## 5. Tester l’API

```bash
# Vérification de santé
curl http://localhost:8000/api/v1/health

# Recherche
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"q": "python recherche"}'
```

## Points clés

- `create_app()` de `whoosh_fastapi` fournit les endpoints `/health`, `/search` et `/autocomplete`.
- Tous les appels bloquants s’exécutent hors boucle d’événements via `run_sync`.
