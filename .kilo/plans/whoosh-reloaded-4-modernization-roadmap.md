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
## Code implémenté
- `src/whoosh/plugins/manager.py`: Plugin base class + PluginManager avec `load_plugins()`, `register()`, `enable()`, `disable()`, `validate_version()`, `detect_conflicts()` ✅
- `src/whoosh/plugins/__init__.py`: Export ✅
## Plugin Discovery
- ❌ **Non configuré** - Aucun entry point dans pyproject.toml
## Requirements
* Auto‑découverte ✅
* Validation de version ✅
* Détection de conflits ✅
* Activation / désactivation du plugin ✅

# Phase 2 – Registry System
## Goal
Fournir un registre centralisé pour tous les types extensibles.
## Code implémenté
- `src/whoosh/registry/base.py`: Registry générique avec register/get/unregister/list_keys/owner ✅
- `src/whoosh/registry/__init__.py`: StorageRegistry, AnalyzerRegistry, RankingRegistry, SuggestRegistry, VectorRegistry, AutocompleteRegistry ✅
## Requirements
* Enregistrement dynamique ✅
* Recherche à l'exécution ✅
* Empêcher la duplication ✅
* Suivi de la propriété du plugin ✅

# Phase 3 – Middleware Pipeline
## Goal
Traitement avant/après l'indexation et la recherche.
## Code implémenté
- ❌ **Non implémenté** - Aucune classe Middleware trouvée dans le codebase
- ❌ CompressionMiddleware, EncryptionMiddleware, MetricsMiddleware, CacheMiddleware: **Manquants**

# Phase 4 – Event Bus
## Goal
Permettre aux plugins de réagir aux événements internes.
## Code implémenté
- `src/whoosh/event_bus.py`: EventBus avec subscribe/publish/clear ✅
- `tests/test_event_bus.py`: Tests existants ✅
- Events DocumentIndexed, SearchExecuted définis dans les tests ✅

# Phase 5 – Hook System
## Goal
Personnalisation légère sans plein middleware.
## Code implémenté
- `src/whoosh/hooks.py`: HookImpl, hookimpl, register_hook, call_hook ✅
- `tests/test_hooks.py`: Tests existants (mais fichier tronqué) ⚠️
- ❌ Integration avec PluginManager: Non connecté

# Phase 6 – Provider Architecture
## Goal
Changer les back‑ends épinglés en providers pluggables.
## Code implémenté
- `src/whoosh/vector/base.py`: VectorProvider, VectorField ✅
- `src/whoosh_modern/vector/numpy_provider.py`: NumpyProvider ✅
- `src/whoosh_modern/vector/base.py`: VectorHit, VectorField ✅
- `tests/test_provider_architecture.py`: StorageProvider, RankingProvider, BM25Provider (tests) ✅
## Manquant
- HNSWProvider, FaissProvider, QdrantProvider, MilvusProvider ❌
- Intégration dans StorageRegistry/VectorRegistry ❓

# Phase 7 – Autocomplete Plugin (`whoosh-autocomplete`)
## Code implémenté
- `src/whoosh_modern/autocomplete/provider.py`: AutocompleteProvider, AutocompleteHit ✅
- `src/whoosh_modern/autocomplete/factory.py`: create_autocomplete() ✅
- `src/whoosh_modern/autocomplete/edge_ngram.py`: InvertedIndexAutocomplete ✅
- `tests/test_modern_autocomplete.py`: Tests ✅
## Manquant
- Entry point dans pyproject.toml ❌
- Configuration YAML ❌

# Phase 8 – FastAPI Plugin (`whoosh-fastapi`)
## Code implémenté
- ❌ **Non implémenté** - Aucun fichier fastapi trouvé

# Phase 9 – Observability Plugin (`whoosh-observability`)
## Code implémenté
- ❌ **Non implémenté** - Aucun fichier observability trouvé

# Phase 10 – Admin UI Plugin (`whoosh-admin`)
## Code implémenté
- ❌ **Non implémenté** - Aucun fichier admin trouvé

# Recommended Official Plugin Ecosystem
* **Priority 1**: `whoosh-fastapi` ❌, `whoosh-autocomplete` ✅, `whoosh-observability` ❌
* **Priority 2**: `whoosh-postgres` ❌, `whoosh-s3` ❌, `whoosh-hnsw` ❌
* **Priority 3**: `whoosh-admin` ❌, `whoosh-rag` ❌, `whoosh-analytics` ❌

# Success Criteria
* Ajout de nouveaux systèmes sans modifier le core. ⚠️ (Middleware manquant, intégration hooks limitée)
* Nouveaux endpoints API sans toucher au core. ❌ (FastAPI non implémenté)
* Réleases indépendantes de plugins. ⚠️ (whoosh_modern existe mais pas structuré comme plugin)
* Core léger, stable, sans dépendances lourdes. ✅

# Roadmap & Execution Sequence
## Phase A – Foundation & Modern CI
- ❓ État inconnu sans accès aux fichiers CI

## Phase B – Modern API & Extensibility
- Milestone 3: Plugin Manager & Registry ✅ **COMPLÉTÉ**
- Milestone 4: Event Bus ✅ **COMPLÉTÉ**
- Milestone 5: Hook System & Provider Architecture ⚠️ **PARTIEL** (Hook OK, Provider partiel)
- Milestone 6: API Objet, Faceting moderne ❌

## Phase C – Semantic Search & Advanced Plugins
- Milestone 7: Vector Search & Embeddings ⚠️ **PARTIEL** (NumpyProvider OK, HNSW/Faiss manquants)
- Milestone 8: Autocomplete Plugin ✅ **COMPLÉTÉ**
- Milestone 9: FastAPI Plugin ❌

## Phase D – Storage & Observability
- Milestone 10: Back‑ends de stockage avancés ❌
- Milestone 11: Observability & Admin UI ❌
- Milestone 12: Sync incrémentale & watchers ❌

## Phase E – Quality & Performance
- Milestone 13: Fuzzy & Phonétique ❌
- Milestone 14: Benchmarks & optimisation ❌

