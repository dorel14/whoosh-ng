---
title: "Guide de migration"
nav_order: 70
lang: fr
---

# Guide de migration

Ce guide vous aide à migrer depuis Whoosh legacy ou Whoosh-Reloaded 3.x vers Whoosh-NG v3.0.0.
> **Prochaine version** : v4.0.0.dev0 (en développement) ajoute `SchemaBuilder`, la hiérarchie d'exceptions middleware, et plus encore — voir le [CHANGELOG]({{ '/changelog/' | relative_url }}).

## Depuis Whoosh 1.x/2.x (Legacy)

### Chemins d'import

| Legacy | Whoosh-NG |
|--------|-----------|
| `import whoosh` | `import whoosh` |
| `from whoosh.index import create_in` | `from whoosh.index import create_in` |
| `from whoosh.fields import Schema, TEXT` | `from whoosh.fields import Schema, TEXT` |

L'API core est intentionnellement stable. La plupart du code existant fonctionne sans modification.

## Depuis Whoosh-Reloaded 3.x

Aucun changement cassant. Whoosh-NG est une continuation de Whoosh-Reloaded.

### Migration optionnelle des plugins

```python
# Ancien
from whoosh_modern.vector.numpy_provider import NumpyProvider

# Nouveau (via registre)
from whoosh.vector import NumpyProvider
from whoosh.registry import VectorRegistry

VectorRegistry.register("numpy", NumpyProvider(), "mon_app")
```

### SchemaBuilder (nouveau dans v4.0.0.dev0)

```python
# Ancien
schema = Schema(title=TEXT(stored=True), content=TEXT)

# Nouveau (API fluent)
from whoosh.fields import SchemaBuilder

schema = (
    SchemaBuilder()
    .field("title", TEXT(stored=True))
    .field("content", TEXT)
    .build()
)
```

## Méthode de migration middleware (nouveau dans v4.0.0.dev0)

```python
from whoosh.middleware import Middleware, MiddlewareContext

class LoggingMiddleware(Middleware):
    def before_search(self, context: MiddlewareContext):
        print(f"Query: {context.query}")
        return context

# Envelopper le writer/searcher existant
writer = apply_middleware_to_writer(ix.writer(), [LoggingMiddleware()])
```

## Liste de vérification

1. **Mettre à jour les dépendances**:
   ```bash
   pip install --upgrade whoosh-ng
   ```

2. **Exécuter les tests**:
   ```bash
   uv run pytest tests/ -q
   ```

3. **Mettre à jour les dépendances optionnelles** (si plugins utilisés):
   ```bash
   pip install whoosh-ng[all]
   ```

4. **Revoir le middleware**: Envisagez d'ajouter du middleware pour les préoccupations transverses

## Dépréciations

| Fonctionnalité | Statut | Remplacement |
|----------------|--------|--------------|
| `whoosh_modern.vector` | Déprécié | `whoosh.vector` |
| `whoosh.store` brut | Déprécié | `whoosh.backends` |
| Utilisation directe de `SegmentWriter` | Découragé | Utilisez `IndexWriter` |

## Compatibilité

Whoosh-NG maintient la compatibilité ascendante. Si vous trouvez un changement cassant, signalez-le comme une issue.
