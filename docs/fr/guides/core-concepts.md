---
title: "Concepts fondamentaux"
nav_order: 21
parent: "Prise en main"
lang: fr
---

# Concepts fondamentaux

Whoosh-NG est une bibliothèque de recherche purement Python. Ce guide explique les principaux concepts pour l'utiliser efficacement.

## Architecture

Whoosh-NG suit une architecture en couches :

```text
Application
    ▼
┌─────────────────────────────┐
│       Whoosh-NG Core        │
├─────────────────────────────┤
│ Schema                      │
│ Search Engine               │
│ Plugin Manager              │
│ Registry System             │
│ Middleware Pipeline         │
│ Event Bus                   │
│ Hook System                 │
└─────────────────────────────┘
       ▼
┌─────────────────────────────┐
│           Plugins           │
├─────────────────────────────┤
│ FastAPI                     │
│ Autocomplete                │
│ Vector Search               │
│ PostgreSQL                  │
│ S3                          │
│ Monitoring                  │
│ Admin UI                    │
└─────────────────────────────┘
```

## Composants clés

### Index

Un `Index` est le conteneur de vos documents. Il gère un ou plusieurs segments sur disque.

```python
from whoosh.index import create_in, open_dir

ix = create_in("indexdir", schema)
ix = open_dir("indexdir")
```

### Schema

Le `Schema` définit les champs des documents. Chaque champ a un type qui détermine son indexation et stockage.

```python
from whoosh.fields import Schema, TEXT, ID, NUMERIC

schema = Schema(
    title=TEXT(stored=True),
    path=ID(stored=True, unique=True),
    content=TEXT,
    rating=NUMERIC(float, stored=True)
)
```

### Writer

Un `IndexWriter` permet d'ajouter, modifier et supprimer des documents.

```python
writer = ix.writer()
writer.add_document(title="Bonjour", content="Monde")
writer.commit()
```

### Searcher

Un `Searcher` interroge l'index et retourne des résultats.

```python
with ix.searcher() as s:
    results = s.search("bonjour")
```

### QueryParser

Convertit une chaîne de requête en objet Query.

```python
from whoosh.qparser import QueryParser

qp = QueryParser("content", schema)
query = qp.parse("bonjour monde")
```

## Fonctionnalités modernes

### Système de plugins

Les plugins étendent Whoosh-NG sans modifier le core. Ils peuvent :

- Enregistrer de nouveaux providers vectoriels
- Ajouter des endpoints FastAPI
- Fournir des analyseurs personnalisés
- S'intégrer au pipeline de middleware

```python
from whoosh.plugins.manager import PluginManager

# Auto-découverte depuis les entry points
PluginManager.load_plugins()
```

### Pipeline de middleware

Le middleware intercepte les opérations d'indexation et de recherche :

```python
from whoosh.middleware import Middleware, MiddlewareContext

class LoggingMiddleware(Middleware):
    def before_search(self, context: MiddlewareContext):
        print(f"Recherche: {context.query}")
        return context

    def after_search(self, context: MiddlewareContext):
        print(f"Trouvé: {len(context.results) if context.results else 0} résultats")
        return context
```

### Recherche vectorielle

Permet la recherche sémantique via des embeddings :

```python
from whoosh.fields import Schema, TEXT, VectorField

schema = Schema(
    content=TEXT,
    embedding=VectorField(dimensions=384)
)
```

### Event Bus

Système d'événements pour un couplage lâche :

```python
from whoosh.event_bus import EventBus, DocumentIndexed

bus = EventBus()

@bus.subscribe
def on_document_indexed(event: DocumentIndexed):
    print(f"Document indexé: {event.docnum}")
```

## Principes de conception

1. **Composabilité**: Les composants se combinent via les opérateurs `|` et `+`
2. **Abstractions sans coût**: Pas de middleware = pas de surcoût
3. **Sync-first**: Le core est synchrone; async est optionnel
4. **Isolation des plugins**: Les plugins ne peuvent pas casser le core
5. **Sécurité des types**: Typage complet avec annotations
