---
title: 'Fournisseurs de stockage'
sidebar_position: 100
---

# Fournisseurs de stockage

Whoosh-NG fournit des backends de stockage modulaires via les contrats
`SyncStorageProvider` / `AsyncStorageProvider`. Cela permet de persister
l'index sur le disque local, SQLite, S3, ou une configuration hybride
(cache local + distant) sans modifier l'écrivain ou l'index.

## Aperçu de l'architecture

### Niveau 1 : SnapshotStorage (Simple)

```
Writer → Local FS → Commit → Upload Segment → S3
Reader → Download Segment → Open locally
```

Très simple à maintenir. Utilisez `SnapshotStorage` quand vous voulez
utiliser S3 comme cible de sauvegarde/restauration simple sans la
complexité d'un cache local.

### Niveau 2 : CachedObjectStorage (Recommandé pour la production)

```
+----------+
|  MinIO   |
+----------+
    ^
    |
Sync |
    v
+-----------+   Cache Layer   +-----------+
| Searcher  |<--------------->| Writer    |
+-----------+                 +-----------+
         |
         v
  Local SSD
```

- L'index réside sur un SSD
- S3 sert de réplication
- Les segments sont poussés après le commit
- La restauration est possible à tout moment

C'est ce que font de nombreux systèmes de recherche distribués modernes.

## Fournisseurs disponibles

| Fournisseur | Type | Backend | Cas d'utilisation |
|-------------|------|---------|--------------------|
| `FileStorage` | sync | système de fichiers local | Nœud unique, pas de cloud |
| `AsyncFileStorage` | async | système de fichiers local | Nœud unique async |
| `S3Storage` | sync | compatible S3 | Accès direct S3 |
| `SnapshotStorage` | sync | compatible S3 | Sauvegarde/restauration simple |
| `HybridStorage` | sync | cache local + distant | **Production** (alias : `CachedObjectStorage`) |
| `AsyncHybridStorage` | async | cache local + distant | Production async |

Tous les fournisseurs sont importables depuis `whoosh_modern.storage`.

## FileStorage

Stockage sur le système de fichiers local. Les clés sont des chemins
relatifs sous `root`.

```python
from whoosh_modern.storage import FileStorage

storage = FileStorage("indexdir")
storage.write("segment_1.dat", b"data")
assert storage.read("segment_1.dat") == b"data"
assert storage.exists("segment_1.dat") is True
storage.delete("segment_1.dat")
keys = storage.list_keys()
```

## AsyncFileStorage

 Variante asynce de `FileStorage`. Toutes les opérations s'exécutent sur
un thread de travail via `asyncio.to_thread` afin de ne jamais bloquer
la boucle d'événements.

```python
import asyncio
from whoosh_modern.storage import AsyncFileStorage

storage = AsyncFileStorage("indexdir")

async def main() -> None:
    await storage.awrite("segment_1.dat", b"data")
    data = await storage.aread("segment_1.dat")
    await storage.adelete("segment_1.dat")

asyncio.run(main())
```

## S3Storage

Stockage d'objets compatible S3. `boto3` est importé de manière paresseuse,
il s'agit donc d'une dépendance optionnelle. Un `client` peut être injecté
pour les tests.

```python
from whoosh_modern.storage import S3Storage

# Client par défaut (nécessite boto3 installé et configuré)
storage = S3Storage(bucket="my-index-bucket", prefix="segments")

# Ou injecter un client pour tests / configuration personnalisée
storage = S3Storage(
    bucket="my-index-bucket",
    prefix="segments",
    client=my_boto3_client,
)

storage.write("segment_1.dat", b"data")
data = storage.read("segment_1.dat")
keys = storage.list_keys()
```

Installez la dépendance optionnelle :

```bash
pip install whoosh-ng[s3]
```

## SnapshotStorage

Stockage d'instantané S3 simple sans cache local. C'est la stratégie de
stockage S3 la plus simple :

- Écriture : téléverse le segment directement vers S3
- Lecture : télécharge le segment depuis S3 vers un fichier temporaire local

Utilisez cela quand vous voulez utiliser S3 comme cible de
sauvegarde/restauration simple sans la complexité d'un cache local.

```python
from whoosh_modern.storage import SnapshotStorage

storage = SnapshotStorage(
    local_path="./index",
    bucket="my-index-bucket",
    prefix="snapshots",
)

storage.write("segment_1.dat", b"data")
data = storage.read("segment_1.dat")
```

