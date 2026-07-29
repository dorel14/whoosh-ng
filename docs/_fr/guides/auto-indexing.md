---
title: "Auto-indexation"
nav_order: 31
lang: fr
---

# Auto-indexation

Whoosh-NG fournit `AutoIndexer` pour maintenir automatiquement un index Whoosh en synchronisation avec vos modèles de données.

## Vue d'ensemble

`AutoIndexer` maintient un registre de modèles et de leurs schémas Whoosh correspondants. Il peut :

- **Indexer** des instances de modèle dans un index Whoosh
- **Supprimer** des instances par leur champ ID
- **Se connecter** aux événements SQLAlchemy pour une synchronisation automatique
- **Gérer les erreurs** avec des stratégies configurables

## Utilisation basique

```python
from whoosh_modern.models import AutoIndexer, ModelIndex
from whoosh.filedb.filestore import RamStorage

# Créer un index Whoosh
storage = RamStorage()
schema = ModelIndex(Book).schema
ix = storage.create_index(schema)

# Créer l'auto-indexeur
auto = AutoIndexer(ix, on_error="raise")

# Enregistrer un modèle
auto.register(Book)

# Indexer une instance
book = Book(title="Bonjour", year=2024)
auto.index(book)

# Supprimer par ID
auto.remove(book)
```

## Gestion des erreurs

Le paramètre `on_error` contrôle ce qui se passe lorsque l'indexation échoue :

- `"raise"` (défaut) : relève l'exception
- `"log"` : journalise l'erreur et continue
- `"skip"` : ignore silencieusement l'erreur

```python
auto = AutoIndexer(ix, on_error="log")
```

## Intégration SQLAlchemy

Pour les modèles SQLAlchemy, `AutoIndexer` enregistre automatiquement des écouteurs d'événements :

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from whoosh_modern.models import register_sqlalchemy_model

engine = create_engine("sqlite:///app.db")
Base = DeclarativeBase()

class Book(Base):
    __tablename__ = "books"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]

Base.metadata.create_all(engine)

# Enregistrer avec AutoIndexer
auto = AutoIndexer(ix)
auto.register(Book)

# Toute opération de session SQLAlchemy se synchronise automatiquement :
# - after_insert -> index.document()
# - after_update -> index.document()
# - after_delete -> remove.document()
```

## Support asynchrone

Pour les applications asynchrones, utilisez `index_async` et `remove_async` :

```python
import asyncio

async def main():
    book = Book(title="Async", year=2024)
    await auto.index_async(book)
    await auto.remove_async(book)

asyncio.run(main())
```

Ces méthodes exécutent l'indexation synchrone dans un thread de travail via `asyncio.to_thread()` pour ne pas bloquer la boucle d'événements.

## Référence API

### `AutoIndexer(index, on_error="raise")`

- `index` : une instance Whoosh `Index`
- `on_error` : stratégie de gestion d'erreur (`"raise"`, `"log"`, `"skip"`)

### Méthodes

- `register(model) -> ModelIndex` : enregistrer une classe modèle et retourner son `ModelIndex`
- `index(instance)` : indexer une instance de modèle
- `remove(instance)` : supprimer une instance de modèle par son champ ID
- `index_async(instance)` : version async de `index`
- `remove_async(instance)` : version async de `remove`

### Fonctions utilitaires

```python
from whoosh_modern.models import index_document, remove_document

# Indexation ponctuelle sans créer d'AutoIndexer
index_document(ix, book_instance, on_error="raise")
remove_document(ix, book_instance, on_error="raise")
```
