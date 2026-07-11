---
title: "Vue d'ensemble API"
nav_order: 0
parent: "Référence API"
lang: fr
---

# Vue d'ensemble API

Cette section fournit une référence complète de l'API publique de Whoosh-NG.

## Modules

| Module | Description |
|--------|-------------|
| `whoosh.index` | Gestion des indexes |
| `whoosh.fields` | Types de champs et schéma |
| `whoosh.writing` | Writers et politiques de fusion |
| `whoosh.searching` | Searcher, Results, collectors |
| `whoosh.query` | Classes de requêtes |
| `whoosh.qparser` | Analyseur de requêtes |
| `whoosh.analysis` | Tokenizers, filtres, analyseurs |
| `whoosh.highlight` | Surbrillance des résultats |
| `whoosh.spelling` | Correction orthographique |
| `whoosh.sorting` | Facettes et tri |
| `whoosh.event_bus` | Système d'événements |
| `whoosh.hooks` | Système de hooks |
| `whoosh.middleware` | Pipeline de middleware |
| `whoosh.plugins` | Système de plugins et registres |
| `whoosh.backends` | Backends de stockage |
| `whoosh.vector` | Providers de recherche vectorielle |
| `whoosh_modern.autocomplete` | Providers d'autocomplétion |
| `whoosh_fastapi` | Intégration FastAPI |

## Référence rapide

### Cycle de vie d'un index

```python
from whoosh.index import create_in, open_dir, exists_in

ix = create_in("indexdir", schema)
ix = open_dir("indexdir")
exists = exists_in("indexdir")
```

### Écriture

```python
with ix.writer() as writer:
    writer.add_document(champ1=val1, champ2=val2)
```

### Lecture

```python
from whoosh.qparser import QueryParser

with ix.searcher() as searcher:
    qp = QueryParser("content", ix.schema)
    q = qp.parse("requête")
    results = searcher.search(q)
```

### Schéma

```python
from whoosh.fields import Schema, TEXT, ID, NUMERIC

schema = Schema(
    titre=TEXT(stored=True),
    chemin=ID(stored=True, unique=True),
    compte=NUMERIC(int, stored=True)
)
```
