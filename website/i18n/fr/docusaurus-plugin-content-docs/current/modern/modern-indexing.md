---
title: "Indexation Moderne"
sidebar_position: 250
---

# Indexation Moderne

Whoosh-NG fournit une couche d'indexation optimisée dans `whoosh_modern.indexing` pour l'absorption de grands volumes de documents. Ces utilitaires encapsulent l'écrivain Whoosh de base sans modifier les internals de la bibliothèque.

## BatchIndexWriter

`BatchIndexWriter` encapsule un écrivain Whoosh avec les optimisations suivantes pour le traitement par lots de grands ensembles de données.

### Optimisations clés

- Pré-calcule les noms de champs du schéma pour un filtrage rapide (O(1) par champ)
- Ignore les champs non présents dans le schéma (évitant le surcoût par document)
- Utilise `multisegment=True` pour reporter les fusions pendant l'indexation
- Supporte des commits par lots configurables pour réduire la pression I/O
- Accepte un callback pour les hooks post-commit

### Utilisation de base

```python
from whoosh_modern.indexing import BatchIndexWriter
from whoosh import index

ix = index.open_dir("indexdir")

writer = BatchIndexWriter(ix, batch_size=5000, commit_every=10)

for batch in source.stream_batches(batch_size=5000):
    writer.add_batch(batch)

writer.close()
```

### Context Manager

```python
with BatchIndexWriter(ix, batch_size=10000) as writer:
    for doc in documents:
        writer.add_document(doc)
```

### Paramètres

| Paramètre | Par défaut | Description |
|-----------|---------|-------------|
| `batch_size` | 5000 | Nombre de documents par lot |
| `limitmb` | 512 | Limite mémoire pour l'écrivain (Mo) |
| `commit_every` | None | Commit après N lots (None = pas de commit auto) |
| `multisegment` | True | Utiliser le mode multisegment |
| `callback` | None | Callback invoqué après chaque commit |
| `**writer_kwargs` | None | Arguments supplémentaires pour `index.writer()` |

### Avec Commit Profiler

```python
from whoosh_modern.indexing import BatchIndexWriter
from whoosh_modern.profiling import CommitProfilerV2

profiler = CommitProfilerV2()
with BatchIndexWriter(ix, batch_size=5000, commit_every=5, commit_profiler=profiler) as writer:
    for batch in source.stream_batches(batch_size=5000):
        writer.add_batch(batch)

print(profiler.report())
```

---

## AnalyzerCache

`AnalyzerCache` fournit un cache LRU pour les résultats d'analyse, évitant les travaux d'analyse redondants sur des valeurs de champ répétées.

### Utilisation de base

```python
from whoosh_modern.indexing import BatchIndexWriter
from whoosh_modern.profiling import AnalyzerCache

cache = AnalyzerCache(maxsize=50000)
analyzer = StandardAnalyzer()

for doc in docs:
    cache_key = f"title:{doc['title']}"
    tokens = cache.get(cache_key)
    if tokens is None:
        tokens = list(analyzer(doc['title']))
        cache.put(cache_key, tokens)
```

### Avec get_or_compute

```python
from whoosh_modern.profiling import AnalyzerCache

cache = AnalyzerCache(maxsize=50000)
analyzer = StandardAnalyzer()

for doc in docs:
    tokens = cache.get_or_compute(
        f"title:{doc['title']}",
        lambda: list(analyzer(doc['title']))
    )
```

### Statistiques du cache

```python
print(f"Hit rate: {cache.hit_rate:.1%}")
print(f"Size: {cache.size}/{cache.maxsize}")
print(cache.report())
```

### Dimensionnement à partir de données de profiling

```python
from whoosh_modern.profiling import AnalyzerCache, CacheAnalyzer

analyzer = CacheAnalyzer()
analysis = analyzer.analyze(source.iter_documents())

cache = AnalyzerCache.from_profiling(analysis.to_dict())
```

---

## FieldAnalyzerCache

`FieldAnalyzerCache` encapsule un analyseur et met en cache les résultats par champ.

### Utilisation de base

```python
from whoosh_modern.profiling import FieldAnalyzerCache

field_cache = FieldAnalyzerCache(
    analyzer=StandardAnalyzer(),
    fields=["Country", "City"],
    cache_size=50000,
)

for doc in docs:
    for field in ["Country", "City"]:
        tokens = field_cache.analyze(field, doc[field])
```

### Invalidation du cache

```python
# Invalider une entrée spécifique
field_cache.invalidate("Country", "USA")

# Vider le cache entier
field_cache.clear()
```

### Statistiques du cache

```python
print(f"Hit rate: {field_cache.hit_rate:.1%}")
print(field_cache.report())
```

---

## Sources de données disponibles

| Classe | Type | Dépendances |
|-------|------|-------------|
| `SQLSource` | Bases SQL | `sqlite3` (stdlib) |
| `SQLAlchemySource` | SQLAlchemy | `sqlalchemy` |
| `RESTSource` | API REST | aucune (stdlib `urllib`) |
| `GraphQLSource` | API GraphQL | aucune (stdlib `urllib`) |
| `FastCSVSource` | Fichiers CSV | aucune |
| `JSONSource` | JSON/JSONL | aucune |
| `ParquetSource` | Parquet | `pyarrow` ou `pandas` |
| `PandasSource` | DataFrames pandas | `pandas` |
| `PolarsSource` | DataFrames Polars | `polars` |
| `PeeweeSource` | ORM Peewee | `peewee` |
| `TortoiseSource` | ORM Tortoise | `tortoise-orm` |
| `PydanticSource` | Modèles Pydantic | `pydantic` |
