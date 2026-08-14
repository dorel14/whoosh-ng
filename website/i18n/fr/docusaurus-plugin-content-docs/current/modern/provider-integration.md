---
title: "Intégration des Providers"
sidebar_position: 85
---

# Intégration des Providers : Guide Complet du Pipeline

Module: `whoosh_modern.storage`, `whoosh_modern.analysis.stemmer_providers`, `whoosh_modern.linguistics.synonyms`, `whoosh_modern.vector`, `whoosh_modern.autocomplete`
Version: 2.0.0

Ce guide explique comment tous les providers de Whoosh-NG s'intègrent dans le
pipeline d'indexation et de recherche. Il est la référence définitive pour
comprendre le flux de données des documents bruts aux résultats de recherche.

## Vue d'ensemble

Whoosh-NG utilise un **pattern de provider** pour garder le moteur de recherche
léger tout en activant un comportement pluggable pour le stockage, l'analyse de
texte, la recherche vectorielle et l'autocomplétion.

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Pile de Providers Whoosh-NG                   │
│                                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌───────────┐ │
│  │ Stockage    │  │ Stemmer      │  │ Synonyme    │  │ Vecteur   │ │
│  │ Providers   │  │ Providers    │  │ Providers   │  │ Providers │ │
│  │             │  │              │  │             │  │           │ │
│  │ FileStorage │  │ Internal     │  │ Static      │  │ Numpy     │ │
│  │ S3Storage   │  │ PyStemmer    │  │ YAML        │  │ HNSW      │ │
│  │ Hybride     │  │ Identity     │  │ JSON        │  │ Faiss     │ │
│  │ SQLite      │  │ Custom       │  │ SQLite      │  │ Qdrant    │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬─────┘ │
│         │                │                │                │       │
│         ▼                ▼                ▼                ▼       │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │              Pipeline de Middleware (hooks)                     ││
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐    ││
│  │  │Stockage     │  │Stemming      │  │Synonyme             │    ││
│  │  │Middleware   │  │Middleware    │  │ExpansionMiddleware  │    ││
│  │  └─────────────┘  └──────────────┘  └─────────────────────┘    ││
│  └─────────────────────────────────────────────────────────────────┘│
│                              │                                       │
│                              ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │              Moteur Core Whoosh                                 ││
│  │  Index │ Writer │ Searcher │ QueryParser │ Fichiers segment     ││
│  └─────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────┘
```

## Pipeline d'Indexation Complet

### Flux étape par étape

```text
┌─────────────────┐
│   DataSource    │  (SQL, JSON, REST, CSV, DataFrame, etc.)
│   .stream_batches() │
└────────┬────────┘
         │ lots de documents
         ▼
┌─────────────────┐
│  SchemaDiscovery │  Infère le schéma Whoosh depuis les colonnes de la source
│  .discover_schema() │
└────────┬────────┘
         │ Schema(TEXT, ID, NUMERIC, VECTOR, ...)
         ▼
┌─────────────────────────────────────────┐
│  Résolution du Provider de Stockage      │
│                                         │
│  storage._root (si présent)             │
│    └──► whoosh.index.create_in(root)    │
│  Pas de root                             │
│    └──► tempfile.mkdtemp() → create_in() │
└────────┬────────────────────────────────┘
         │ Instance Index
         ▼
┌─────────────────────────────────────────┐
│  Writer + MiddlewareChain                │
│                                         │
│  chain.run_before("before_index")        │
│    ├── StorageMiddleware                 │
│    │   └── marque le contexte            │
│    ├── StemmingMiddleware                │
│    │   └── stemme les champs             │
│    └── SynonymExpansionMiddleware        │
│        └── expande les champs            │
│                                         │
│  writer.add_document(**doc)              │
│    └── Whoosh core applique les analyzeurs│
│        (TEXT.analyzer)                    │
│        et écrit le segment               │
│                                         │
│  writer.commit()                         │
│    └── chain.run_after("on_commit")      │
│        └── StorageMiddleware             │
│            └── écrit un point de commit  │
└────────┬────────────────────────────────┘
         │ Fichiers segment sur le disque/S3/cache
         ▼
┌─────────────────┐
│  Index Whoosh    │
│  (segments)      │
└─────────────────┘
```

### Exemple concret

```python
from whoosh import index, fields
from whoosh_modern import (
    SearchApplication,
    SQLSource,
    HybridStorage,
    S3Storage,
    StemmingAnalyzer,
    get_stemmer,
    SynonymManager,
    SynonymExpansionMiddleware,
    StorageMiddleware,
    StemmingMiddleware,
)
from sqlalchemy import create_engine

# 1. Source de données
engine = create_engine("sqlite:///products.db")
source = SQLSource(query="SELECT id, name, description FROM products", connection=engine)

