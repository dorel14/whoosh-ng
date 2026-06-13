# Whoosh-Reloaded 4.0 - Plan de modernisation

## Objectif produit
Transformer Whoosh Reloaded d'une bibliothèque de recherche traditionnelle en une plateforme de recherche extensible. Le package core doit rester léger et stable tout en permettant l'ajout de fonctionnalités avancées via des extensions officielles ou tierces, sans modification du code de base.

## High‑Level Architecture (Plugin Architecture & Extensibility Specification)

```text
Application
      │
      ▼
┌──────────────────────┐
│      Whoosh Core     │
├──────────────────────┤
│ Schema               │
│ Query Parser         │
│ Search Engine        │
│ BM25                 │
│ Facets               │
│ Plugin Manager       │
│ Middleware Pipeline  │
│ Event Bus            │
│ Hook System          │
└──────────────────────┘
      │
      ▼
┌──────────────────────┐
│      Plugins         │
├──────────────────────┤
│ FastAPI              │
│ Autocomplete         │
│ Vector Search        │
│ PostgreSQL           │
│ S3                   │
│ Monitoring           │
│ Admin UI             │
│ Custom Plugins       │
└──────────────────────┘
```

# Phase 1 – Plugin System
## Goal
Permettre aux packages externes d'enregistrer des composants sans modifier Whoosh Core.
## Create Plugin Manager
File: `whoosh/plugins/manager.py`
## Plugin Base Class
```python
from abc import ABC

class Plugin(ABC):
    name: str
    version: str
    def register(self, registry):
        pass
```
## Plugin Discovery
Utilisation des entry‑points Python. Exemple de `pyproject.toml` :
```toml
[project.entry-points."whoosh.plugins"]
autocomplete = "whoosh_autocomplete.plugin:AutocompletePlugin"
postgres = "whoosh_postgres.plugin:PostgresPlugin"
```
## Plugin Loading
Au démarrage : `PluginManager.load_plugins()`
## Requirements
* Auto‑découverte
* Validation de version
* Détection de conflits
* Activation / désactivation du plugin

# Phase 2 – Registry System
## Goal
Fournir un registre centralisé pour tous les types extensibles.
## Create Registries
Folder: `whoosh/registry/`
### Storage Registry
`StorageRegistry.register("postgres", PostgresStorageProvider)`
### Analyzer Registry
`AnalyzerRegistry.register("french", FrenchAnalyzer)`
### Ranking Registry
`RankingRegistry.register("rrf", RRFRanker)`
### Suggest Registry
`SuggestRegistry.register("edge_ngram", EdgeNgramProvider)`
### Vector Registry
`VectorRegistry.register("hnsw", HNSWProvider)`
## Requirements
* Enregistrement dynamique
* Recherche à l’exécution
* Empêcher la duplication
* Suivi de la propriété du plugin

# Phase 3 – Middleware Pipeline
## Goal
Traitement avant/ après l’indexation et la recherche.
## Middleware Base
```python
class Middleware:
    async def before_index(self, document):
        return document
    async def after_index(self, document):
        return document
    async def before_search(self, query):
        return query
    async def after_search(self, results):
        return results
```
## Execution Flow
Document → Middleware 1 → Middleware 2 → Storage Provider
## Built‑in Middlewares
* **CompressionMiddleware** – compresse les données stockées.
* **EncryptionMiddleware** – chiffrez le contenu indexé.
* **MetricsMiddleware** – collecte statistiques d’indexation/recherche.
* **CacheMiddleware** – met en cache résultats et facettes.

# Phase 4 – Event Bus
## Goal
Permettre aux plugins de réagir aux événements internes.
## Base Event
```python
class Event: pass
```
## Core Events
* `DocumentIndexed(document_id)`
* `DocumentDeleted(document_id)`
* `SearchExecuted(query)`
* `SegmentMerged(segment_id)`
## API d’abonnement
```python
@event_bus.subscribe(DocumentIndexed)
async def on_document_indexed(event):
    pass
```
## Requirements
* Asynchrone
* Multiples listeners
* Isolation des exceptions
* Sécurité d’exécution

# Phase 5 – Hook System
## Goal
Personnalisation légère sans plein middleware.
## Hook Points
* Indexing: `before_index()`, `after_index()`
* Search:   `before_search()`, `after_search()`
* Query:    `before_parse()`, `after_parse()`
## Example
```python
@hookimpl
def before_search(query):
    return query
```

# Phase 6 – Provider Architecture
## Goal
Changer les back‑ends épinglés en providers pluggables.
## Storage Provider
```python
class StorageProvider:
    async def read(self, key): pass
    async def write(self, key, data): pass
    async def delete(self, key): pass
```
### Official Providers
* Core: `FileStorageProvider`
* Plugins: `PostgresStorageProvider`, `SQLiteStorageProvider`, `S3StorageProvider`, `MinioStorageProvider`
## Ranking Provider
`BM25Provider` (core) plus `TFIDFProvider`, `RRFProvider`, `HybridProvider` via plugins.
## Vector Provider
Examples: `NumpyProvider`, `HNSWProvider`, `FaissProvider`, `QdrantProvider`, `MilvusProvider`.

