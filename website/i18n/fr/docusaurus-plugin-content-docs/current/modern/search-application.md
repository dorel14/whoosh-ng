---
title: "SearchApplication"
sidebar_position: 21
---

# SearchApplication

Module : `whoosh_modern.application`
Version : 3.2.0

`SearchApplication` est le **point d'entrée unifié** de Whoosh-NG. Il orchestre l'ensemble du pipeline d'indexation et de recherche, depuis une `DataSource` jusqu'à un index Whoosh interrogeable : découverte de schéma, validation, résolution du stockage, composition des middleware, création de l'index et exécution des requêtes.

## Architecture

```text
DataSource (SQL, JSON, REST, CSV, …)
    │
    ▼
SearchApplication
    │
    ├── source.discover_schema() ──► Schéma Whoosh
    │
    ├── storage._resolve_index_path() ──► chemin fichiersystem
    │       │
    │       ├── FileStorageProvider ──► provider.root
    │       └── Autres providers ──► tempfile.mkdtemp()
    │
    ├── SearchView.build(path)
    │       │
    │       ├── MiddlewareChain.before_index()
    │       │   ├── StorageMiddleware
    │       │   ├── EmbeddingMiddleware (optionnel)
    │       │   ├── StemmingMiddleware
    │       │   └── SynonymExpansionMiddleware
    │       │
    │       ├── for doc in source.iter_documents():
    │       │       writer.add_document(**prepared_doc)
    │       │
    │       └── writer.commit()
    │
    ▼
Index Whoosh (segments sur disque / S3 / cache hybride)
```

## Démarrage rapide

```python
from whoosh_modern import SearchApplication, SQLSource
from whoosh_modern.storage import FileStorage
import sqlite3

engine = sqlite3.connect("products.db")
app = SearchApplication(
    source=SQLSource(query="SELECT * FROM products", connection=engine),
    storage=FileStorage("indexdir"),
)
app.build()
results = app.search("laptop")
for hit in results:
    print(hit["title"])
```

## Constructeur

```python
SearchApplication(
    source: DataSource | None = None,
    storage: SyncStorageProvider | None = None,
    wiktionary_indexer: WiktionaryIndexer | None = None,
    language_detector: LanguageDetector | None = None,
    dictionary_stem_overrides: dict[str, str] | None = None,
    embedding_provider: Any | None = None,
    embedding_fields: list[dict[str, str]] | None = None,
)
```

### Paramètres

| Paramètre | Type | Description |
|-----------|------|-------------|
| `source` | `DataSource \| None` | Source de données fournissant les documents à indexer. Requis pour `build()`. |
| `storage` | `SyncStorageProvider \| None` | Backend de stockage pour les fichiers d'index. Si c'est un `FileStorageProvider`, son attribut public `root` est utilisé comme répertoire d'index. Sinon, un répertoire temporaire est créé. |
| `wiktionary_indexer` | `WiktionaryIndexer \| None` | Indexeur Wiktionary dont les synonymes seront chargés dans le middleware d'expansion de synonymes lors du premier accès. |
| `language_detector` | `LanguageDetector \| None` | Détecteur de langue utilisé lorsque `language="auto"` est défini sur les champs. Lorsqu'il est fourni, le détecteur est appelé sur chaque document pour résoudre la langue et injecter un champ stocké `_language`. |
| `dictionary_stem_overrides` | `dict[str, str] \| None` | Mapping mot → forme stemmée pour remplacer le stemmer Snowball par défaut. |
| `embedding_provider` | `Any \| None` | Fournisseur d'embeddings utilisé pour enrichir les documents avec des vecteurs denses avant l'indexation. |
| `embedding_fields` | `list[dict[str, str]] \| None` | Séquence de mappings `{"source_field": "...", "target_field": "..."}` pour l'embedding multi-champs. Lorsque fourni, les valeurs par défaut `source_field` / `target_field` de la configuration d'embedding sont ignorées. |

## Propriétés

### `index`

```python
@property
def index(self) -> Index
```

Retourne l'`Index` Whoosh construit.

Lève `RuntimeError` si `build()` n'a pas été appelé.

### `language_detector`

```python
@property
def language_detector(self) -> LanguageDetector | None
```

Retourne le détecteur de langue configuré, ou `None` si aucun n'a été fourni.

### `synonym_manager`

```python
@property
def synonym_manager(self) -> SynonymManager
```

Retourne le `SynonymManager` peuplé à partir de l'index Wiktionary. Si un `wiktionary_indexer` a été fourni lors de la construction, le manager est peuplé paresseusement lors du premier accès, même si `build()` n'a pas été appelé. Si aucun indexer n'a été fourni, un manager vide est retourné.

## Méthodes

### `build()`

```python
def build(self) -> SearchApplication
```

Construit l'index à partir de la source de données.

