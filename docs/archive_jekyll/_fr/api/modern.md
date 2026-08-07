---
title: "Fournisseurs de stockage"
nav_order: 210
lang: fr
---

# Fournisseurs de stockage

Whoosh-NG fournit des backends de stockage pluggables via les contrats
`SyncStorageProvider` / `AsyncStorageProvider`. Cela permet de persister
l'index sur disque local, SQLite, S3, ou une configuration hybride cache +
distant sans modifier le writer ni l'index.

## Vue d'ensemble de l'architecture

### Niveau 1 : SnapshotStorage (Simple)

```
Writer → FS local → Commit → Upload Segment → S3
Reader → Download Segment → Open local
```

Très simple à maintenir. Utilisez `SnapshotStorage` quand vous voulez S3
comme cible de sauvegarde/restauration simple sans la complexité d'un cache
local.

### Niveau 2 : CachedObjectStorage (Recommandé pour la production)

```
+----------+
|  MinIO   |
+----------+
     ^
     |
 Sync |
     v
+-----------+   Couche Cache   +-----------+
| Searcher  |<--------------->| Writer    |
+-----------+                 +-----------+
        |
        v
 Local SSD
```

- L'index vit sur SSD
- S3 sert de réplication
- Les segments sont poussés après commit
- Restauration possible à tout moment

C'est exactement ce que font beaucoup de systèmes de recherche distribués
modernes.

## Fournisseurs disponibles

| Fournisseur | Type | Backend | Cas d'usage |
|-------------|------|---------|-------------|
| `FileStorage` | sync | système de fichiers local | Single-node, pas de cloud |
| `AsyncFileStorage` | async | système de fichiers local | Single-node async |
| `S3Storage` | sync | compatible S3 | Accès S3 direct |
| `SnapshotStorage` | sync | compatible S3 | Sauvegarde/restauration simple |
| `HybridStorage` | sync | cache local + distant | **Production** (alias : `CachedObjectStorage`) |
| `AsyncHybridStorage` | async | cache local + distant | Production async |

Tous les fournisseurs sont importables depuis `whoosh_modern.storage`.

## FileStorage

Stockage local sur système de fichiers. Les clés sont des chemins relatifs
sous ``root``.

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

Variante async de ``FileStorage``. Toutes les opérations s'exécutent dans
un thread de travail via ``asyncio.to_thread``.

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

Stockage blobs compatible S3. ``boto3`` est requis uniquement lorsque ce
fournisseur est utilisé ; il est importé paresseusement pour que le reste
de Whoosh-NG n'en dépende pas. Un ``client`` peut être injecté pour les tests.

```python
from whoosh_modern.storage import S3Storage

storage = S3Storage(bucket="mon-bucket", prefix="segments")
storage.write("segment_1.dat", b"data")
data = storage.read("segment_1.dat")
keys = storage.list_keys()
```

Installer la dépendance optionnelle :

```bash
pip install whoosh-ng[s3]
```

## SnapshotStorage

Stockage snapshot S3 simple sans cache local. C'est la stratégie la plus
simple :

- Écriture : upload du segment directement vers S3
- Lecture : download du segment depuis S3 vers un fichier temporaire local

Utilisez ceci quand vous voulez S3 comme cible de sauvegarde/restauration
simple sans la complexité d'un cache local.

```python
from whoosh_modern.storage import SnapshotStorage

storage = SnapshotStorage(
    local_path="./index",
    bucket="mon-bucket",
    prefix="snapshots",
)

storage.write("segment_1.dat", b"data")
data = storage.read("segment_1.dat")
```

## HybridStorage / CachedObjectStorage

`HybridStorage` compose un cache local avec un backend distant. Le distant
est la source de vérité ; le cache local est une couche de performance
write-through.

`CachedObjectStorage` est un alias de `HybridStorage` qui exprime mieux
l'intention : un cache d'objets local synchronisé avec S3.

C'est l'architecture recommandée pour les déploiements production avec des
motifs de lecture répétés.

