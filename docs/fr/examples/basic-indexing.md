---
title: "Indexation de base"
parent: "Exemples"
lang: fr
nav_order: 1
---

# Indexation de base

Exemples pour indexer des documents dans Whoosh-NG.

## Créer l'index

```python
from whoosh import index
from whoosh.fields import Schema, TEXT, ID, NUMERIC

schema = Schema(
    title=TEXT(stored=True),
    path=ID(stored=True, unique=True),
    content=TEXT,
    rating=NUMERIC(float, stored=True)
)
```

## Indexer un document

```python
from whoosh import index

ix = index.create_in("indexdir", schema)

with ix.writer() as writer:
    writer.add_document(
        title="Premier document",
        content="Bonjour le monde avec whoosh",
        path="/1",
        rating=4.5
    )
    writer.commit()
```

## Bulk Insert

```python
documents = [
    {"title": "Doc 1", "content": "Premier document", "path": "/1", "rating": 3.0},
    {"title": "Doc 2", "content": "Deuxième document", "path": "/2", "rating": 4.0},
]

with ix.writer() as writer:
    for doc in documents:
        writer.add_document(**doc)
    writer.commit()
```

## Mise à jour

```python
with ix.writer() as writer:
    writer.update_document(
        path="/1",
        title="Titre mis à jour",
        content="Contenu mis à jour",
        rating=4.8
    )
    writer.commit()
```

## Suppression

```python
from whoosh.query import Term

with ix.writer() as writer:
    writer.delete_by_term("path", "/2")
    writer.commit()
```