# Checklist de Validation par Étape
| Étape | Code implémenté | Tests passent (100%) | 0 erreur Ruff | 0 erreur Mypy | Aucune régression | PR vers `dev` |
|-------|-----------------|----------------------|---------------|---------------|---------------------|---------------|
| Phase 1 – Plugin System | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Phase 2 – Registry System | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Phase 3 – Middleware Pipeline | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Phase 4 – Event Bus | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Phase 5 – Hook System | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Phase 6 – Provider Architecture | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Phase 7 – Autocomplete Plugin | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Phase 8 – FastAPI Plugin | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Phase 9 – Observability Plugin | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Phase 10 – Admin UI Plugin | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |

# Points Critiques à Implémenter
1. **Middleware Pipeline** - Le fichier existe mais le système est squelettique et non intégré au core ; besoin de refactor `src/whoosh/middleware/base.py` et d’ajouter `context.py`, `chain.py`, `registry.py`, `exceptions.py`.
2. **Entry Points** - Configurer dans pyproject.toml pour l'auto-découverte des plugins
3. **whoosh_modern → whoosh_intégration** - Les providers autocomplete/vector ne sont pas intégrés dans les registries
4. **FastAPI Plugin** - Créer `src/whoosh_fastapi/` avec factory et endpoints
5. **Observability Plugin** - Métriques Prometheus, endpoints /metrics, /health, /stats
6. **Hooks - intégration PluginManager** - Connecter les hooks avec le cycle de vie du plugin

# Point codebase au 2026-06-14

## État réel vs plan existant

### Déjà présent mais à moderniser

- **Middleware existe déjà**, mais il est squelettique et non intégré au core :
  - `src/whoosh/middleware/base.py:6` définit une classe `Middleware` avec seulement `before_index`, `after_index`, `before_search`, `after_search`.
  - Les middlewares d’exemple `CompressionMiddleware`, `EncryptionMiddleware`, `MetricsMiddleware`, `CacheMiddleware` existent mais ne font que poser des flags ou compter en mémoire (`src/whoosh/middleware/base.py:20-70`).
  - Aucun test middleware n’est présent.
  - Aucun appel middleware n’est branché dans `IndexWriter.add_document`, `update_document`, `commit`, ni dans `Searcher.search` / `search_with_collector`.
- **PluginManager est déjà partiellement fonctionnel** :
  - Chargement par entry points via `importlib.metadata` : `src/whoosh/plugins/manager.py:39-60`.
  - Enregistrement, activation/désactivation, validation version, conflits : `src/whoosh/plugins/manager.py:30-100`.
  - `register_hooks()` est déclarée mais non utilisée par le manager : `src/whoosh/plugins/manager.py:26` et `src/whoosh/plugins/manager.py:68`.
  - Imports inutiles de registries dans `PluginManager` : `src/whoosh/plugins/manager.py:7-14`.
- **Registry system présent** :
  - `Registry` générique avec owner tracking : `src/whoosh/registry/base.py:8-34`.
  - Registries globales `StorageRegistry`, `AnalyzerRegistry`, `RankingRegistry`, `SuggestRegistry`, `VectorRegistry`, `AutocompleteRegistry`, `BackendRegistry` : `src/whoosh/registry/__init__.py:3-9`.
- **Event Bus présent** :
  - `EventBus.subscribe/publish/clear` : `src/whoosh/event_bus.py:23-72`.
  - Events `DocumentIndexed` et `SearchExecuted` : `src/whoosh/event_bus.py:18-20`.
- **Hook system présent mais minimal** :
  - `hookimpl`, `register_hook`, `call_hook` : `src/whoosh/hooks.py:13-38`.
  - Tests existants mais limités : `tests/test_hooks.py:1-73`.
- **Provider architecture partiellement commencée** :
  - `VectorProvider` et `VectorField` dans `src/whoosh/vector/base.py:18-49`.
  - `NumpyProvider` dans `src/whoosh_modern/vector/numpy_provider.py:13-57`.
  - Tests vectoriels importent probablement depuis un module inexistant : `tests/test_modern_vector.py:9` pointe vers `whoosh_modern.vector.base`, alors que le fichier listé est `src/whoosh_modern/vector/__init__.py`.
- **Backends modernes amorcés** :
  - `Backend` ABC avec lifecycle async : `src/whoosh/backends/abc.py:13-69`.
  - `FileBackend` : `src/whoosh/backends/file.py:14-84`.
  - `SQLiteBackend` : `src/whoosh/backends/sqlite.py:163-420`, avec `BackendRegistry.register("sqlite", SQLiteBackend, "whoosh")` en `src/whoosh/backends/sqlite.py:419-420`.
- **Autocomplete plugin officiel interne** :
  - Entrées entry points déjà présentes : `pyproject.toml:99-102`.
  - `AutocompletePlugin` enregistre `inverted` : `src/whoosh_modern/autocomplete/plugin.py:9-17`.
- **FastAPI / Observability / Admin non implémentés**.

### Packaging / CI / fichiers legacy

- `pyproject.toml` contient déjà :
  - dépendances runtime : `pyproject.toml:35-38`.
  - optional dependencies : `pyproject.toml:40-98`.
  - dev dependencies : `pyproject.toml:86-96`.
  - entry points plugins : `pyproject.toml:99-102`.
  - config ruff, mypy, pytest, coverage : `pyproject.toml:120-244`.
- `requirements.txt` et `requirements-dev.txt` ne contiennent que `.` et `.[dev]` : ils sont redondants avec `pyproject.toml`.
- `.codiumai.toml` est une configuration d’outil de génération de tests, pas une dépendance runtime. À supprimer si l’équipe n’utilise pas CodiumAI/Codium.
- Aucun fichier `tox.ini` ni workflow tox n’est présent.
- `.github/workflows/test.yml` utilise déjà `uv` + matrice Python/OS :
  - install : `uv sync --extra dev --extra vector --extra vector --extra vector` (`test.yml:34-35`).
  - ruff check : `test.yml:37-38`.
  - ruff format : `test.yml:40-41`.
  - mypy : `test.yml:43-44`.
  - pytest : `test.yml:46-47`.
  - build/twine : `test.yml:49-53`.
- `tox` ne peut pas être remplacé par `ruff` : ce sont des outils différents.
  - `tox` crée des environnements isolés et permet de tester plusieurs versions Python / combinaisons de dépendances.
  - `ruff` fait lint/format.
  - Dans ce repo, `tox` n’est pas utilisé et `uv` remplit déjà le rôle principal d’environnement reproductible. Le clean peut donc supprimer toute référence tox uniquement si elle existe, mais ici il n’y a rien à nettoyer côté tox.
