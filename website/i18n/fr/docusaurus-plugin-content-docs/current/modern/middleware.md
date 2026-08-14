---
title: "Middleware"
sidebar_position: 40
---

# Middleware

Le pipeline de middleware permet d'intercepter et modifier les opérations d'indexation et de recherche. C'est le mécanisme d'extension principal pour les préoccupations transverses comme le logging, le cache, les métriques et la sécurité.

## Concepts de base

Un middleware est une classe qui implémente des hooks dans le cycle de vie :

```python
from whoosh.middleware.base import Middleware
from whoosh.middleware.context import MiddlewareContext

class MonMiddleware(Middleware):
    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        # Modifier context.query ou context.metadata
        return context

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        # Accéder à context.results
        return context
```

## Hooks disponibles

| Hook | Quand | Utilisations courantes |
|------|------|------------------------|
| `startup(context)` | Initialisation | Ouvrir connexions, remplir caches |
| `shutdown(context)` | Nettoyage | Fermer connexions, flush buffers |
| `before_index(context)` | Avant indexation | Validation, enrichissement, flags compression |
| `after_index(context)` | Après indexation | Métriques, événements, invalidation cache |
| `before_delete(context)` | Avant suppression | Journalisation audit, contrôle d'accès |
| `after_delete(context)` | Après suppression | Métriques, invalidation cache |
| `before_search(context)` | Avant recherche | Réécriture de requête, cache, auth |
| `after_search(context)` | Après résultats | Logging, métriques, modification résultats |
| `on_error(context, exc)` | Sur exception | Gestion d'erreur, fallbacks |
| `on_commit(context)` | Après commit | Métriques, notifications |

## Classes intégrées

### MetricsMiddleware

```python
from whoosh.middleware import MetricsMiddleware

metrics = MetricsMiddleware()
# Après opérations:
stats = metrics.get_metrics()
# Retourne: {"documents_indexed": N, "searches_executed": N}
```

### CacheMiddleware

```python
from whoosh.middleware import CacheMiddleware

cache = CacheMiddleware()
cached = cache.get_cached("requête utilisateur")
cache.set_cached("requête utilisateur", results)
```

### EmbeddingMiddleware

Enrichit les documents avec des embeddings vectoriels denses avant l'indexation :

```python
from whoosh_modern.middleware import EmbeddingMiddleware
from whoosh_modern.embeddings import FastEmbedProvider

provider = FastEmbedProvider(model_name="BAAI/bge-small-en-v1.5")
embedding = EmbeddingMiddleware(
    embedding_provider=provider,
    source_field="body",
    target_field="body_vector",
)
```

Utilisez `embedding_fields` pour la vectorisation multi-champs :

```python
embedding = EmbeddingMiddleware(
    embedding_provider=provider,
    embedding_fields=[
        {"source_field": "title", "target_field": "title_vector"},
        {"source_field": "body", "target_field": "body_vector"},
    ],
)
```

> **Précédence :** Quand `embedding_fields` est fourni, les valeurs par défaut
> `source_field` / `target_field` sont **ignorées** — chaque entrée est traitée
> indépendamment. Pour éviter la confusion, n'indiquez pas `source_field` /
> `target_field` au niveau racine lorsque vous utilisez `embedding_fields`.

### CompressionMiddleware

Marque les documents pour la compression au niveau du backend :

```python
from whoosh.middleware import CompressionMiddleware

compression = CompressionMiddleware()
# Définit document["_compressed"] = True
```

### EncryptionMiddleware

Marque les documents pour le chiffrement au niveau du backend :

```python
from whoosh.middleware import EncryptionMiddleware

encryption = EncryptionMiddleware()
# Définit document["_encrypted"] = True
```

## MiddlewareChain

```python
from whoosh.middleware import MiddlewareChain

chain = MiddlewareChain([
    MetricsMiddleware(),
    CacheMiddleware()
])

# Exécuter un hook before
context = MiddlewareContext("search")
context.query = "test"
context = chain.run_before("before_search", context)

# ... opération core ...

# Exécuter un hook after
context = chain.run_after("after_search", context)
```

### Ordre d'exécution

- Les hooks `before_*` s'exécutent dans l'ordre d'enregistrement
- Les hooks `after_*` s'exécutent dans l'ordre inverse
- Si un hook lève `StopOperation`, le pipeline s'arrête
- Si `fail_open=False`, les exceptions se propagent immédiatement

