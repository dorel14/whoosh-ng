---
title: "Recherche vectorielle"
nav_order: 29
parent: "Guides"
lang: fr
---

# Recherche vectorielle

Whoosh-NG supporte la recherche sémantique via des embeddings vectoriels. Ce guide couvre la configuration et l'utilisation des champs vectoriels.

## Concept

La recherche vectorielle permet de trouver des documents par similarité sémantique plutôt que par correspondance exacte de mots-clés.

```
Embedding requête  ----\
                       >--- Similarité cosinus ---> Résultats classés
Embedding document ---/
```

## Configuration

```python
from whoosh.fields import Schema, TEXT, VectorField

schema = Schema(
    title=TEXT(stored=True),
    content=TEXT,
    embedding=VectorField(dimensions=384)  # ex: all-MiniLM-L6-v2
)
```

## Providers

| Provider | Description | Cas d'usage |
|----------|-------------|-------------|
| `NumpyProvider` | NumPy pur, similarité cosinus | Petits/moyens indexes |
| `HNSWProvider` | Hierarchical Navigable Small World | Gros indexes, ANN rapide |
| `FaissProvider` | Facebook AI Similarity Search | Très gros indexes |
| `QdrantProvider` | Qdrant vector DB | Distribué |

## Indexation avec vecteurs

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode([
    "Premier document",
    "Deuxième document"
])

with ix.writer() as writer:
    writer.add_document(
        title="Doc 1",
        content="Python est génial",
        embedding=embeddings[0].tolist()
    )
    writer.commit()
```

## Recherche hybride (mots-clés + vecteur)

```python
with ix.searcher() as searcher:
    # Composante sémantique
    query_embedding = model.encode(["Tutoriel Python"])[0]
    vector_results = searcher.vector_search(
        "embedding", query_embedding, limit=20
    )

    # Composante mots-clés
    keyword_query = QueryParser("content", schema).parse("Python")
    keyword_results = searcher.search(keyword_query, limit=20)

    # Combiner (ex: fusion RRF)
    final_results = fuse_results(vector_results, keyword_results)
```

## Bonnes pratiques

1. **Normalisez les embeddings**: Utilisez la similarité cosinus avec des vecteurs normalisés
2. **Choisissez le provider wisely**: Numpy pour <100k vecteurs, HNSW/Faiss pour plus
3. **Recherche hybride**: Combinez vecteur et mots-clés pour de meilleurs résultats
4. **Cachez les embeddings**: Pré-calculez et stockez pour éviter de recalculer
5. **Indexation par lots**: Indexez les vecteurs en lots pour l'efficacité