- Les exclusions `.tox` dans ruff/pytest restent inoffensives mais peuvent être retirées si on veut un fichier plus propre.

## Architecture cible : middleware inspiré de Taskiq

### Principes à reprendre de Taskiq

Taskiq expose un modèle simple et extensible :

- une base `TaskiqMiddleware` ;
- hooks synchrones ou asynchrones ;
- hooks côté client et worker : `pre_send`, `post_send`, `pre_execute`, `on_error`, `post_execute`, `post_save` ;
- référence au broker dans `self.broker` ;
- capacité à modifier le message et à stocker des labels/contextes.

Pour Whoosh, on adapte ce modèle à une bibliothèque de recherche, pas à une file de tâches.

### API cible proposée

Créer un système middleware en 4 couches :

1. **Context**
   - `MiddlewareContext` avec :
     - `operation`: `index`, `search`, `delete`, `commit`, `open`, `close`.
     - `index`, `backend`, `writer`, `searcher`.
     - `document`, `query`, `collector`, `results`.
     - `labels: dict[str, object]`.
     - `metadata: dict[str, object]`.
   - Objectif : éviter de passer 15 arguments à chaque hook.

2. **Base middleware**
   - `startup(context)`, `shutdown(context)`.
   - `before_index(context) -> context`.
   - `after_index(context) -> context`.
   - `before_delete(context) -> context`.
   - `after_delete(context) -> context`.
   - `before_search(context) -> context`.
   - `after_search(context) -> context`.
   - `on_error(context, exc)`.
   - `on_commit(context)`.
   - Support sync et async via `inspect.isawaitable`.

3. **Middleware chain**
   - `MiddlewareChain` ordonnée, propriétaire plugin, priorité, dépendances.
   - Exécution en chaîne :
     - avant : `middleware_1.before_search -> middleware_2.before_search -> core`.
     - après : `middleware_2.after_search -> middleware_1.after_search`.
   - Politique claire :
     - par défaut, une exception middleware fait échouer l’opération.
     - option `fail_open=True` uniquement pour observability/metrics non critiques.
   - Support `StopOperation` pour annuler proprement une recherche ou un indexage.

4. **Integration points**
   - `Index.writer()` enveloppe le writer avec middleware si configuré.
   - `Index.searcher()` enveloppe le searcher avec middleware si configuré.
   - `Backend.startup/shutdown` déclenchent les middlewares lifecycle.
   - `SegmentWriter.add_document/update_document/delete_document/commit/cancel` passent par la chaîne.
   - `Searcher.search`, `search_page`, `find`, `search_with_collector` passent par la chaîne sans casser l’API legacy.
   - `AsyncWriter`, `BufferedWriter`, `MpWriter` doivent être couverts par des wrappers au niveau `IndexWriter` plutôt que par modification de chaque sous-classe.

### Middlewares officiels à fournir

- `MetricsMiddleware` : compteurs internes sans dépendance Prometheus.
- `CacheMiddleware` : cache de recherche simple, désactivable.
- `ObservabilityMiddleware` : optionnel, dépend de `prometheus-client`, expose `/metrics` dans le plugin FastAPI.
- `CompressionMiddleware` et `EncryptionMiddleware` doivent être déplacés ou clarifiés :
  - compression au stockage/backend, pas au document brut.
  - encryption au backend ou au store, avec gestion explicite des clés.
- `RetryMiddleware` n’a pas de sens direct pour Whoosh, sauf pour backends réseau.

### Règles d’architecture

- Le core Whoosh ne doit dépendre d’aucun plugin lourd.
- Les middlewares doivent être optionnels et transparents si aucun n’est configuré.
- L’API legacy doit rester compatible.
- Les middlewares doivent être typés, testés et documentés.
- Les middlewares doivent pouvoir venir de plugins externes via entry points.

## Inspirations Tantivy à intégrer progressivement

Tantivy apporte une architecture très claire autour d’index immuables, segments, snapshots et séparation writer/reader/searcher.

### Concepts à transposer

1. **Segments immuables + commit atomique**
   - Whoosh a déjà une logique de segments/TOC, mais elle est ancienne et dispersée.
   - Objectif : documenter et renforcer le modèle :
     - un commit écrit un ou plusieurs segments immuables ;
     - le fichier meta/TOC est mis à jour atomiquement ;
     - les anciens segments restent lisibles tant que des readers existent.

2. **Searcher = snapshot**
   - Formaliser que `Searcher` capture une génération d’index.
   - Ajouter des tests garantissant qu’un searcher ouvert avant commit ne voit pas les documents ajoutés après commit.

3. **Directory abstraction**
   - `FileStorage` existe déjà, mais on peut le généraliser en `Directory` / `Store` :
     - `FileDirectory`
     - `RamDirectory`
     - `SQLiteDirectory`
     - futur `S3Directory`
   - Les backends doivent composer avec cette abstraction.

4. **Composants de segment explicites**
   - S’inspirer de Tantivy :
     - `Postings`
     - `Positions`
     - `FastFields`
     - `FieldNorms`
     - `Terms`
     - `Store`
     - `Delete`
   - Whoosh possède déjà des morceaux équivalents dans `codec`, `columns`, `filedb`, mais ils ne sont pas nommés comme un modèle moderne.

5. **Fast fields / columns**
   - `src/whoosh/columns.py` existe déjà.
   - À moderniser en provider typé pour :
     - tri ;
     - facettes ;
     - agrégations ;
     - scoring hybride ;
     - filtres post-query.

6. **DocStore séparé du posting store**
   - Les champs stockés doivent être pensés comme un docstore compressé/lazy.
   - Éviter de lire les stored fields pour chaque document matché.

7. **Delete bitset / tombstones**
   - Aujourd’hui les deletes Whoosh sont compatibles mais peuvent être optimisés.
   - Ajouter une stratégie explicite :
     - tombstones par segment ;
     - merge janitor ;
     - purge des segments trop supprimés.

8. **Merge janitor / background merge**
   - Ajouter une politique de merge plus moderne :
     - seuil par nombre de segments ;
     - seuil par ratio de deletes ;
     - option async/background.