## Intégration

### Avec Writer

```python
from whoosh.middleware.integration import apply_middleware_to_writer

writer = apply_middleware_to_writer(ix.writer(), chain.middlewares)

with writer:
    writer.add_document(title="Bonjour", content="Monde")
```

### Avec Searcher

```python
from whoosh.middleware.integration import apply_middleware_to_searcher

searcher = apply_middleware_to_searcher(ix.searcher(), chain.middlewares)
results = searcher.search("query")
```

### Avec PluginManager

```python
from whoosh.plugins.manager import PluginManager

# Les plugins peuvent fournir du middleware
PluginManager.load_plugins()
chain = PluginManager.get_middleware_chain()
```

## Exemple: middleware personnalisé

```python
class RequestLoggingMiddleware(Middleware):
    """Journaliser toutes les recherches."""

    def before_search(self, context: MiddlewareContext):
        context.metadata["request_id"] = generate_request_id()
        logger.info(f"Recherche: {context.query}")
        return context

    def after_search(self, context: MiddlewareContext):
        logger.info(f"Trouvé: {len(context.results)} résultats")
        return context

class RateLimitMiddleware(Middleware):
    """Abandonner les recherches dépassant la limite."""

    def before_search(self, context: MiddlewareContext):
        if not rate_limiter.allow(context):
            raise StopOperation("Limite de taux dépassée")
        return context

class QueryEnrichmentMiddleware(Middleware):
    """Ajouter des synonymes à la requête."""

    def before_search(self, context: MiddlewareContext):
        if context.query:
            context.query += " " + get_synonyms(context.query)
        return context
```

## Gestion des erreurs

```python
class ResilientMiddleware(Middleware):
    """Continuer malgré les erreurs non critiques."""

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        try:
            send_to_analytics(context.results)
        except Exception:
            logger.warning("Analytics failed", exc_info=True)
        return context
```

## Bonnes pratiques

1. **Sans état**: Utilisez `context.metadata` pour les données par requête
2. **Fail fast**: Utilisez `fail_open=True` uniquement pour middleware non critique
3. **L'ordre compte**: Placez le cache avant les métriques, l'auth avant le routage
4. **Performance**: Gardez les hooks légers; utilisez async pour les I/O
5. **Testabilité**: Mockez le contexte pour tester le middleware isolément

## Intégration des providers via middleware

De nombreux providers Whoosh-NG s'intègrent dans le pipeline d'indexation et de recherche grâce aux hooks de middleware. C'est le pattern standard pour les préoccupations transverses qui doivent transformer des documents, des requêtes ou des résultats.

### Mapping provider → middleware

| Provider | Middleware | Hooks utilisés | Usage |
|----------|-----------|----------------|-------|
| `StorageProvider` | `StorageMiddleware` | `before_index`, `on_commit` | Marque le contexte avec le backend de stockage ; écrit des points de commit |
| `StemmerProvider` | `StemmingMiddleware` | `before_index`, `before_search` | Stemme les champs de document et le texte de requête |
| `SynonymProvider` | `SynonymExpansionMiddleware` | `before_index`, `before_search` | Étend les documents et les requêtes avec des synonymes |
| `EmbeddingProvider` | `EmbeddingMiddleware` | `before_index` | Calcule des vecteurs denses pour les champs configurés et les stocke comme champs `VECTOR` |
| `VectorProvider` | (intégré au core Whoosh) | N/A (format de segment) | Enregistré dans `VectorRegistry` ; résolu au moment de la recherche à partir des métadonnées de segment |
| `AutocompleteProvider` | ( autonome ou registre) | N/A | Utilisé directement via `.search()` ou via `AutocompleteRegistry` |

### Flux des providers dans le pipeline