```python
from whoosh_modern.storage import HybridStorage, S3Storage

distant = S3Storage(bucket="mon-bucket", prefix="segments")
stockage = HybridStorage(local_cache="./cache", remote=distant)

# Write-through : le distant est la source de vérité, le cache est mis à jour
stockage.write("segment_1.dat", b"data")

# Première lecture : miss cache → fetch depuis S3, write-through dans le cache
data = stockage.read("segment_1.dat")

# Deuxième lecture : hit cache → servi depuis le disque local, zéro réseau
data = stockage.read("segment_1.dat")

# Forcer le rafraîchissement depuis le distant
stockage.invalidate("segment_1.dat")

# Pré-chauffer le cache
stockage.prefetch(["segment_2.dat", "segment_3.dat"])
```

### Chemin de lecture

1. hit cache local → retour immédiat
2. miss → lecture depuis le distant, write-through dans le cache, retour

### Chemin d'écriture

- ``distant.write(key, data)`` (source de vérité)
- en cas de succès → ``local_cache.write(key, data)``
- en cas d'échec → lever l'erreur avant de polluer le cache

### Éviction du cache

Le cache local est limité par `max_cache_size_mb` (défaut 1024 Mo). Quand
la limite est atteinte, les entrées les plus anciennes sont évincées selon
une politique LRU.

### `list_keys`

`list_keys()` utilise le distant comme source de vérité car le cache n'est
que partiel. Passez `include_cache=True` pour retourner l'union des clés
distant et cache.

## AsyncHybridStorage

Variante async de ``HybridStorage``. Les opérations distantes s'exécutent
dans un thread de travail via ``asyncio.to_thread`` pour ne jamais bloquer
la boucle d'événements.

```python
import asyncio
from whoosh_modern.storage import AsyncHybridStorage, S3Storage

distant = S3Storage(bucket="mon-bucket", prefix="segments")
stockage = AsyncHybridStorage(local_cache="./cache", remote=distant)

async def main() -> None:
    await stockage.awrite("segment_1.dat", b"data")
    data = await stockage.aread("segment_1.dat")
    await stockage.adelete("segment_1.dat")
    cles = await stockage.alist_keys()

asyncio.run(main())
```

## Utilisation avec SearchApplication

```python
from whoosh_modern import SearchApplication, SQLSource
from whoosh_modern.storage import HybridStorage, S3Storage

distant = S3Storage(bucket="mon-bucket", prefix="segments")
stockage = HybridStorage(local_cache="./cache", remote=distant)

app = SearchApplication(
    source=SQLSource(query="SELECT * FROM produits", connection=engine),
    storage=stockage,
)
app.build()
resultats = app.index.search("laptop")
```

## Benchmarks de performance

Les benchmarks ont été exécutés contre une instance MinIO locale en utilisant
un index Whoosh de 28,89 Mo (2 fichiers de segment). Les résultats indiquent
les performances relatives entre les stratégies sur un stockage compatible S3.

| Stratégie | Sauvegarde (Mo/s) | Restauration (Mo/s) | Notes |
|-----------|-------------------|---------------------|-------|
| `1_obj_per_segment` | 39.44 | 139.72 | Meilleur débit de restauration ; le plus simple |
| `compressed_zstd` | 31.56 | 133.74 | Bande passante réduite, overhead CPU |
| `hybrid_cache_s3` | 44.97 | 133.61 | Meilleure sauvegarde ; lectures cache chaud excellentes |
| `1_obj_per_posting_list` | 0.28 | 4.79 | **À éviter** : millions de petits objets tuent S3 |

### Recommandations

- **Par défaut** : `S3Storage` avec 1 objet par fichier de segment. Il offre
  le meilleur débit de restauration et est le plus simple à exploiter.
- **Production avec lectures répétées** : `HybridStorage(cache_local, S3Storage)`.
  Après le premier accès, les lectures suivantes sont servies depuis le disque
  local à ~133 Mo/s.
- **À éviter** : 1 objet par posting list. S3 n'est pas optimisé pour des
  millions de petits objets ; la latence et le coût explosent.
- **Compression** : ZSTD réduit la taille des transferts de ~20-30% au prix
  d'un overhead CPU. À utiliser quand la bande passante réseau est le
  goulot, pas quand le CPU l'est.

### Exécution des benchmarks

```bash
# Démarrer MinIO
docker run -d --name minio-benchmark -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio:latest server /data --console-address ":9001"

# Lancer le benchmark synthétique
python benchmark/s3_storage_benchmark.py

# Lancer le benchmark avec un vrai index Whoosh (nécessite le CSV customers)
python benchmark/s3_storage_benchmark_real.py
```