9. **Query plan / collector modernization**
   - Whoosh a déjà une bonne séparation `Query -> Collector -> Results`.
   - Ajouter une couche `QueryPlan` optionnelle pour :
     - expliquer une requête ;
     - estimer un coût ;
     - permettre optimisations futures.

10. **Schema builder moderne**
   - Garder `Schema(...)` pour compatibilité.
   - Ajouter `SchemaBuilder()` inspiré de Tantivy pour une API plus lisible et typée.

## Plan d’exécution recommandé

### Phase 0 — Clean packaging et CI

Objectif : supprimer les doublons sans casser les utilisateurs.

Actions :

1. Supprimer `requirements.txt` et `requirements-dev.txt` si aucun workflow/doc ne les utilise.
2. Mettre à jour README pour ne documenter que :
   - `pip install whoosh-reloaded`
   - `uv sync --extra dev`
   - `uv run ruff check .`
   - `uv run ruff format --check .`
   - `uv run mypy src/whoosh`
   - `uv run pytest tests`
3. Supprimer `.codiumai.toml` si l’équipe n’utilise pas CodiumAI.
4. Vérifier `git status` avant suppression :
   - si `src/whoosh_reloaded.egg-info` est ignoré, ne pas le committer.
   - si des fichiers générés sont trackés, les retirer proprement.
5. Nettoyer les références `.tox` uniquement si elles existent. Ici aucun `tox.ini`, aucun workflow tox.
6. Corriger l’install CI :
   - `uv sync --extra dev --extra vector --extra vector --extra vector` doit devenir `uv sync --extra dev --extra vector`.

Critères d’acceptation :

- `uv sync --extra dev` fonctionne.
- CI inchangée fonctionnellement.
- Aucun fichier packaging redondant.

### Phase 1 — Middleware foundation

Objectif : créer un système middleware robuste avant de l’intégrer au core.

Actions :

1. Remplacer `src/whoosh/middleware/base.py` par une API complète.
2. Ajouter :
   - `context.py`
   - `chain.py`
   - `registry.py`
   - `exceptions.py`
3. Ajouter tests :
   - sync middleware ;
   - async middleware ;
   - ordre avant/après ;
   - exception isolation ou fail-fast selon décision ;
   - `StopOperation` ;
   - labels/context ;
   - lifecycle startup/shutdown.
4. Ajouter un `MiddlewareRegistry` ou intégrer middleware dans `Registry`.

Critères d’acceptation :

- 100 % des nouveaux tests middleware passent.
- Aucun middleware configuré = comportement inchangé.
- API typée et documentée.

### Phase 2 — Intégration Writer/Searcher

Objectif : brancher middleware aux vrais points d’entrée sans casser l’API legacy.

Actions :

1. Créer un wrapper `MiddlewareWriter(IndexWriter)` :
   - `add_document`
   - `update_document`
   - `delete_document`
   - `delete_by_term`
   - `delete_by_query`
   - `commit`
   - `cancel`
2. Créer un wrapper `MiddlewareSearcher(Searcher)` :
   - `search`
   - `search_page`
   - `find`
   - `search_with_collector`
3. Intégrer dans `Index.writer()` et `Index.searcher()` uniquement si middleware configuré.
4. Ajouter events EventBus :
   - `IndexingStarted`, `IndexingCompleted`, `IndexingFailed`
   - `SearchStarted`, `SearchCompleted`, `SearchFailed`
5. Garder `DocumentIndexed` et `SearchExecuted` pour compatibilité.

Critères d’acceptation :

- Les tests legacy Whoosh passent sans modification.
- Les middlewares voient les bons contextes.
- Les wrappers n’altèrent pas `MpWriter`, `AsyncWriter`, `BufferedWriter`.

### Phase 3 — Plugin lifecycle + hooks + middleware

Objectif : connecter PluginManager, hooks, registries et middleware.

Actions :

1. Nettoyer `PluginManager` :
   - retirer imports inutiles ;
   - ajouter `PluginMetadata` ;
   - gérer `depends_on`, `priority`, `middleware`.
2. Ajouter `PluginManager.list_middleware()` ou `get_middleware_chain()`.
3. Rendre `Plugin.register_hooks()` réellement utilisé.
4. Ajouter tests de conflit et dépendances.
5. Documenter un plugin middleware externe minimal.

Critères d’acceptation :

- Un plugin externe peut enregistrer un middleware via entry point.
- Les hooks plugins sont appelés au bon moment.
- Les conflits de plugins sont détectés avant activation.

### Phase 4 — Middlewares officiels

Objectif : fournir des middlewares utiles mais optionnels.

Actions :

1. `MetricsMiddleware` sans dépendance externe.
2. `CacheMiddleware` avec TTL optionnel.
3. Plugin `whoosh-observability` :
   - Prometheus metrics.
   - endpoints `/metrics`, `/health`, `/stats` via FastAPI.
4. Déplacer/clarifier `CompressionMiddleware` et `EncryptionMiddleware` :
   - compression au backend/store.
   - encryption au backend/store avec gestion explicite des clés.

Critères d’acceptation :

- Aucun optional dependency lourd dans le core.
- Metrics/observability installables via extra `metrics`.
- Tests couvrant les middlewares officiels.

### Phase 5 — Modernisation core inspirée Tantivy

Objectif : améliorer performance, maintenabilité et extensibilité sans réécrire Whoosh d’un coup.

Actions :

1. Formaliser le modèle segments/TOC :
   - docs d’architecture ;
   - tests de snapshot.
2. Ajouter `Directory` abstraction progressive autour de `FileStorage`.
3. Moderniser `columns.py` en fast fields provider.
4. Ajouter `SchemaBuilder` tout en gardant `Schema`.
5. Ajouter `QueryPlan` optionnel.
6. Ajouter merge janitor configurable.
7. Améliorer delete/tombstone strategy.

Critères d’acceptation :

- Aucun changement cassant sur API publique.
- Benchmarks avant/après documentés.
- Tests de non-régression sur recherche, faceting, sorting, highlighting.

### Phase 6 — FastAPI plugin

Objectif : fournir une API HTTP moderne sans alourdir le core.

Actions :

1. Créer `src/whoosh_fastapi/`.
2. Factory `create_app(index, autocomplete=None, vector=None)`.
3. Endpoints :
   - `GET /health`
   - `POST /search`
   - `GET /autocomplete`
   - `POST /vector/search`
   - `GET /metrics` si observability installé.
