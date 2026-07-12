---
color_scheme: dark
title: "API Moderne"
nav_order: 10
parent: "Référence API"
lang: fr
---

# API Moderne

Features introduites dans Whoosh-NG 4.0.

## VectorField

```python
from whoosh.fields import VectorField

champ = VectorField(dimensions=384, metric="cosine", stored=False)
```

### Attributs

| Attribut | Type | Description |
|----------|------|-------------|
| `dimensions` | int | Dimensions du vecteur |
| `metric` | str | Métrique de similarité (`"cosine"`, `"euclidean"`, `"dot"`) |
| `stored` | bool | Stocker le vecteur |
| `provider` | str | Provider à utiliser |

**Exemple:**
```python
schema = Schema(
    titre=TEXT(stored=True),
    embedding=VectorField(dimensions=384, metric="cosine")
)
```

## VectorSearch

```python
class whoosh.vector.VectorSearch(searcher)
```

Moteur de recherche vectorielle.

### Méthodes

| Méthode | Description |
|---------|-------------|
| `vs.search(fieldname, vector, limit, **kwargs)` | Recherche par similarité vectorielle |
| `vs.index_vectors(fieldname, vectors)` | Indexer des vecteurs |
| `vs.save()` | Sauvegarde l'index vectoriel |
| `vs.load()` | Charge l'index vectoriel |

**Exemple:**
```python
with ix.searcher() as s:
    vs = s.vector_search("embedding", query_vector, limit=10)
    for hit in vs:
        print(hit["titre"], hit.score)
```

## AutocompleteField

```python
from whoosh_modern.autocomplete import AutocompleteField

champ = AutocompleteField(
    prefix_length=3,
    max_prefix=50,
    stored=False
)
```

## FastAPI Integration

```python
from whoosh_fastapi import WhooshFastAPI

app = FastAPI()
api = WhooshFastAPI(ix)

api.register_search_endpoint("/search", "content")
api.register_index_endpoint("/documents", schema)
```

## SchemaBuilder

API fluent pour construire des schémas:

```python
from whoosh.fields import SchemaBuilder, TEXT, ID, NUMERIC

schema = (
    SchemaBuilder()
    .field("titre", TEXT(stored=True))
    .field("chemin", ID(stored=True, unique=True))
    .field("contenu", TEXT)
    .field("note", NUMERIC(float, stored=True))
    .build()
)
```

## Monitoring

```python
from whoosh.middleware import MetricsMiddleware, MiddlewareChain
from whoosh.middleware.integration import apply_middleware_to_searcher

chain = MiddlewareChain([MetricsMiddleware()])
searcher = apply_middleware_to_searcher(ix.searcher(), chain.middlewares)

metrics = chain.get_metrics()
print(metrics)
# {"documents_indexed": 10, "searches_executed": 5}
```