1. Résout le chemin d'index à partir du provider de stockage.
2. Découvre le schéma depuis la source de données.
3. Crée un `SearchView` et attache optionnellement `EmbeddingMiddleware`.
4. Exécute la validation.
5. Crée ou ouvre l'index Whoosh.
6. Peuple l'index en itérant tous les documents.

Retourne `self` pour permettre le chaînage.

Lève `ValueError` si aucune source de données n'a été fournie.

### `search()`

```python
def search(self, query: Any, **kwargs: Any) -> Any
```

Recherche dans l'index.

- Si `query` est une chaîne, elle est analysée en utilisant `QueryParser` avec le premier champ du schéma comme champ par défaut.
- Ouvre un searcher et délègue à `searcher.search()`.

Retourne les résultats de recherche du searcher Whoosh.

Lève `RuntimeError` si `build()` n'a pas été appelé.

## Exemples d'utilisation

### Avec stockage local

```python
from whoosh_modern import SearchApplication, SQLSource
from whoosh_modern.storage import FileStorage
import sqlite3

engine = sqlite3.connect("products.db")
app = SearchApplication(
    source=SQLSource(query="SELECT * FROM products", connection=engine),
    storage=FileStorage("indexdir"),
)
app.build()
results = app.search("laptop")
```

### Avec stockage hybride S3

```python
from whoosh_modern import SearchApplication, SQLSource
from whoosh_modern.storage import HybridStorage, S3Storage

remote = S3Storage(bucket="my-index-bucket", prefix="segments")
storage = HybridStorage(local_cache="./cache", remote=remote)

app = SearchApplication(
    source=SQLSource(query="SELECT * FROM products", connection=engine),
    storage=storage,
)
app.build()
results = app.search("laptop")
```

### Avec détection de langue

```python
from whoosh_modern import SearchApplication
from whoosh_modern.linguistics.detection import StopwordDetector
from whoosh_modern.data_sources.json import JSONSource

detector = StopwordDetector(["fr", "en", "de"])
source = JSONSource("data/products.json")

app = SearchApplication(
    source=source,
    language_detector=detector,
)
app.build()
```

Lorsque les champs sont configurés avec `language="auto"`, le détecteur résout la langue à partir du contenu du document et injecte un champ stocké `_language`.

### Avec synonymes Wiktionary

```python
from whoosh_modern import SearchApplication
from whoosh_modern.linguistics.wiktionary_indexer import WiktionaryIndexer

indexer = WiktionaryIndexer(language="en")
indexer.build()

app = SearchApplication(
    source=source,
    wiktionary_indexer=indexer,
)
app.build()

# Accéder au synonym_manager peuplé
synonym_manager = app.synonym_manager
```

### Avec remplacements de stemming personnalisés

```python
from whoosh_modern import SearchApplication

app = SearchApplication(
    source=source,
    dictionary_stem_overrides={
        "mice": "mouse",
        "geese": "goose",
    },
)
app.build()
```

## SearchApplication vs SearchView

`SearchApplication` est un wrapper simplifié autour de `SearchView`. Utilisez `SearchApplication` pour la plupart des cas de production. Utilisez `SearchView` directement lorsque vous avez besoin d'un contrôle plus fin du cycle de vie d'indexation.

| Fonctionnalité | SearchApplication | SearchView |
|----------------|-------------------|------------|
| Découverte de schéma | ✅ automatique | ✅ automatique |
| Validation | ✅ automatique | ✅ automatique |
| Rafraîchissement incrémental | ❌ | ✅ `refresh()` |
| Réindexation complète | ❌ | ✅ `reindex()` |
| Évolution de schéma | ❌ | ✅ `evolve_schema()` |
| Middleware personnalisé | ❌ | ✅ `middleware=` |
| Facettes | ❌ | ✅ `facets=` |
| Remplacements de champs | ❌ | ✅ `fields=` |
| Intégration du stockage | ✅ automatique | ✅ via `StorageMiddleware` |

## Fonctionnement de l'intégration du stockage

Lorsque `storage` est un `FileStorageProvider` (exposé sous le nom `FileStorage`), `SearchApplication` utilise son attribut public `root` comme répertoire d'index. Pour tous les autres providers (S3, Hybride, Snapshot), il se rabat sur un répertoire temporaire car Whoosh core nécessite un chemin filesystem pour `create_in()`.

Le routage réel des segments, le pointage de commit et la synchronisation du cache sont gérés par `StorageMiddleware` au niveau middleware, et non par le provider de stockage lui-même.

## Voir aussi

- [SearchView](/examples/search-view) — Vue de bas niveau avec rafraîchissement, réindexation et validation
- [Fournisseurs de stockage](/modern/storage-providers) — Backends de stockage enfichables
- [Pipeline de middleware](/modern/middleware-pipeline) — Hooks d'indexation et de recherche transverses
- [Linguistique](/modern/linguistics) — Détection de langue et expansion de synonymes
- [Intégration des providers](/modern/provider-integration) — Guide de pipeline de bout en bout
- [Auto-indexation](/modern/auto-indexing) — Découverte de schéma et indexation pilotée par source de données