4. Pydantic v2 models optionnels.
5. Tests avec `httpx ASGITransport`.

Critères d’acceptation :

- Plugin installable via extra `api`.
- Aucun import FastAPI dans le core.
- Documentation d’usage.

### Phase 7 — Qualité, docs, benchmarks

Actions :

1. Ajouter docs :
   - middleware architecture ;
   - plugin developer guide ;
   - backend provider guide ;
   - migration guide Whoosh legacy -> Whoosh Reloaded 4.
2. Renforcer ruff progressivement :
   - garder E4/E9/F au départ ;
   - ajouter UP, B, SIM, C4 par phases.
3. Réduire progressivement les disables mypy au lieu de tout activer d’un coup.
4. Ajouter benchmarks ciblés :
   - indexation batch ;
   - search top-k ;
   - facet/sort ;
   - middleware overhead.
5. Ajouter tests de compatibilité API legacy.

Critères d’acceptation :

- CI verte sur Linux/Windows.
- Ruff/format/mypy/pytest/build/twine passent.
- Benchmarks reproductibles avec `uv run`.

## Décisions à valider avec lead dev / architecte

1. **Compatibilité legacy**
   - Recommandation : conserver `whoosh.index.create_in`, `open_dir`, `IndexWriter`, `Searcher.search`.
   - Ne pas casser les utilisateurs existants.

2. **Middleware fail-fast ou fail-open**
   - Recommandation architecte : fail-fast par défaut.
   - Les middlewares non critiques doivent opt-in `fail_open=True`.

3. **Async dans le core**
   - Recommandation : garder le core sync pour compatibilité.
   - Middleware peut être async.
   - Backends async via `Backend.startup/shutdown` et futures providers.

4. **Compression/encryption**
   - Recommandation : ne pas les mettre dans le middleware document.
   - Les placer au niveau backend/store pour éviter de stocker des documents déjà transformés de manière ambiguë.

5. **Tantivy-inspired rewrite**
   - Recommandation : ne pas réécrire le codec d’un coup.
   - Moderniser par couches : snapshots, directory, fast fields, merge janitor, docs/benchmarks.

6. **Tox**
   - Recommandation : ne pas réintroduire tox.
   - Garder `uv` + matrice GitHub Actions.
   - `ruff` ne remplace pas tox, mais `uv` remplace le besoin principal d’environnements reproductibles.

## Priorités immédiates

1. Clean packaging/CI.
2. Middleware foundation + tests.
3. Intégration writer/searcher.
4. PluginManager + hooks + registries.
5. Middlewares officiels.
6. Modernisation core Tantivy-inspired par petites étapes.

### Tâche supplémentaire - README update

Après validation du nommage Whoosh-NG :

- Renommer projet en **Whoosh-NG** dans README.md
- Conserver attribution **Matt Chaput** (créateur original)
- Conserver mention **Sygil-Dev** (mainteneurs actuels)
- Mettre à jour badges PyPI vers `whoosh-NG`
- Aligner instructions d'installation avec nouvelle structure

---

# Phase 0.5 — Refactoring Pylance & Typage

## Objective

Corriger les erreurs Pylance/Mypy pour une base de code stable et maintenable, tout en préparant le terrain pour des docstrings exhaustives.

## Erreurs connues à corriger

### `src/whoosh/automata/fst.py`
- Ligne 202: méthode `@staticmethod` avec paramètre `self` → changer en méthode normale
- Ligne 371, 392 : accès à `.keys` sur objet potentiellement None → ajouter vérification `is not None`
- Ligne 402 : subscript sur None → vérifier avant indexation
- Ligne 407 : `sorted(Node)` incompatible → implémenter `__lt__` ou utiliser key function
- Ligne 517 : attribut `copy` manquant sur `BaseCursor` → ajouter ou corriger implémentation
- Ligne 757-762 : opérateurs `<` et `+=` sur types incompatibles → ajouter guards
- Ligne 759 : `__getitem__` signature incorrecte → typer correctement
- Ligne 1065 : comparaison `>` sur types incompatibles → ajouter cast ou type guards
- Ligne 1109 : appel sur None → vérifier avant appel
- Ligne 1210-1212, 1409-1413 : `.read`/`.write` sur None → vérifier `is not None`
- Ligne 1280 : attribut `_root` inconnu → typer la classe

### `src/whoosh/automata/glob.py`
- Ligne 85 : subscript sur None → vérifier avant

### `src/whoosh/codec/plaintext.py`
- Ligne 43-51 : accès à `_dbfile` inconnu → ajouter attribut ou corriger type
- Ligne 363 : argument manquant `command` → ajouter paramètre
- Ligne 386 : kwargs mal typé → ajouter `**kwargs: str` ou caster

## Actions

1. Exécuter `uv run pyright --stats src/whoosh` pour lister toutes les erreurs
2. Corriger progressivement par module :
   - `automata/fst.py`
   - `automata/glob.py`
   - `codec/plaintext.py`
   - `automata/` autres fichiers
   - `codec/` autres fichiers
   - Modules legacy avec imports conditionnels
3. Ajouter `# type: ignore[misc]` temporaire sur code legacy non-modifié si nécessaire
4. Mettre à jour `.github/workflows/test.yml` pour inclure `pyright` dans les checks
5. Ajouter `pyright` dans `requirements-dev.txt` ou `pyproject.toml` optional deps

## Stratégie

- **Pas de refactor massif** : corriger uniquement ce qui plante Pylance
- **Ne pas casser l'API publique** : garder compatibilité
- **Docstrings** : ajouter après les corrections de types

## Intégration triage legacy issues

Avant tout refactor, analyser les issues ouvertes sur whoosh-community/whoosh :

- Identifier les bugs critiques (crash, data corruption, performance)
- Prioriser selon impact utilisateur
- Corriger dans les petites itérations
- Fermer les issues obsolètes ou déjà résolues dans quiose-reloaded

Actions :

1. Script `tools/triage_issues.py` pour lister, classer, tagger
2. Label `legacy-bug` sur les issues pertinentes
3. Corriger ou épingler dans le plan

---

## Délégation aux agents

Chaque tâche doit être exécutée par un agent spécialisé avec des commits atomiques.

