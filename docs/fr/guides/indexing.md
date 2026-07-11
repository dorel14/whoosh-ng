---
title: "Indexation"
nav_order: 23
parent: "Guides"
lang: fr
---

# Indexation

Guide pour ajouter, mettre à jour et supprimer des documents.

## Ouvrir un writer

```python
from whoosh import index

ix = index.open_dir("indexdir")

# Writer basique
writer = ix.writer()

# Writer avec options
writer = ix.writer(
    timeout=10.0,
    delay=0.1,
    limitmb=128,
    compound=True
)
```

## Ajouter des documents

```python
with ix.writer() as writer:
    writer.add_document(
        title="Premier document",
        content="Bonjour le monde",
        path="/doc1",
        tags=["python", "recherche"]
    )
    writer.commit()
```

## Mettre à jour

```python
with ix.writer() as writer:
    writer.update_document(
        path="/doc1",
        content="Contenu mis à jour"
    )
```

## Supprimer

```python
# Par numéro de document
writer.delete_document(docnum=42)

# Par terme
writer.delete_by_term("path", "/doc1")

# Par requête
from whoosh.query import Term
q = Term("tags", "deprecated")
writer.delete_by_query(q)

writer.commit()
```

## Bonnes pratiques

- Utilisez `with ix.writer() as writer:` pour le nettoyage automatique
- Commutez par lots pour de meilleures performances
- Utilisez `BufferedWriter` en environnement multi-processus
- Libérez toujours le verrou avec `commit()` ou `cancel()`
