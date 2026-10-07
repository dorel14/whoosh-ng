---
title: "Recherche vectorielle"
sidebar_position: 60
---

# Recherche vectorielle

Module: `whoosh_modern.vector`
Version: 4.0.0

Whoosh-NG supporte la recherche sémantique via des embeddings vectoriels. Ce guide couvre les providers vectoriels et leur utilisation avec l'API actuelle.

## Concept

La recherche vectorielle permet de trouver des documents par similarité sémantique plutôt que par correspondance exacte de mots-clés. Vous embarquez des documents et des requêtes dans un espace à haute dimension, puis trouvez les voisins les plus proches.

```
Embedding requête  ----\
                       >--- Similarité cosinus ---> Résultats classés
Embedding document ---/
```

## Providers

Whoosh-NG inclut deux backends vectoriels :

| Provider | Description | Cas d'usage |
|----------|-------------|-------------|
| `NumpyProvider` | NumPy pur, similarité cosinus vectorisée | Petits/moyens indexes (jusqu'à ~100k docs) |
| `HnswlibProvider` | HNSW approximate nearest neighbor | Gros indexes, recherche ANN rapide |

### NumpyProvider (par défaut)

`NumpyProvider` stocke les vecteurs en mémoire et calcule la similarité cosinus en utilisant des opérations NumPy vectorisées. C'est le choix par défaut pour les indexes jusqu'à ~100k documents.

```python
from whoosh_modern.vector.numpy_provider import NumpyProvider

provider = NumpyProvider()
provider.add([("doc1", [0.1, 0.2, ...]), ("doc2", [0.4, 0.5, ...])])
hits = provider.search(query_embedding, k=10)
for hit in hits:
    print(hit.doc_id, hit.score)
```

**Optimisations v4.0 :**
- Similarité cosinus vectorisée via `matrix @ query`
- Consolidation paresseuse de la matrice (construite seulement au moment de la recherche)
- `np.argpartition` pour la sélection top-k en O(N)
- Stockage float32 pour -50% de mémoire

### HnswlibProvider

`HnswlibProvider` utilise HNSW pour la recherche de voisins approximatifs. Adapté aux gros indexes où la recherche exacte est trop lente.

```python
from whoosh_modern.vector.hnswlib_provider import HnswlibProvider

provider = HnswlibProvider(dimension=384, space="cosine")
provider.add([("doc1", [0.1, 0.2, ...]), ("doc2", [0.4, 0.5, ...])])
hits = provider.search(query_embedding, k=10)
```

## Champ vectoriel

Utilisez `VECTOR` depuis `whoosh_modern.fields` pour déclarer un champ vecteur dense :

```python
from whoosh.fields import Schema, TEXT, ID
from whoosh_modern.fields import VECTOR

schema = Schema(
    id=ID(stored=True, unique=True),
    title=TEXT(stored=True),
    content=TEXT,
    embedding=VECTOR(dimension=384),
)
```

## Indexation avec vecteurs

### Générer des embeddings

```python
from whoosh_modern.embeddings.fastembed_provider import FastEmbedProvider

provider = FastEmbedProvider(model_name="BAAI/bge-small-en-v1.5")
texts = ["Premier document", "Deuxième document"]
embeddings = provider.embed_batch(texts)
```

### Écrire des documents

```python
with ix.writer() as writer:
    for doc_id, text, embedding in zip(doc_ids, texts, embeddings):
        writer.add_document(
            id=doc_id,
            content=text,
            embedding=embedding,
        )
    writer.commit()
```

## Recherche

### Recherche vectorielle pure

```python
from whoosh_modern.vector.numpy_provider import NumpyProvider

provider = NumpyProvider()
# Peupler le provider avec les vecteurs indexés...
query_embedding = provider.embed("requête de recherche")
hits = provider.search(query_embedding, k=10)
```

### Recherche hybride (BM25 + Vector)

```python
from whoosh_modern.searching.hybrid import HybridSearcher

with ix.searcher() as searcher:
    hs = HybridSearcher(searcher, vector_provider, id_field="id")
    results = hs.search(
        "programmation Python",
        query_vector=query_embedding,
        method="weighted",
        alpha=0.5,
    )
    for r in results:
        print(r.doc_id, r.score, r.bm25_score, r.vector_score)
```

## Performance

Pour des performances de recherche vectorielle optimales :

- **NumpyProvider** : utilisez-le pour des indexes jusqu'à ~100k vecteurs. La multiplication matricielle vectorisée garantit un temps de recherche en O(N).
- **HnswlibProvider** : utilisez-le pour les plus gros indexes. HNSW fournit une recherche approximative en O(log N).
- **Embeddings par batch** : utilisez `embed_batch()` au lieu de `embed()` par document pour +33% de throughput.
- **ProviderPool** : utilisez plusieurs instances de provider pour un embedding parallèle sur CPU multi-coeurs.

## Voir aussi

- [Embeddings](/modern/embeddings) — Providers d'embeddings et configuration
- [Recherche hybride](/modern/search-application) — Fusion BM25 + vectorielle
- [Stockage](/modern/storage-providers) — Persistance des indexes vectoriels
- [Moteur de configuration](/modern/configuration-engine) — Interface de configuration typée