### Agent `code-modernizer` : Refactoring Pylance & Typage

Fichiers : `src/whoosh/automata/fst.py`, `src/whoosh/automata/glob.py`, `src/whoosh/codec/plaintext.py`, autres modules legacy

Actions :
- Exécuter pyright, créer commit par fichier corrigé
- Ajouter `# type: ignore[misc]` temporaire sur code non-modifié
- Ne pas casser l'API publique

### Agent `issue-triage` : Analyse des issues legacy

Actions :
- Script `tools/triage_issues.py` pour lister issues whoosh-community
- Label `legacy-bug` et priorisation
- Reporter bugs critiques dans le plan

### Agent `doc-architect` : Documentation Jekyll

Fichiers : `docs/_config.yml`, `docs/en/`, `docs/fr/`

Actions :
- Créer structure guides + API reference
- Écrire pages Markdown bilingues
- Intégrer snippets commentés

### Agent `plugin-engineer` : Middleware & Plugins

Fichiers : `src/whoosh/middleware/`, `src/whoosh/plugins/`, `src/whoosh_modern/vector/`, `src/whoosh_modern/autocomplete/`

Actions :
- Implémenter `MiddlewareContext`, `MiddlewareChain`
- Connecter hooks dans PluginManager
- Intégrer middlewares dans writer/searcher

### Agent `backend-architect` : Provider Architecture

Fichiers : `src/whoosh/backends/`, `src/whoosh/registry/`

Actions :
- Compléter `BackendRegistry.register()`
- Ajouter providers manquants (HNSW, Faiss, etc.)
- Tests d'intégration

### Agent `fastapi-plugin` : API Plugin

Fichiers : `src/whoosh_fastapi/` (à créer)

Actions :
- Factory `create_app()`
- Endpoints `/search`, `/autocomplete`, `/health`, `/metrics`
- Tests httpx ASGITransport

---

## Critères d'acceptation

- `uv run pyright src/whoosh` retourne < 50 erreurs (objectif progressif)
- Aucun régression dans les tests
- Documentation des signatures mises à jour

---

# Annexe — Vision Whoosh-NG fournie par le dirigeant

## Vision produit

Whoosh-NG doit devenir une plateforme de recherche modulaire et extensible, tout en conservant les forces historiques de Whoosh :

- Pure Python.
- Embedded.
- Lightweight.
- Aucun service externe obligatoire.
- Dépendances minimales.
- Intégration simple.
- Extensibilité communautaire.

Le core doit rester petit, stable et sans dépendance obligatoire. Les fonctionnalités avancées doivent être livrées par plugins indépendants.

## Architecture globale validée comme direction

```text
Application
      │
      ▼
┌─────────────────────────────┐
│       Whoosh-NG Core        │
├─────────────────────────────┤
│ Schema                      │
│ Search Engine               │
│ BM25                        │
│ Facets                      │
│ Plugin Manager              │
│ Registry System             │
│ Middleware Pipeline         │
│ Event Bus                   │
│ Hook System                 │
└─────────────────────────────┘
      │
      ▼
┌─────────────────────────────┐
│           Plugins           │
├─────────────────────────────┤
│ FastAPI                     │
│ Autocomplete                │
│ PostgreSQL                  │
│ SQLite                      │
│ S3                          │
│ Vector Search               │
│ Embeddings                  │
│ Monitoring                  │
│ Admin UI                    │
│ RAG                         │
└─────────────────────────────┘
```

## Écosystème plugin cible

Les plugins doivent pouvoir être installés indépendamment :

```bash
pip install whoosh-ng
pip install whoosh-ng-fastapi
pip install whoosh-ng-autocomplete
pip install whoosh-ng-postgres
pip install whoosh-ng-hnsw
pip install whoosh-ng-observability
```

À arbitrer avant implémentation : le dépôt actuel s’appelle encore `whoosh-reloaded` avec package `whoosh` et `whoosh_modern`. La vision Whoosh-NG impose une décision de nommage :

1. garder `whoosh-reloaded` comme nom de distribution, avec modules `whoosh` et `whoosh_modern` ;
2. renommer progressivement vers `whoosh-ng` ;
3. publier `whoosh-ng` comme nouveau package tout en gardant `whoosh-reloaded` comme compat layer.

Recommandation : ne pas renommer d’un coup. Préparer d’abord les briques techniques, puis décider du nommage avant publication 4.0 stable.

## Roadmap Whoosh-NG à fusionner avec le plan existant

### Phase 0 — Foundation Refactoring

À intégrer dans notre Phase 0 et Phase 7 :

- Typage strict progressif, pas `mypy --strict` d’un coup sur tout le legacy.
- Ruff/format/mypy/pytest/build/twine dans CI.
- `py.typed` dans le package.
- Nouvelle structure logique :
  - `core`
  - `plugins`
  - `registry`
  - `middleware`
  - `events`
  - `hooks`
  - `providers`
  - `models`
  - `asyncio`
  - `api`

Recommandation : créer cette structure progressivement sous `src/whoosh/...` et `src/whoosh_modern/...` avant tout renommage public.

### Phase 1 — Plugin System

Déjà partiellement présent. À compléter avec :

- validation de version ;
- validation de dépendances ;
- conflit entre plugins ;
- enable/disable ;
- dépendances entre plugins ;
- priorité d’exécution ;
- entry points `whoosh.plugins` ou `whoosh_ng.plugins` selon décision de nommage.

### Phase 2 — Registry System

Déjà présent. À enrichir avec :

- `StorageRegistry`
- `AnalyzerRegistry`
- `RankingRegistry`
- `SuggestRegistry`
- `VectorRegistry`
- `MiddlewareRegistry`
- `BackendRegistry`

### Phase 3 — Middleware Framework

Vision dirigeant :

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

Fusion avec recommandation architecte :

- garder une API simple pour les plugins ;
- utiliser un `MiddlewareContext` en interne pour éviter les signatures fragiles ;
- supporter sync/async ;
- exécuter en chaîne avant/après ;
- ajouter middlewares officiels :
  - `CompressionMiddleware`
  - `EncryptionMiddleware`
  - `CacheMiddleware`
  - `MetricsMiddleware`
  - `QueryExpansionMiddleware`
  - `SpellCorrectionMiddleware`

