---
title: "API Moderne"
nav_order: 190
lang: fr
---

# API Moderne

Recherche vectorielle, autocomplétion, indexation de modèles et autres fonctionnalités avancées.

## VectorField

```python
from whoosh.fields import VectorField

champ = VectorField(dimensions=384, metric="cosine", stored=False)
```

Champ de vecteur d'embedding.

---

### VectorProvider

```python
class whoosh.vector.base.VectorProvider
```

Classe de base pour les providers de vecteurs.

#### Méthodes

##### `add_vector()`

```python
provider.add_vector(doc_id, embedding: list[float])
```

Indexer un vecteur.

##### `search()`

```python
results = provider.search(query_embedding, limit=10)
```

Rechercher des vecteurs.

### Providers intégrés

#### NumpyProvider

```python
from whoosh.vector.numpy_provider import NumpyProvider

provider = NumpyProvider()
```

Similarité cosinus NumPy pure. Meilleur pour les petits index.

---

#### HNSWProvider

```python
from whoosh.vector.hnsw_provider import HNSWProvider

provider = HNSWProvider(dimensions=384, metric="cosine")
```

Hierarchical Navigable Small World. ANN rapide pour les grands index.

---

#### FaissProvider

```python
from whoosh.vector.faiss_provider import FaissProvider
```

Facebook AI Similarity Search. Très grands index.

---

#### QdrantProvider

```python
from whoosh.vector.qdrant_provider import QdrantProvider
```

Intégration DB vectorielle distribuée.

---

## API d'indexation de modèles

### ModelIndex

```python
from whoosh_modern.models import ModelIndex

idx = ModelIndex(Book)
schema = idx.schema
doc = idx.to_whoosh_document(instance)
```

Mappe automatiquement des modèles Python vers des schémas Whoosh.

#### Types de modèles supportés

- Dataclasses (`dataclasses.is_dataclass`)
- Pydantic v2 (`BaseModel`)
- SQLAlchemy (`__mapper__`)
- SQLModel (sous-classes de `SQLModel`)
- msgspec (`msgspec.Struct`)
- Classes Python avec `__annotations__`

#### Mappings de types

| Type Python | Champ Whoosh |
|-------------|--------------|
| `str` | `TEXT` |
| `int` / `float` | `NUMERIC` |
| `bool` | `BOOLEAN` |
| `datetime` / `date` | `DATETIME` |
| `Decimal` | `NUMERIC(int, decimal_places=2)` |
| `Enum` | `KEYWORD` |
| `bytes` | `KEYWORD` (stockage hexadécimal) |
| `list[str]` | `KEYWORD` |

### SearchField et SearchOptions

```python
from whoosh_modern.models import SearchField, SearchOptions

class Book:
    title: str = SearchField(fulltext=True, stored=True, analyzer="Simple")
    count: int = SearchField(sortable=True)
```

### AutoIndexer

```python
from whoosh_modern.models import AutoIndexer

auto = AutoIndexer(ix, on_error="raise")
auto.register(Book)
auto.index(instance)
auto.remove(instance)
await auto.index_async(instance)
await auto.remove_async(instance)
```

Indexation automatique avec hooks d'événements SQLAlchemy.

---

## API Autocomplétion

### AutocompleteProvider

```python
class whoosh_modern.autocomplete.base.AutocompleteProvider
```

Classe de base pour les providers d'autocomplétion.

#### Méthodes

##### `suggest()`

```python
suggestions = provider.suggest(
    prefix: str,
    limit: int = 5,
    fuzzy: int = 0
) -> list[str]
```

Obtenir des suggestions d'autocomplétion.

---

### Providers intégrés

#### EdgeNgramProvider

```python
from whoosh_modern.autocomplete.edge_ngram import EdgeNgramProvider

provider = EdgeNgramProvider(searcher, fieldname)
```

Complétion de préfixe via edge n-grammes.

---

#### NgramProvider

```python
from whoosh_modern.autocomplete.ngram import NgramProvider

provider = NgramProvider(searcher, fieldname)
```

Complétion infixe via n-grammes.

---

## Plugins

### VectorPlugin

```python
from whoosh_modern.vector.plugin import VectorPlugin
```

Enregistre les providers de vecteurs et ajoute vector_search au searcher.

### AutocompletePlugin

```python
from whoosh_modern.autocomplete.plugin import AutocompletePlugin
```

Enregistre les providers d'autocomplétion.
