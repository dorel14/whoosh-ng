---
title: "Documentation Whoosh-NG"
nav_order: 0
lang: fr
---

# Documentation Whoosh-NG

Bibliothèque d'indexation et de recherche full-text purement Python, modernisée pour 2025+.

## Démarrage rapide

```bash
pip install whoosh-ng
```

```python
import whoosh.index as index
from whoosh.fields import Schema, TEXT, ID

schema = Schema(id=ID(stored=True), content=TEXT())
ix = index.create_in("indexdir", schema)

with ix.writer() as w:
    w.add_document(id="1", content="hello world")

with ix.searcher() as s:
    results = s.search("world")
    print(results[0])
```

## Fonctionnalités

- Pur Python, aucune dépendance native
- Moteur de recherche embarqué
- Architecture de plugins pour l'extensibilité
- Pipeline de middleware pour les préoccupations transversales
- Support de recherche vectorielle (NumPy, HNSW, Faiss)
- Support asynchrone via extra optionnel