```text
                     ┌──────────────────┐
                     │  PluginManager   │
                     │  .load_plugins() │
                     └────────┬─────────┘
                              │
               ┌──────────────┼──────────────┐
               │              │              │
      ┌────────▼──────┐ ┌────▼─────┐ ┌──────▼────────┐
      │ VectorPlugin  │ │AutoPlugin│ │ Other Plugins │
      │               │ │         │ │               │
      │ VectorRegistry│ │AutoReg. │ │ ProviderReg.  │
      │ .register()   │ │.register│ │ .register()   │
      └───────────────┘ └─────────┘ └───────────────┘

                     ┌──────────────────┐
                     │ MiddlewareChain  │
                     │                  │
                     │ ┌──────────────┐ │
                     │ │ before_index │ │
                     │ │  hooks       │ │
                     │ │  (ordered)   │ │
                     │ └──────┬───────┘ │
                     │        │         │
                     │ ┌──────▼───────┐ │
                     │ │   Writer     │ │
                     │ │  .add_doc()  │ │
                     │ └──────┬───────┘ │
                     │        │         │
                     │ ┌──────▼───────┐ │
                     │ │  on_commit   │ │
                     │ │  hooks       │ │
                     │ └──────────────┘ │
                     └──────────────────┘

                     ┌──────────────────┐
                     │  Searcher         │
                     │                  │
                     │ ┌──────────────┐ │
                     │ │before_search │ │
                     │ │  hooks       │ │
                     │ └──────┬───────┘ │
                     │        │         │
                     │ ┌──────▼───────┐ │
                     │ │   Query      │ │
                     │ │  execution   │ │
                     │ └──────┬───────┘ │
                     │        │         │
                     │ ┌──────▼───────┐ │
                     │ │ after_search │ │
                     │ │  hooks       │ │
                     │ └──────────────┘ │
                     └──────────────────┘
```

### Exemple: pipeline complet de providers

```python
from whoosh.middleware.chain import MiddlewareChain
from whoosh.middleware.wrappers import MiddlewareWriter, MiddlewareSearcher
from whoosh_modern.middleware import (
    StorageMiddleware,
    StemmingMiddleware,
    FileStorageProvider,
)
from whoosh_modern.linguistics.synonyms import (
    SynonymExpansionMiddleware,
    SynonymManager,
)
from whoosh_modern.analysis import get_stemmer

# 1. Construire les providers
storage = FileStorageProvider("/data/index")
stemmer = get_stemmer("auto", "english")
syn_manager = SynonymManager({"car": ["automobile", "vehicle"]})

# 2. Construire la chaîne de middleware
chain = MiddlewareChain([
    StorageMiddleware(storage, name="primary"),
    StemmingMiddleware(stemmer=stemmer.stem, fields=["title", "content"]),
    SynonymExpansionMiddleware(syn_manager),
])

# 3. Indexer avec middleware
with MiddlewareWriter(ix.writer(), chain) as writer:
    writer.add_document(title="Car for sale", content="House near beach")
    # StorageMiddleware.before_index() marque le contexte
    # StemmingMiddleware stemme "Car" → "car"
    # SynonymExpansionMiddleware étend "Car" → "Car automobile vehicle"
    writer.commit()
    # StorageMiddleware.on_commit() écrit le checkpoint

# 4. Rechercher avec middleware
with MiddlewareSearcher(ix.searcher(), chain) as searcher:
    # StemmingMiddleware stemme la requête "cars" → "car"
    # SynonymExpansionMiddleware étend "car" → "car automobile vehicle"
    results = searcher.search("cars")
```

### Insight clé : le middleware comme adaptateur de provider

Le middleware agit comme l'**adaptateur** entre les providers et le pipeline core de Whoosh :

```text
Provider (logique métier)
    │
    ▼
Middleware (intégration pipeline)
    │
    ▼
Whoosh core (moteur générique)
```

- **StorageProvider** → **StorageMiddleware** → writer/searcher Whoosh
- **StemmerProvider** → **StemmingMiddleware** → document/requête Whoosh
- **SynonymProvider** → **SynonymExpansionMiddleware** → champs texte Whoosh

Cette séparation garde les providers simples (responsabilité unique) tandis que le middleware gère l'intégration du cycle de vie (quand et comment appliquer le provider).

## Middleware Moderne (Whoosh-NG 2.0)

Whoosh-NG 2.0 ajoute un package middleware moderne (`whoosh_modern.middleware`) avec un middleware de résilience de type wrapper (réessaissance, cache, journalisation) et un middleware basé sur des hooks pour le stockage, la recherche et l'analyse. Pour plus de détails sur l'architecture moderne du middleware, l'intégration de plugins et le déploiement, consultez le [Guide Middleware & Pipeline de Plugins](middleware-pipeline.md).
