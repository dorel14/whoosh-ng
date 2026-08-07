---
title: "Autocomplete"
nav_order: 55
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

## Modern Autocomplete Providers (Whoosh-NG 2.0)

Whoosh-NG 2.0 introduces multiple autocomplete provider strategies: `InvertedIndexAutocomplete`, `NGramProvider`, and `FuzzySuggestProvider`. For full details on creating, registering, and switching providers, see the [Autocomplete Providers Guide](autocomplete-sprint-d.md).
