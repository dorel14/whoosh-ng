---
title: "Autocomplétion"
nav_order: 30
parent: "Guides"
lang: fr
---

# Autocomplétion

Couche optionnelle d'autocomplétion par edge-ngram pour Whoosh-NG.

## Installer

```bash
pip install whoosh-ng[autocomplete]
```

## Index minimal

```python
from whoosh.fields import Schema, TEXT, AutocompleteField

schema = Schema(
    titre=TEXT(stored=True),
    query=AutocompleteField()
)

with ix.writer() as writer:
    writer.add_document(titre="Démarrage Python", query="demarrage python")
    writer.commit()
```

## Requête d'autocomplétion

```python
from whoosh_modern.autocomplete import AutocompleteProvider

provider = AutocompleteProvider(ix, "query")
suggestions = provider.suggest("de", limit=5)
print(suggestions)  # ["demarrage python", ...]
```