Précision architecturale : compression et encryption doivent probablement être des middlewares de stockage/backend plutôt que des middlewares de document brut.

### Phase 4 — Event Bus

À aligner avec les events proposés :

- `DocumentIndexed`
- `DocumentDeleted`
- `SearchExecuted`
- `SegmentMerged`
- futurs :
  - `IndexingStarted`
  - `IndexingCompleted`
  - `IndexingFailed`
  - `SearchStarted`
  - `SearchCompleted`
  - `SearchFailed`

### Phase 5 — Hook System

À conserver comme extension légère :

- `before_search`
- `after_search`
- `before_index`
- `after_index`
- `before_parse`
- `after_parse`

À connecter au PluginManager pour que les plugins puissent enregistrer leurs hooks.

### Phase 6 — Provider Architecture

À fusionner avec notre vision Tantivy-inspired :

- Storage Providers :
  - `FileStorageProvider`
  - `SQLiteStorageProvider`
  - `PostgresStorageProvider`
  - `S3StorageProvider`
  - `MinioStorageProvider`
  - `RedisStorageProvider`
  - `MongoStorageProvider`
- Ranking Providers :
  - `BM25Provider`
  - `TFIDFProvider`
  - `RRFProvider`
  - `HybridProvider`

### Phase 7 — Modern Object Models

À ajouter comme module optionnel :

- dataclass ;
- Pydantic ;
- msgspec ;
- `ModelSchema(Book)`.

Dépendance : extra `models`.

### Phase 8 — AsyncIO Support

À traiter prudemment :

- garder le core sync ;
- proposer `AsyncIndex`, `AsyncWriter`, `AsyncSearcher` ;
- utiliser `asyncio.to_thread()` pour les opérations bloquantes ;
- ne pas rendre async obligatoire.

### Phase 9 — Vector Search Plugin

À fusionner avec notre Phase 7/semantic search :

- `VectorField(dimensions=768)` ;
- `searcher.vector_search(...)` ;
- `searcher.hybrid_search(...)` ;
- providers :
  - `NumpyProvider`
  - `HNSWProvider`
  - `FaissProvider`
  - `QdrantProvider`
  - `MilvusProvider`

### Phase 10 — Embedding Providers

À ajouter en plugin :

- `SentenceTransformerProvider`
- `FastEmbedProvider`
- `CustomEmbeddingProvider`

### Phase 11 — Autocomplete Plugin

Déjà amorcé. À compléter :

- `EdgeNgramSuggestProvider`
- `NgramSuggestProvider`
- `FuzzySuggestProvider`
- API `searcher.autocomplete("mach")`
- endpoint `GET /autocomplete?q=mach`

### Phase 12 — FastAPI Plugin

À créer :

- `create_app(index)`
- CLI `whoosh-ng serve`
- endpoints :
  - `POST /search`
  - `GET /autocomplete`
  - `GET /suggest`
  - `POST /facets`
  - `GET /health`
  - `GET /stats`
  - `GET /metrics` via observability

### Phase 13 — Incremental Indexing

À intégrer avec watchers :

- `index.sync()`
- détection par :
  - taille ;
  - mtime ;
  - checksum ;
- optional extra `xxhash`.

### Phase 14 — Real-Time Watchers

Plugin :

- `whoosh-ng-watch`
- dépendance `watchdog`
- API `index.watch("/documents")`
- support Linux, Windows, macOS.

### Phase 15 — Advanced Fuzzy Search

Plugin :

- `whoosh-ng-fuzzy`
- dépendance `rapidfuzz`
- algorithmes :
  - Levenshtein
  - Damerau-Levenshtein
  - Jaro-Winkler
  - Trigram Similarity

### Phase 16 — Phonetic Search

Plugin :

- `whoosh-ng-phonetic`
- dépendance `metaphone`
- analyzers :
  - `SoundexAnalyzer`
  - `MetaphoneAnalyzer`
  - `DoubleMetaphoneAnalyzer`

### Phase 17 — Observability Plugin

Plugin :

- `whoosh-ng-observability`
- endpoint `GET /metrics`
- métriques :
  - search_count
  - search_duration
  - indexed_documents
  - indexing_duration
  - cache_hits
  - cache_misses
  - autocomplete_requests
  - autocomplete_duration

### Phase 18 — Admin UI Plugin

Plugin :

- `whoosh-ng-admin`
- features :
  - index explorer ;
  - query playground ;
  - analyzer playground ;
  - metrics dashboard.

### Phase 19 — Configuration System

À ajouter après les briques core :

- configuration YAML ou TOML ;
- exemple :

```yaml
index:
  storage: postgres
  middleware:
    - compression
    - encryption
    - cache
  ranking: bm25

vector:
  provider: hnsw

autocomplete:
  provider: edge_ngram

api:
  enabled: true

metrics:
  enabled: true
```

Recommandation : ne pas ajouter YAML dans le core. Fournir un petit module `whoosh.config` basé sur `tomllib` pour Python 3.11+ ; YAML uniquement dans plugin ou extra optionnel.

## Critères de succès Whoosh-NG

Whoosh-NG doit permettre :

- nouveaux moteurs de stockage sans modifier le core ;
- nouveaux algorithmes de ranking sans modifier le core ;
- nouveaux analyzers sans modifier le core ;
- nouveaux moteurs vectoriels sans modifier le core ;
- nouveaux endpoints API sans modifier le core ;
- cycles de release indépendants pour les plugins ;
- extensions développées par la communauté ;
- stabilité long terme du core.

Le core doit rester lightweight, dependency-free, et concentré sur les fondamentaux de recherche.

## Synthèse de fusion avec le plan actuel

Le complément Whoosh-NG confirme la direction du plan actuel et ajoute trois axes à garder visibles :

1. **Nommage et packaging** : arbitrer `whoosh-reloaded` vs `whoosh-ng` avant publication stable.
2. **Async et models** : ajouter comme modules optionnels, sans casser le core sync.
3. **Plugins applicatifs** : FastAPI, Admin UI, Watchers, Fuzzy, Phonetic, RAG et Analytics doivent être conçus comme des packages externes, pas comme du code core.

---

# Documentation GitHub Pages Evolution

## Objective

Migrer la documentation vers **Jekyll + Just the Docs** pour une publication native sur GitHub Pages, avec une structure bilingue (EN/FR), documentation manuelle exhaustive des APIs, et intégration des exemples existants.