# Phase 7 – Autocomplete Plugin (`whoosh-autocomplete`)
## API
`searcher.autocomplete("mach")` → `["machine learning", "machine vision"]`
### Endpoints
`GET /autocomplete?q=mach`
### Configuration
```yaml
autocomplete:
  enabled: true
  provider: edge_ngram
  max_results: 10
```

# Phase 8 – FastAPI Plugin (`whoosh-fastapi`)
## Factory
`app = create_app(index)`
## CLI
`whoosh serve`
## Endpoints
* `/search` – POST
* `/autocomplete` – GET
* `/suggest` – GET
* `/facets` – POST
* `/health` – GET
* `/stats` – GET

# Phase 9 – Observability Plugin (`whoosh-observability`)
## Endpoints
`GET /metrics`
### Metrics
* `search_count`, `search_duration`
* `indexed_documents`, `indexing_duration`
* `cache_hits`, `cache_misses`
* `autocomplete_requests`, `autocomplete_duration`

# Phase 10 – Admin UI Plugin (`whoosh-admin`)
## Features
* Index Explorer (segments, docs, fields)
* Query Tester
* Analyzer Playground
* Metrics Dashboard

# Recommended Official Plugin Ecosystem
* **Priority 1**: `whoosh-fastapi`, `whoosh-autocomplete`, `whoosh-observability`
* **Priority 2**: `whoosh-postgres`, `whoosh-s3`, `whoosh-hnsw`
* **Priority 3**: `whoosh-admin`, `whoosh-rag`, `whoosh-analytics`

# Success Criteria
* Ajout de nouveaux systèmes sans modifier le core.
* Nouveaux endpoints API sans toucher au core.
* Réleases indépendantes de plugins.
* Core léger, stable, sans dépendances lourdes.

# Roadmap & Execution Sequence
## Phase A – Foundation & Modern CI
1. Milestone 0: Nettoyage CI/CD, tooling, versioning.
2. Milestone 1: Modernisation du packaging et de la qualité.
3. Milestone 2: Refactor interne du cœur.
## Phase B – Modern API & Extensibility
1. Milestone 3: Implémentation du Plugin Manager & Registry (Phases 1‑2).
2. Milestone 4: Middleware Pipeline & Event Bus (Phases 3‑4).
3. Milestone 5: Hook System & Provider Architecture (Phases 5‑6).
4. Milestone 6: API Objet, Faceting moderne.
## Phase C – Semantic Search & Advanced Plugins
1. Milestone 7: Vector Search & Embeddings.
2. Milestone 8: Autocomplete Plugin (Phase 7).
3. Milestone 9: FastAPI Plugin (Phase 8).
## Phase D – Storage & Observability
1. Milestone 10: Back‑ends de stockage avancés (Postgres, S3).
2. Milestone 11: Observability & Admin UI (Phases 9‑10).
3. Milestone 12: Sync incrémentale & watchers.
## Phase E – Quality & Performance
1. Milestone 13: Fuzzy & Phonétique.
2. Milestone 14: Benchmarks & optimisation.

# Acceptance Criteria Globaux
* **Profil Minimal**: BM25, full‑text, stockage fichier, Python pur.
* **Profil Modern Python**: Dataclasses, Pydantic v2, msgspec, AsyncIO.
* **Profil Semantic Search**: VectorField, Numpy, Embeddings, Hybrid Search.
* **Profil Service Mode**: REST API, PostgreSQL, Métriques.

# Checklist de Validation par Étape
Chaque étape doit être validée par le Lead Dev avec un contrôle obligatoire :

| Étape | Code implémenté | Tests passent (100%) | 0 erreur Ruff | 0 erreur Mypy | Aucune régression | PR vers `dev` |
|-------|-----------------|----------------------|---------------|---------------|---------------------|---------------|
| Phase 1 – Plugin System | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Phase 2 – Registry System | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Phase 3 – Middleware Pipeline | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Phase 4 – Event Bus | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Phase 5 – Hook System | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Phase 6 – Provider Architecture | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Phase 7 – Autocomplete Plugin | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Phase 8 – FastAPI Plugin | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Phase 9 – Observability Plugin | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Phase 10 – Admin UI Plugin | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |

*Un check vert (✔) n'est autorisé que si tous les critères sont vérifiés.*

# Definition of Done par Milestone
* Code implémenté + tests unitaires / intégration.
* 0 erreur Ruff, 0 erreur Mypy.
* Validation Windows & Linux.
* Documentation API + notes de migration.
* PR revue par lead dev senior.

# Risques & Mitigation
* **Compatibilité**: Tests de non‑régression, imports historiques.
* **Dépendances**: Isolation dans les extras.
* **Typage**: Strict mode progressif.
* **Windows**: Tests systématiques paths & locks.
* **Performance**: Benchmarks avant/après.
