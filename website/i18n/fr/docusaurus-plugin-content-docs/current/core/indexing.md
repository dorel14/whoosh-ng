---
title: "Indexation"
sidebar_position: 20
---

:::info
Suite au renommage de `whoosh-reloaded` en `whoosh-ng`, les nouveaux modules spécifiques à Whoosh-NG se trouvent généralement sous `whoosh_modern`.
Les composants Whoosh core (comme `whoosh.analysis`, `whoosh.index`) restent accessibles directement sous l'espace de noms `whoosh` pour la rétrocompatibilité.
:::

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

## Valeurs stockées vs indexées

Pour les champs qui sont à la fois indexés et stockés, vous pouvez stocker une valeur différente :

```python
writer.add_document(
    title="Title to be indexed",
    _stored_title="Display title to show in results"
)
```

> **Note** : Le préfixe underscore (`_stored_<field>`, `_<field>_boost`) est une
> convention Whoosh pour les overrides par document. Il vous permet de stocker
> une valeur différente pour l'affichage (`_stored_title`) sans modifier ce qui
> est indexé, ou de booster un champ spécifique pour un seul document
> (`_title_boost`) sans affecter le boost au niveau du schéma.

## Boosts de champs

Booster des champs individuels au niveau du document :

```python
writer.add_document(
    title="Important title",
    _title_boost=2.0,   # Double weight for title terms
    content="Body content"
)
```

## Mettre à jour les documents

Utilisez `update_document` pour remplacer les documents correspondant à des champs uniques :

```python
schema = Schema(path=ID(unique=True, stored=True), content=TEXT)
ix = index.create_in("indexdir", schema)

with ix.writer() as writer:
    writer.add_document(path="/doc1", content="Original content")
    writer.commit()

with ix.writer() as writer:
    # Remplace tout document avec path="/doc1"
    writer.update_document(path="/doc1", content="Updated content")
    writer.commit()
```

## Supprimer des documents

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