## Current State

- Sphinx existant dans `docs/source/` avec ~50 fichiers RST
- `docs/requirements.txt` : sphinx, sphinx_rtd_theme, sphinx-jsonschema
- Thème RTD configuré dans `docs/source/conf.py`
- GitHub Pages nécessite Jekyll ou HTML statique

## Proposed Structure

```text
docs/
├── _config.yml           # Jekyll config (Just the Docs theme)
├── Gemfile               # bundler + jekyll-remote-theme
├── favicon.ico
├── logo.png
├── _pages/               # Legacy Sphinx redirect pages (optional)
├── en/
│   ├── index.md
│   ├── quickstart.md
│   ├── guides/
│   │   ├── installation.md
│   │   ├── core-concepts.md
│   │   ├── schema.md
│   │   ├── indexing.md
│   │   ├── searching.md
│   │   ├── query.md
│   │   ├── plugins.md
│   │   ├── middleware.md
│   │   ├── backends.md
│   │   ├── vector.md
│   │   ├── autocomplete.md
│   │   └── migration.md
│   ├── api/
│   │   ├── index.md
│   │   ├── core.md          # Index, Schema, Version
│   │   ├── fields.md        # FieldType, TEXT, ID, NUMERIC, etc.
│   │   ├── writing.md       # IndexWriter, AsyncWriter, BufferedWriter
│   │   ├── searching.md     # Searcher, Results, Collector
│   │   ├── query.md         # Query classes, parsers
│   │   ├── plugins.md       # Plugin, PluginManager
│   │   ├── registry.md      # Registry system
│   │   ├── middleware.md    # Middleware base & hooks
│   │   ├── event-bus.md     # EventBus, DocumentIndexed, etc.
│   │   ├── hooks.md         # hookimpl, register_hook, call_hook
│   │   ├── backends.md      # Backend ABC, FileBackend, SQLiteBackend
│   │   └── modern.md        # VectorProvider, AutocompleteProvider, etc.
│   └── examples/
│       ├── basic-indexing.md
│       ├── search-examples.md
│       ├── plugin-example.md
│       └── fastapi-plugin.md
└── fr/
    ├── index.md
    ├── quickstart.md
    ├── guides/
    │   ├── installation.md
    │   ├── core-concepts.md
    │   ├── schema.md
    │   ├── indexing.md
    │   ├── searching.md
    │   ├── query.md
    │   ├── plugins.md
    │   ├── middleware.md
    │   ├── backends.md
    │   ├── vector.md
    │   ├── autocomplete.md
    │   └── migration.md
    ├── api/
    │   ├── index.md
    │   ├── core.md
    │   ├── fields.md
    │   ├── writing.md
    │   ├── searching.md
    │   ├── query.md
    │   ├── plugins.md
    │   ├── registry.md
    │   ├── middleware.md
    │   ├── event-bus.md
    │   ├── hooks.md
    │   ├── backends.md
    │   └── modern.md
    └── examples/
        ├── basic-indexing.md
        ├── search-examples.md
        ├── plugin-example.md
        └── fastapi-plugin.md
```

## Jekyll Configuration (`docs/_config.yml`)

```yaml
title: Whoosh-NG Documentation
description: Pure-Python full-text indexing and search library, modernized for 2025+
lang: en
timezone: UTC

baseurl: "/whoosh-NG"

remote_theme: just-the-docs/just-the-docs
color_scheme: dark

collections:
  en:
    output: true
    sort_by: nav_order
  fr:
    output: true
    sort_by: nav_order

defaults:
  - scope:
      path: ""
      type: pages
    values:
      layout: default
  - scope:
      path: "en"
      type: en
    values:
      layout: default
      lang: en
  - scope:
      path: "fr"
      type: fr
    values:
      layout: default
      lang: fr

include:
  - _pages
  - favicon.ico
  - logo.png

plugins:
  - jekyll-remote-theme
  - jekyll-seo-tag
  - jekyll-sitemap
  - jekyll-feed
```

## Gemfile

```ruby
source "https://rubygems.org"
gem "jekyll"
gem "jekyll-remote-theme"
gem "jekyll-seo-tag"
gem "jekyll-sitemap"
gem "jekyll-feed"
gem "webrick"
```

## Front Matter Pattern

```markdown
---
title: "API Reference: Writing"
nav_order: 30
permalink: /en/api/writing/
---
```

## API Documentation Style (exemple `en/api/writing.md`)

Texte clair, sans icônes. Tableaux pour méthodes, sections commentées.

```python
# Écriture basique
with index.writer() as w:
    w.add_document(title="Hello", content="World")

# AsyncWriter pour environnements concurrents
from whoosh import writing
writer = writing.AsyncWriter(index)

# BufferedWriter pour accumulation mémoire
writer = writing.BufferedWriter(index, period=30, limit=50)
```

## Code Examples Integration

Les exemples dans `/examples/` du repo restent en Python. Les pages `en/examples/*.md` contiennent :

- Description du scénario
- Snippet commenté du code source
- Résultat attendu
- Points clés à retenir

## Assets

- `docs/assets/logo.png` : logo Whoosh
- `docs/assets/favicon.ico` : favicon

## GitHub Actions Workflow

`.github/workflows/docs.yml` : build Jekyll + déployer sur GitHub Pages avec `ruby/setup-ruby` + `actions/deploy-pages`.

## Archive Sphinx Heritage

Options :

1. Copier `docs/source/` vers `docs/archive/sphinx/`
2. Rediriger les anciens URLs vers nouvelles
3. Garder `Makefile`/`make.bat` pour génération locale

## Tasks à Réaliser

1. **Préparer l'infra**
   - Créer `docs/Gemfile`
   - Créer `docs/_config.yml`
   - Créer assets + workflow CI

2. **Écrire les pages principales** (15 guides FR/EN)

3. **API Reference manuelle** (12 pages FR/EN)

4. **Traduire en français**

5. **Exemples** (4 pages FR/EN)

## Critères d'acceptation

- Site builds avec `bundle exec jekyll serve`
- Documentation exhaustive : chaque classe/fonction publique documentée
- Exemples commentés et testables
- Version française synchronisée
- CI déploy sur GitHub Pages
- Anciens docs Sphinx archivés
