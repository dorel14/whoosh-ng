---
title: "API Moderne"
nav_order: 190
lang: fr
---

# API Moderne

Sources de données, découverte de schéma, facettes, validation, middleware et SearchView.

## DataSource Protocol

```python
from whoosh_modern.data_sources import DataSource, SQLSource, RESTSource
```

### SQLSource

```python
source = SQLSource(
    connection=conn,
    query="SELECT * FROM reuters_articles",
    incremental_field="article_date",
    id_field="id",
)
schema = source.discover_schema()
docs = list(source.iter_documents())
```

### RESTSource

```python
source = RESTSource(
    url="https://api.example.com/v2/products",
    pagination="page",
    page_size=50,
)
schema = source.discover_schema()
docs = list(source.iter_documents())
```

## SchemaDiscovery

```python
from whoosh_modern.schema_discovery import SchemaDiscovery

schema = SchemaDiscovery.from_result_set(columns)
schema = SchemaDiscovery.from_sample(docs)
id_field = SchemaDiscovery.detect_id_field(dict(schema))
```

## FacetManager

```python
from whoosh_modern.facets import FacetManager

manager = FacetManager(schema)
facets = manager.get_facets()
manager.set_manual_override("price", {"type": "range"})
```

## ValidationFramework

```python
from whoosh_modern.validation import ValidationFramework, ValidationResult

validator = ValidationFramework()
results = validator.validate(source)
```

## Middleware Pipeline

```python
from whoosh_modern.middleware import MiddlewarePipeline, RetryMiddleware, LoggingMiddleware

pipeline = MiddlewarePipeline(
    RetryMiddleware(attempts=3, backoff="exponential"),
    LoggingMiddleware(),
)
result = pipeline.execute(operation)
```

## SearchView

```python
from whoosh_modern.views import SearchView

view = SearchView(name="reuters", source=source)
ix = view.build("indexdir")
count = view.reindex()
results = view.validate()
```

## Fournisseurs de stockage

```python
from whoosh_modern.storage import (
    FileStorage,
    AsyncFileStorage,
    S3Storage,
    HybridStorage,
    AsyncHybridStorage,
)
```

### FileStorage

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

### AsyncFileStorage

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

### S3Storage

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

### HybridStorage

Compose un cache local avec un backend distant pour des indexes cloud-native.
Le distant est la source de vérité ; le cache local est une couche de
performance write-through.

```python
from whoosh_modern.storage import HybridStorage, S3Storage

distant = S3Storage(bucket="mon-bucket", prefix="segments")
stockage = HybridStorage(local_cache="./cache", remote=distant)

stockage.write("segment_1.dat", b"data")
data = stockage.read("segment_1.dat")  # servi depuis le cache après le premier accès
stockage.invalidate("segment_1.dat")   # forcer le rafraîchissement depuis le distant
stockage.prefetch(["segment_2.dat"])   # préchauffer le cache
```

Chemin de lecture :

1. hit cache local → retour immédiat
2. miss → lecture depuis le distant, write-through dans le cache, retour

Chemin d'écriture :

- ``distant.write(key, data)`` (source de vérité)
- en cas de succès → ``local_cache.write(key, data)``
- en cas d'échec → lever l'erreur avant de polluer le cache

### AsyncHybridStorage

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

asyncio.run(main())
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