## HybridStorage / CachedObjectStorage

`HybridStorage` compose un cache local et un backend distant. Le backend
distant est la source de vérité ; le cache local est un anneau de
performance en écriture-transparente.

`CachedObjectStorage` est un alias pour `HybridStorage` qui exprime
mieux l'intention : un cache d'objets local synchronisé avec S3.

C'est l'architecture recommandée pour les déploiements de production
avec des modèles de lecture répétés.

```python
from whoosh_modern.storage import HybridStorage, S3Storage

remote = S3Storage(bucket="my-index-bucket", prefix="segments")
storage = HybridStorage(local_cache="./cache", remote=remote)

# Write-through : le distant est la source de vérité, le cache est mis à jour en cas de succès
storage.write("segment_1.dat", b"data")

# Première lecture : cache manquant → récupère depuis S3, écrit dans le cache
data = storage.read("segment_1.dat")

# Deuxième lecture : cache hit → servi depuis le disque local, zéro réseau
data = storage.read("segment_1.dat")

# Forcer le rafraîchissement depuis le distant
storage.invalidate("segment_1.dat")

# Préchauffer le cache de manière proactive
storage.prefetch(["segment_2.dat", "segment_3.dat"])
```

### Chemin de lecture

1. cache local hit → retourne immédiatement
2. cache manquant → lit depuis le distant, écrit dans le cache, retourne

### Chemin d'écriture

- `remote.write(key, data)` (source de vérité)
- en cas de succès → `local_cache.write(key, data)`
- en cas d'échec → lève l'erreur avant de polluer le cache

### Éviction du cache

Le cache local est borné par `max_cache_size_mb` (par défaut 1024 Mo).
Lorsque la limite est atteinte, les entrées les plus anciennes sont
évictées selon une politique LRU.

### `list_keys`

`list_keys()` utilise le backend distant comme source de vérité car le
cache n'est qu'partiel. Passez `include_cache=True` pour retourner
l'union des clés distantes et du cache.

## AsyncHybridStorage

 Variante asynce de `HybridStorage`. Les opérations distantes sont
exécutées sur un thread de travail via `asyncio.to_thread` afin de ne
jamais bloquer la boucle d'événements.

```python
import asyncio
from whoosh_modern.storage import AsyncHybridStorage, S3Storage

remote = S3Storage(bucket="my-index-bucket", prefix="segments")
storage = AsyncHybridStorage(local_cache="./cache", remote=remote)

async def main() -> None:
    await storage.awrite("segment_1.dat", b"data")
    data = await storage.aread("segment_1.dat")
    await storage.adelete("segment_1.dat")
    keys = await storage.alist_keys()

asyncio.run(main())
```

## Benchmarks de performance

Les benchmarks ont été exécutés contre une instance MinIO locale en
utilisant un index Whoosh de 28,89 Mo (2 fichiers de segment). Les
résultats sont indicatives de la performance relative entre les
stratégies sur du stockage compatible S3.

| Stratégie | Sauvegarde (Mo/s) | Restauration (Mo/s) | Notes |
|-----------|-------------------|---------------------|-------|
| `1_obj_per_segment` | 39.44 | 139.72 | Meilleur débit de restauration ; le plus simple |
| `compressed_zstd` | 31.56 | 133.74 | Moins de bande passante, surcharge CPU |
| `hybrid_cache_s3` | 44.97 | 133.61 | Meilleur sauvegarde ; lectures excellentes avec cache chaud |
| `1_obj_per_posting_list` | 0.28 | 4.79 | **À éviter** : des millions de petits objets tuent S3 |

### Recommandations

- **Par défaut** : `S3Storage` avec 1 objet par fichier de segment. Offre
  le meilleur débit de restauration et est le plus simple à exploiter.
- **Production avec lectures répétées** : `HybridStorage(local_cache, S3Storage)`.
  Après la première lecture, les lectures suivantes sont servies depuis le
  disque local à ~133 Mo/s.
- **À éviter** : 1 objet par liste de postings. S3 n'est pas optimisé
  pour des millions de petits objets ; la latence et les coûts explosent.
- **Compression** : ZSTD réduit la taille de transfert d'environ 20-30%
  au coût du CPU. Utilisez-le quand la bande passante réseau est le
  goulot d'étranglement, pas quand c'est le CPU.

### Exécution des benchmarks

