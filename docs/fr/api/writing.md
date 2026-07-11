---
title: "API Écriture"
nav_order: 3
parent: "Référence API"
lang: fr
---

# API Écriture

Écrire, mettre à jour et supprimer des documents via l'interface `IndexWriter`.

## IndexWriter

```python
class whoosh.writing.IndexWriter
```

Classe de base pour l'écriture de documents.

### Contexte manager

```python
with ix.writer() as writer:
    writer.add_document(title="Bonjour", content="Monde")
    # commit() appelé automatiquement
```

### Méthodes

#### `add_document(**fields)`

Ajoute un document.

**Kwargs spéciaux:**
- `_stored_<nom_champ>`: Valeur stockée alternative
- `_<nom_champ>_boost`: Boost spécifique au champ
- `_boost`: Boost global du document

---

#### `update_document(**fields)`

Met à jour/remplace un document. Utilise les champs `unique` pour trouver les documents existants.

---

#### `delete_document(docnum, delete=True)`

Supprime par numéro de document.

---

#### `delete_by_term(fieldname, text) -> int`

Supprime tous les documents avec le terme dans le champ.

**Retourne:**
- `int`: Nombre de documents supprimés.

---

#### `delete_by_query(q, searcher=None) -> int`

Supprime les documents correspondant à la requête.

---

#### `commit(mergetype=None, optimize=False, merge=True)`

Commit les changements sur disque.

**Args:**
- `mergetype`: Fonction de fusion personnalisée
- `optimize`: Fusionner tous les segments en un seul
- `merge`: Si False, ne pas fusionner les segments existants

---

#### `cancel()`

Annule les changements et libère le verrou.

---

#### `add_field(fieldname, fieldtype, **kwargs)`

Ajoute un champ (avant d'ajouter des documents).

---

#### `remove_field(fieldname)`

Supprime un champ du schéma.

---

#### `searcher(**kwargs) -> Searcher`

Retourne un searcher (pour lecture pendant la session d'écriture).

---

#### `reader(**kwargs) -> IndexReader`

Retourne un reader pour l'état actuel.

---

#### `group()`

Context manager pour grouper des documents dans un segment.

## SegmentWriter

Implémentation concrète d'IndexWriter.

## AsyncWriter

Writer threaded qui réessaie automatiquement en cas de contention.

```python
from whoosh.writing import AsyncWriter

writer = AsyncWriter(index, delay=0.25, writerargs={})
```

## BufferedWriter

Buffer les documents en mémoire et commit périodiquement.

```python
from whoosh.writing import BufferedWriter

writer = BufferedWriter(
    index,
    period=60,      # Max secondes entre commits
    limit=100       # Max documents par commit
)
```

## Politiques de fusion

```python
from whoosh.writing import NO_MERGE, MERGE_SMALL, OPTIMIZE, CLEAR

writer.commit(mergetype=NO_MERGE)
writer.commit(mergetype=MERGE_SMALL)
writer.commit(mergetype=OPTIMIZE)
writer.commit(mergetype=CLEAR)
```

## Exceptions

### IndexingError

```python
class whoosh.writing.IndexingError(Exception)
```

Levée quand une opération d'indexation échoue.
