---
title: "Autocomplete"
nav_order: 30
parent: "Guides"
lang: en
---

# Autocomplete

An optional edge-ngram style autocomplete layer for Whoosh-NG.

## Install

```bash
pip install whoosh-ng[autocomplete]
```

## Minimal index

```python
from whoosh.fields import Schema, TEXT, AutocompleteField

schema = Schema(
    title=TEXT(stored=True),
    query=AutocompleteField()
)

with ix.writer() as writer:
    writer.add_document(title="Python Quickstart", query="python quickstart")
    writer.commit()
```

## Query autocomplete

```python
from whoosh_modern.autocomplete import AutocompleteProvider

provider = AutocompleteProvider(ix, "query")
suggestions = provider.suggest("py", limit=5)
print(suggestions)  # ["python", "pyramid", ...]
```