```bash
# Start MinIO
docker run -d --name minio-benchmark -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio:latest server /data --console-address ":9001"

# Run synthetic benchmark
python benchmark/s3_storage_benchmark.py

# Run real Whoosh index benchmark (requires customers CSV)
python benchmark/s3_storage_benchmark_real.py
```

## Comment les Fournisseurs de Stockage s'Intègre dans le Pipeline d'Indexation et de Recherche

Le fournisseur de stockage participe à deux phases distinctes : **la création de l'index** (déterminer où les segments vivent) et **l'intégration en temps réel** (via `StorageMiddleware`).

### Flux d'indexation complet avec un fournisseur de stockage

```text
DataSource.stream_batches()
    │
    ▼
SearchApplication.build()
    │
    ├── source.discover_schema() ──► Whoosh Schema
    │
    ├── résolution de storage._root
    │       │
    │       ├── HybridStorage/S3Storage/FileStorage
    │       │   └── a _root ? ──► whoosh.index.create_in(root, schema)
    │       │
    │       └── Pas de _root (S3 pur/SnapshotStorage)
    │           └── tempfile.mkdtemp() ──► create_in(tmpdir, schema)
    │
    ├── Writer = index.writer()
    │       │
    │       ├── MiddlewareChain.before_index()
    │       │   └── StorageMiddleware.before_index()
    │       │       ├── context.labels["storage_backend"] = provider.__class__.__name__
    │       │       └── context.metadata["storage_provider"] = self
    │       │
    │       ├── for batch in source.stream_batches():
    │       │       for doc in batch:
    │       │           writer.add_document(**doc)
    │       │
    │       └── writer.commit()
    │           │
    │           └── StorageMiddleware.on_commit()
    │               └── provider.write("commits/{name}/{timestamp}", b"1")
    │
    ▼
Index persistsé sur le disque / S3 / cache hybride
```

### Flux de recherche complet avec un fournisseur de stockage

```text
SearchApplication.search(query)
    │
    ├── index.searcher()
    │       │
    │       └── Whoosh core ouvre les fichiers segment depuis :
    │           ├── système de fichiers local (racine FileStorageProvider)
    │           ├── base de données SQLite (SQLiteStorageProvider)
    │           └── S3 / cache hybride (S3StorageProvider / HybridStorage)
    │
    ├── QueryParser.parse(query) ──► Objet Query
    │
    └── searcher.search(query)
        │
        └── Whoosh core lit les listes de postings depuis les fichiers segment
            └── Retourne Results (Hits)
```

### Hooks détaillés de StorageMiddleware

`StorageMiddleware` (`whoosh_modern.middleware.storage`) est le point d'intégration
qui redirige la persistance de l'index via n'importe quel `SyncStorageProvider` sans
modifier le writer.

| Hook | Quand | Ce qu'il fait |
|------|------|--------------|
| `before_index(context)` | Avant qu'un document soit ajouté | Marque le contexte avec l'étiquette `storage_backend` et les métadonnées `storage_provider` |
| `on_commit(context)` | Après `writer.commit()` | Écrit un point de commit (`commits/{name}/{timestamp}`) dans le provider |

### Insight clé : StorageProvider vs StorageMiddleware

| Composant | Rôle |
|-----------|------|
| `SyncStorageProvider` / `AsyncStorageProvider` | **Contrat** définissant `write()`, `read()`, `delete()`, `exists()`, `list_keys()` |
| `FileStorageProvider`, `S3StorageProvider`, `HybridStorage` | **Implémentations** du contrat |
| `StorageMiddleware` | **Couche d'intégration** qui appelle le provider aux hooks de cycle de vie (`before_index`, `on_commit`) |
| `SearchApplication` | **Point d'entrée** qui extrait `_root` du provider pour créer le répertoire d'index Whoosh. Voir [SearchApplication](/modern/search-application). |

Le provider ne **n'intercepte pas** les lectures internes de segments de Whoosh. Ces lectures passent par le `FileStorage` intégré de Whoosh (`whoosh.filedb.filestore`) qui lit depuis le chemin du système de fichiers donné à `create_in()`. L'abstraction provider de Whoosh-NG est conçue pour :
- Le routage personnalisé de segments (S3, SQLite, cache hybride)
- Le pointage de commit via le middleware
- Futur : l'interception de lectures/écritures au niveau des segments

## Voir Aussi

- [Intégration des Providers](provider-integration.md) — Guide complet du pipeline pour tous les providers
- [Guide Middleware](middleware-pipeline.md) — Pipeline hooks et adaptateurs de providers
