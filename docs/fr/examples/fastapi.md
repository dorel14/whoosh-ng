---
color_scheme: dark
title: "Intégration FastAPI"
parent: "Exemples"
nav_order: 4
lang: fr
---

# Intégration FastAPI

Un service REST complet exposant la recherche Whoosh‑NG via HTTP.

## 1. Installation

```bash
pip install "whoosh-ng[api]" fastapi uvicorn
```

## 2. Schéma et création de l’index

```python
from whoosh import index
from whoosh.fields import Schema, TEXT, ID

schema = Schema(
    id=ID(stored=True, unique=True),
    title=TEXT(stored=True),
    content=TEXT,
)

ix = index.create_in("docs_index", schema)

# Indexer des documents
with ix.writer() as w:
    w.add_document(id="1", title="Python Basics", content="Learn Python fundamentals.")
    w.add_document(id="2", title="FastAPI Tutorial", content="REST API with FastAPI.")
    w.commit()
```

## 3. Service REST avec create_app

```python
from fastapi import FastAPI
from whoosh_fastapi import create_app

app = create_app(ix, prefix="/api/v1")

# L’application fournit automatiquement :
# - GET  /api/v1/health   → {"status": "ok"}
# - POST /api/v1/search   → {"hits": [...], "total": N}
# - GET  /api/v1/autocomplete?q=... → {"suggestions": [...]}
```

## 4. Démarrer le serveur

```bash
uvicorn main:app --reload --port 8000
```

## 5. Requêtes de test

```bash
# Vérification de santé
curl http://localhost:8000/api/v1/health

# Recherche
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"q": "python"}'

# Autocomplétion
curl "http://localhost:8000/api/v1/autocomplete?q=py"
```

## 6. Indexation en lot

```python
from fastapi import FastAPI
from whoosh.writing import BufferedWriter

ix = index.open_dir("docs_index")

@app.post("/api/v1/index")
async def index_docs(docs: list[dict]):
    with BufferedWriter(ix, period=30, limit=50) as w:
        for doc in docs:
            w.add_document(**doc)
    return {"indexed": len(docs)}
```

## Points clés

- `create_app()` de `whoosh_fastapi` expose `/health`, `/search` et `/autocomplete`.
- Les appels bloquants s’exécutent hors boucle d’événements.
- Utilisez `BufferedWriter` pour l’indexation en masse.