# 2. Stockage
remote = S3Storage(bucket="my-index-bucket", prefix="segments")
storage = HybridStorage(local_cache="./cache", remote=remote)

# 3. Schéma (auto-découvert des colonnes SQL)
#    Mais on personnalise l'analyseur
stemmer = get_stemmer("auto", "english")
schema = fields.Schema(
    name=fields.TEXT(analyzer=StemmingAnalyzer(stemmer=stemmer), stored=True),
    description=fields.TEXT(analyzer=StemmingAnalyzer(stemmer=stemmer)),
    id=fields.ID(stored=True, unique=True),
)

# 4. Créer l'index dans la racine du stockage
ix = index.create_in(storage._cache_root, schema)

# 5. Construire la chaîne de middleware
syn_manager = SynonymManager({"laptop": ["notebook", "portable"]})
chain = MiddlewareChain([
    StorageMiddleware(storage, name="products"),
    StemmingMiddleware(stemmer=stemmer.stem),
    SynonymExpansionMiddleware(syn_manager),
])

# 6. Indexer avec le middleware
with MiddlewareWriter(ix.writer(), chain) as writer:
    for batch in source.stream_batches():
        for doc in batch:
            writer.add_document(**doc)
    writer.commit()
```

## Pipeline de Recherche Complet

### Flux étape par étape

```text
┌─────────────────┐
│   Requête Utilisateur │  "running cats"
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  MiddlewareChain.run_before("search")    │
│                                         │
│  ├── StemmingMiddleware                  │
│  │   └── "running cats" → "run cat"      │
│  ├── SynonymExpansionMiddleware          │
│  │   └── "run cat" → "run cat running feline" │
│  └── QueryRewriteMiddleware              │
│      └── réécritures personnalisées      │
└────────┬────────────────────────────────┘
         │ Requête modifiée
         ▼
┌─────────────────────────────────────────┐
│  QueryParser.parse(query)                │
│    └── Objet Query (Term, And, Or...)    │
└────────┬────────────────────────────────┘
         │ Objet Query
         ▼
┌─────────────────────────────────────────┐
│  Searcher.search(query)                  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  Chemin de recherche par mot-clé  │  │
│  │  └── lit les listes de postings │  │
│  │      depuis les fichiers segment   │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  Chemin de recherche vectorielle  │  │
│  │  └── VectorRegistry.get(provider) │  │
│  │      └── NumpyProvider.search()   │  │
│  │          └── similarité cosinus   │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  Chemin d'autocomplétion            │  │
│  │  └── AutocompleteRegistry.get()   │  │
│  │      └── provider.suggest()       │  │
│  └───────────────────────────────────┘  │
└────────┬────────────────────────────────┘
         │ Résultats bruts
         ▼
┌─────────────────────────────────────────┐
│  MiddlewareChain.run_after("search")     │
│                                         │
│  └── RankingMiddleware                   │
│      └── réclasse les résultats          │
└────────┬────────────────────────────────┘
         │ Résultats finaux
         ▼
┌─────────────────┐
│  Hits retournés   │
└─────────────────┘
```

### Exemple concret

```python
from whoosh.qparser import QueryParser
from whoosh_modern.middleware import (
    StemmingMiddleware,
    RankingMiddleware,
    QueryRewriteMiddleware,
)
from whoosh_modern.analysis import get_stemmer
from whoosh_modern.vector import NumpyProvider
from whoosh_modern.vector.plugin import VectorPlugin
from whoosh.plugins.manager import PluginManager
import numpy as np

# 1. Configurer les plugins au démarrage
manager = PluginManager()
VectorPlugin().register(manager)

# 2. Ouvrir l'index
ix = index.open_dir("indexdir")

# 3. Construire la chaîne de middleware
stemmer = get_stemmer("auto", "english")
chain = MiddlewareChain([
    StemmingMiddleware(stemmer=stemmer.stem),
    QueryRewriteMiddleware(rewriter=lambda q: q + " portable"),  # ajouter synonyme
    RankingMiddleware(ranker=lambda r: sorted(r, key=lambda h: h.score, reverse=True)),
])

# 4. Rechercher avec le middleware
with MiddlewareSearcher(ix.searcher(), chain) as searcher:
    # La requête est transformée par le middleware avant l'exécution
    results = searcher.search("laptop")
    for hit in results:
        print(f"{hit['name']}: {hit.score:.4f}")

    # 5. Recherche vectorielle (parallèle)
    query_vec = np.random.rand(384).tolist()
    vector_results = searcher.vector_search("embedding", query_vec, limit=10)
    for hit in vector_results:
        print(f"doc_id={hit.doc_id}, score={hit.score:.4f}")
