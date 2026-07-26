---
color_scheme: dark
title: "Recherche Vectorielle"
parent: "Exemples"
nav_order: 5
lang: fr
---

# Recherche Vectorielle avec Whoosh‑NG

Cet exemple montre comment activer la **recherche sémantique/vectorielle** avec l’option `vector` supplémentaire. Nous indexons des embeddings et effectuons une recherche de plus proches voisins (k-NN).

## 1. Installer les dépendances optionnelles

```bash
pip install "whoosh-ng[vector]" numpy
```

## 2. Schéma avec champ Vectoriel

```python
from whoosh.fields import Schema, TEXT, ID, VECTOR

schema = Schema(
    doc_id=ID(stored=True, unique=True),
    title=TEXT(stored=True),
    content=TEXT,
    embedding=VECTOR(stored=True, dim=128),
)
```

## 3. Indexer les vecteurs

```python
import numpy as np
from whoosh import index
import shutil

shutil.rmtree("vector_index", ignore_errors=True)
ix = index.create_in("vector_index", schema)

documents = [
    {"doc_id": "doc1", "title": "Python Basics", "content": "Learn Python programming."},
    {"doc_id": "doc2", "title": "Advanced Python", "content": "Deep dive into decorators."},
    {"doc_id": "doc3", "title": "Data Science", "content": "Pandas and NumPy."},
]

np.random.seed(42)
embeddings = {d["doc_id"]: np.random.rand(128).astype(np.float32) for d in documents}

with ix.writer() as w:
    for doc in documents:
        w.add_document(
            doc_id=doc["doc_id"],
            title=doc["title"],
            content=doc["content"],
            embedding=embeddings[doc["doc_id"]].tobytes(),
        )
    w.commit()
```

## 4. Recherche vectorielle avec NumpyProvider

```python
from whoosh_modern.vector.numpy_provider import NumpyProvider
from whoosh_modern.vector.plugin import VectorPlugin
from whoosh.plugins.manager import PluginManager

VectorPlugin().register(PluginManager())

provider = NumpyProvider()
for doc_id, vec in embeddings.items():
    provider.add([(doc_id, vec.tolist())])

query_vec = embeddings["doc1"]
hits = provider.search(query_vec, k=2)

for hit in hits:
    print(f"doc_id={hit.doc_id}, score={hit.score:.3f}")
```

## 5. Utiliser VectorField pour la sérialisation

```python
from whoosh.vector import VectorField

vf = VectorField(dimension=128, name="embedding")

values = [0.1, 0.2, 0.3, 0.4] + [0.0] * 124
raw = vf.vector_to_bytes(values)
restored = vf.bytes_to_vector(raw)
print(restored == tuple(values))  # True
```

## Points clés

- Installez avec `pip install whoosh-ng[vector]`.
- `VECTOR` stocke les octets bruts ; utilisez `VectorField` pour convertir.
- `NumpyProvider` implémente la similarité cosinus.
- Enregistrez le plugin via `VectorPlugin().register(manager)`.
- Utilisez `filter_ids` dans `provider.search()` pour restreindre les documents.
