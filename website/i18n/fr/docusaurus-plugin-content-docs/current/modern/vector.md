---
title: "Recherche vectorielle"
sidebar_position: 60
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
2. **Choisissez le provider wisely**: Numpy pour &lt;100k vecteurs, HNSW/Faiss pour plus
3. **Recherche hybride**: Combinez vecteur et mots-clés pour de meilleurs résultats
4. **Cachez les embeddings**: Pré-calculez et stockez pour éviter de recalculer
5. **Indexation par lots**: Indexez les vecteurs en lots pour l'efficacité

## Intégration des Fournisseurs de Vecteurs dans le Pipeline

Le système de recherche vectorielle s'intègre via le registre de plugins de Whoosh
et le format de segment. Le provider est stocké dans le segment d'index et résolu
au moment de la recherche.

### Architecture

```text
┌─────────────────────────────────────────────────────────────────────┐
│  Enregistrement (démarrage)                                         │
│                                                                     │
│  VectorPlugin.register(PluginManager)                              │
│    └── VectorRegistry.register("numpy", NumpyProvider(), owner)     │
│                                                                     │
│  Le provider est maintenant disponible pour tout champ VECTOR      │
│  qui spécifie provider="numpy"                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Indexation                                                          │
│                                                                     │
│  VECTOR(dimensions=384, provider="numpy")                          │
│       │                                                             │
│       ▼                                                             │
│  PerDocWriter.add_vector_items(fieldname, field, items)            │
│       │                                                             │
│       ▼                                                             │
│  Le fichier segment contient :                                     │
│    - octets vectoriels (bruts)                                     │
│    - nom du provider ("numpy")                                     │
│    - métrique ("cosine")                                           │
│       │                                                             │
│       ▼                                                             │
│  writer.commit() → segments écrits sur le disque                  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Recherche                                                         │
│                                                                     │
│  searcher.vector_search("embedding", query_vec, k=10)              │
│       │                                                             │
│       ▼                                                             │
│  Whoosh core lit le segment                                        │
│    └── récupère le nom du provider ("numpy")                        │
│       │                                                             │
│       ▼                                                             │
│  VectorRegistry.get("numpy")                                        │
│       │                                                             │
│       ▼                                                             │
│  NumpyProvider.search(query_vec, k, filter_ids)                    │
│       │                                                             │
│       ▼                                                             │
│  VectorHit[] trié par similarité cosinus                           │
└─────────────────────────────────────────────────────────────────────┘
```

### Chaîne de résolution du provider

Quand `searcher.vector_search()` est appelé, Whoosh core :

1. Lit la configuration du champ `VECTOR` depuis le schéma
2. Ouvre le fichier segment contenant les données vectorielles
3. Extrait le nom du provider stocké dans le segment (ex: `"numpy"`)
4. Recherche le provider dans `VectorRegistry`
5. Appelle `provider.search(query_vector, k, filter_ids)`
6. Retourne `list[VectorHit]`

Si le provider n'est pas enregistré, la recherche échoue avec un manquant de registre.
C'est pourquoi `VectorPlugin().register(manager)` (ou l'enregistrement manuel) est
requise au démarrage.

## Voir Aussi

- [Embeddings](/modern/embeddings) — Provider d'embeddings ONNX Runtime compatible CPU
- [Intégration des Providers](provider-integration.md) — Guide complet du pipeline pour tous les providers
- [Guide Middleware](middleware-pipeline.md) — Pipeline hooks et adaptateurs de providers