```

## Matrice de Comparaison des Providers

| Aspect | Stockage | Stemmer | Synonyme | Vecteur | Autocomplétion |
|--------|----------|---------|----------|---------|----------------|
| **Point d'intégration** | `StorageMiddleware` + `create_in()` | `StemmingAnalyzer` (champ) + `StemmingMiddleware` | `SynonymExpansionMiddleware` | `VectorRegistry` + format de segment | `AutocompleteRegistry` + autonome |
| **Enregistrement** | Manuel ou `__getattr__` | Décorateur `register_stemmer()` | CRUD `SynonymManager` | `VectorPlugin.register()` | `AutocompletePlugin.register()` |
| **Utilisé à l'indexation** | Oui (points de commit) | Oui (analyseur de champ + middleware) | Oui (before_index) | Oui (champ VECTOR) | Non (autonome ou post-indexation) |
| **Utilisé à la recherche** | Oui (lectures de segments via le système de fichiers) | Oui (analyseur de champ + middleware) | Oui (before_search) | Oui (vector_search) | Oui (suggest/search) |
| **Persistance** | Fichiers segment / S3 / SQLite | En mémoire (sans état) | En mémoire / YAML / JSON / SQLite | Fichiers segment (métadonnées) | En mémoire (liste de phrases) |
| **Configuration** | Classe provider + kwargs | Nom du backend + langue | Dict de mapping ou fichier | Nom du provider + métrique | Type de provider + paramètres |

## Patterns Communs

### Pattern 1 : Provider comme Analyseur de Champ

Utilisé par: Stemmer providers, analyzeurs linguistiques

```python
schema = Schema(
    content=TEXT(analyzer=StemmingAnalyzer(stemmer="auto"))
)
```

Le provider est encapsulé dans un analyzeur Whoosh et appliqué automatiquement.

### Pattern 2 : Provider comme Middleware

Utilisé par: Stockage, Stemmer, Synonymes

```python
chain = MiddlewareChain([
    StorageMiddleware(storage),
    StemmingMiddleware(stemmer=stemmer.stem),
    SynonymExpansionMiddleware(manager),
])
```

Le provider est consommé par des hooks de middleware dans le pipeline.

### Pattern 3 : Provider comme Entrée du Registre

Utilisé par: Vecteur, Autocomplétion

```python
VectorRegistry.register("numpy", NumpyProvider(), owner="my_app")
provider = VectorRegistry.get("numpy", "my_app")
```

Le provider est stocké dans un registre global et résolu par nom à l'exécution.

### Pattern 4 : Provider comme Service Autonome

Utilisé par: Autocomplétion, Vecteur (mode manuel)

```python
provider = NumpyProvider()
provider.add([(doc_id, vec)])
results = provider.search(query_vec)
```

Le provider fonctionne indépendamment de l'index/searcher Whoosh.

## Bonnes Pratiques

1. **Choisir le bon pattern d'intégration** : Les analyseurs de champs pour les schémas statiques, le middleware pour le comportement dynamique, le registre pour les backends interchangeables.
2. **Éviter les double-applications** : Ne pas utiliser à la fois les analyseurs de niveau champ et le middleware pour la même transformation (ex: stemming).
3. **Enregistrer les providers au démarrage** : Appeler `VectorPlugin().register(manager)` et `AutocompletePlugin().register(manager)` avant de créer les index.
4. **Utiliser l'API de plus haut niveau quand c'est possible** : [`SearchApplication`](/modern/search-application) pour le bout en bout, `create_autocomplete()` pour les suggestions, `get_stemmer()` pour le stemming.
5. **Garder les providers sans état** : Les providers ne devraient pas contenir d'état spécifique à l'index; utilisez le contexte de middleware pour les données par requête.
6. **Tester les providers en isolation** : Chaque provider devrait être testable sans Whoosh core (tests unitaires pour `provider.search()`, `provider.add()`).
7. **Documenter les dépendances des providers** : Noter les dépendances optionnelles (boto3, PyStemmer, PyYAML) dans les exigences de votre projet.

## Voir Aussi

- [Guide des Fournisseurs de Stockage](storage-providers.md) — Intégration des backends de stockage
- [Guide des Stemmers](stemmers-fournisseurs.md) — Intégration des fournisseurs de stemmers
- [Guide de Recherche Vectorielle](vector.md) — Intégration des fournisseurs de vecteurs
- [Guide d'Autocomplétion](autocomplete-providers.md) — Intégration des fournisseurs d'autocomplétion
- [Guide Middleware](middleware-pipeline.md) — Pipeline hooks et adaptateurs de providers
- [Guide Plugins](plugins-advanced.md) — Enregistrement et entry points des plugins
- [API: Moderne](../api/modern.md) — Référence complète de l'API pour tous les providers
