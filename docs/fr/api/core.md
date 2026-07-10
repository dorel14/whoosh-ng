---
title: "API Core"
nav_order: 1
parent: "Référence API"
lang: fr
---

# API Core

Gestion des indexes via les fonctions et classes du module `whoosh.index`.

## Fonctions

### create_in

```python
def create_in(dirname, schema, indexname="MAIN", create=True, **kwargs) -> FileIndex
```

Crée un nouvel index dans le répertoire donné.

**Args:**
- `dirname (str)`: Chemin du répertoire.
- `schema (Schema)`: Objet Schema définissant les champs.
- `indexname (str)`: Nom de l'index.
- `create (bool)`: Si True, crée même si existe (efface l'existant).

**Retourne:**
- `FileIndex`: Objet index.

**Exemple:**
```python
from whoosh.index import create_in
index = create_in("indexdir", schema)
```

### open_dir

```python
def open_dir(dirname, indexname="MAIN", readonly=False, **kwargs) -> FileIndex
```

Ouvre un index existant.

**Exemple:**
```python
index = open_dir("indexdir")
```

### exists_in

```python
def exists_in(dirname, indexname="MAIN", **kwargs) -> bool
```

Vérifie si un index valide existe dans le répertoire.

## Classes

### Index

Classe de base pour les objets index.

#### Méthodes principales

| Méthode | Description |
|---------|-------------|
| `writer(**kwargs)` | Retourne un IndexWriter |
| `searcher(**kwargs)` | Retourne un Searcher |
| `reader()` | Retourne un IndexReader |
| `commit()` | Commit via un writer temporaire |
| `optimize()` | Fusionne tous les segments |
| `add_field()` | Ajoute un champ au schéma |
| `remove_field()` | Supprime un champ du schéma |
| `doc_count()` | Nombre de documents |
| `doc_count_all()` | Nombre total (y compris supprimés) |

## Exceptions

### LockError

Levée quand l'index est verrouillé par un autre writer.

```python
from whoosh.index import LockError

try:
    writer = ix.writer(timeout=5.0)
except LockError:
    print("Index verrouillé, réessayez plus tard")
```

### IndexMissingError

Levée quand l'index n'existe pas.
