---
color_scheme: dark
title: "API Middleware"
nav_order: 7
parent: "Référence API"
lang: fr
---

# API Middleware

Pipeline de middleware pour les opérations d'indexation et de recherche.

## Classes principales

### Middleware

```python
class whoosh.middleware.base.Middleware
```

Classe de base pour tous les middlewares.

#### Méthodes

| Hook | Signature | Appelé quand |
|------|-----------|--------------|
| startup | (context) -> context | Initialisation writer/searcher |
| shutdown | (context) -> context | Nettoyage writer/searcher |
| before_index | (context) -> context | Avant l'ajout d'un document |
| after_index | (context) -> context | Après l'ajout d'un document |
| before_delete | (context) -> context | Avant la suppression |
| after_delete | (context) -> context | Après la suppression |
| before_search | (context) -> context | Avant la recherche |
| after_search | (context) -> context | Après les résultats |
| on_error | (context, exc) -> None | Sur exception |
| on_commit | (context) -> None | Après le commit |

### MiddlewareContext

```python
class whoosh.middleware.context.MiddlewareContext(
    operation: str,
    metadata: dict | None = None
)
```

Attributs:

| Attribut | Type | Description |
|----------|------|-------------|
| `operation` | str | `"index"`, `"search"`, `"delete"`, `"commit"` |
| `query` | Any | Requête (pour `search`) |
| `results` | Any | Résultats de la recherche |
| `document` | dict | Document à indexer (pour `index`) |
| `docnum` | int | Numéro du document (pour `delete`) |
| `metadata` | dict | Données par requête (request_id, trace_id) |

### MiddlewareChain

```python
class whoosh.middleware.base.MiddlewareChain(middlewares)
```

Orchestre l'exécution des middlewares dans l'ordre.

#### Méthodes

| Méthode | Description |
|---------|-------------|
| `chain.add(middleware)` | Ajoute un middleware |
| `chain.run_before(hook, context)` | Exécute les hooks before |
| `chain.run_after(hook, context)` | Exécute les hooks after |
| `chain.run_before_all(hook, context)` | Exécute tous les hooks before |
| `chain.run_after_all(hook, context)` | Exécute tous les hooks after |

### SettingGuard

```python
class whoosh.middleware.base.SettingGuard(
    field: str | None = None,
    default: bool = False
)
```

Vérifie et réinitialise les settings de middleware.

### Skip

```python
class whoosh.middleware.base.Skip(metadata)
```

Exception pour sauter une opération tout en la commitant.

## Intégration

### apply_middleware_to_writer

```python
def apply_middleware_to_writer(
    writer: IndexWriter,
    middlewares: list[Middleware]
) -> IndexWriter
```

Retourne un writer enveloppé par les middlewares.

### apply_middleware_to_searcher

```python
def apply_middleware_to_searcher(
    searcher: Searcher,
    middlewares: list[Middleware]
) -> Searcher
```

Retourne un searcher enveloppé par les middlewares.

## Exceptions

```python
class MiddlewareError(Exception)
class StopOperation(Exception)
class SkipOperation(Skip)
```
