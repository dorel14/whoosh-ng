---
title: 'Documents imbriqués (Nested)'
sidebar_position: 100
---

# Documents imbriqués (Nested)

Ce guide couvre l'indexation et la recherche de structures de documents
hiérarchiques imbriqués (par exemple, un document parent contenant plusieurs
documents enfants) en utilisant les fonctionnalités de relation
parent-enfant de Whoosh.

## Définition des documents imbriqués

Vous pouvez indexer des documents parents qui contiennent des documents
enfants en utilisant un champ parent et des champs enfants :

```python
from whoosh import fields, index

schema = fields.Schema(
    type=fields.ID(sortable=True),
    title=fields.TEXT(stored=True),
    content=fields.TEXT,
    section_name=fields.ID,
    section_content=fields.TEXT,
)
```

Le champ `type` distingue les documents parents des documents enfants.

## Indexation des documents imbriqués

Utilisez `IndexWriter.add_all()` avec un générateur qui produit les
documents parents et enfants groupés ensemble :

```python
writer = ix.writer()
writer.add_all([
    parent_doc,
    child_doc_1,
    child_doc_2,
    parent_doc_2,
    child_doc_3,
])
```

Les documents parents ont `type="parent"` et les documents enfants ont
`type="child"`.

## Recherche dans les documents imbriqués

### Recherche-enfants, correspondance-parents

Recherchez dans les documents enfants et faites correspondre leurs
documents parents :

```python
from whoosh.query import Every, Term
from whoosh.sorting import NestedParent

# Correspondre tous les documents parents
parents = NestedParent(Term("type", "parent"))
q = Every("section_content", "hello")
results = searcher.search(q, sortedby=parents)
```

### Recherche-parents, correspondance-enfants

Recherchez les documents parents dont les enfants correspondent :

```python
from whoosh.sorting import NestedChildren

# Correspondre les documents parents qui ont des enfants correspondant à la requête
parent_results = searcher.search(child_query, groupedby=NestedChildren(parent_matcher, child_matcher))
```

## Relations parent-enfant lors de l'indexation

Lors de l'écriture des documents, utilisez le paramètre `parent` pour
lier les enfants aux parents :

```python
writer.add_document(type="parent", title="Chapitre 1", _key="chapter1")
writer.add_document(type="child", section_name="Section 1.1",
                    section_content="...", parent="chapter1")
writer.add_document(type="child", section_name="Section 1.2",
                    section_content="...", parent="chapter1")
```

## Accès aux résultats imbriqués

Pour récupérer les correspondances d'enfants aux côtés des résultats
parents, utilisez la méthode `expand` sur les résultats :

```python
results = searcher.search(parent_query)
expanded = results.expand_child("section")
```

## Facettisation imbriquée

Combinez les relations parent-enfant avec la facettisation en utilisant
`NestedParent` et `NestedChildren` comme facets :

```python
parent_facet = NestedParent(FieldFacet("type"))
results = searcher.search(query, groupedby=parent_facet)
```

## Considérations de performance

- Les jointures parent-enfant sont plus coûteuses que les recherches
  sur des documents plats.
- Utilisez l'option `childperm` du chercheur pour limiter le nombre de
  permutations examinées.
- Considérez si la structure hiérarchique est nécessaire lors de la
  requête, ou si les documents peuvent être aplatis lors de l'indexation.
