---
title: "Autocomplete"
sidebar_position: 55
---

# Autocomplete

An optional edge-ngram style autocomplete layer for Whoosh-NG.

## Install

```bash
pip install whoosh-ng[autocomplete]
```

## Minimal index

```python
from whoosh.fields import Schema, TEXT, KEYWORD

schema = Schema(
    title=TEXT(stored=True),
    tags=KEYWORD(stored=True, commas=True),
)

with ix.writer() as writer:
    writer.add_document(title="Python Quickstart", tags="python,quickstart")
    writer.commit()
```

## Query autocomplete

```python
from whoosh_modern.autocomplete import create_autocomplete

# Create provider (inverted = prefix matching by default)
provider = create_autocomplete("inverted")

# Index terms (typically done at index time)
provider.add(["python", "quickstart", "programming", "pyramid"])

# Search for suggestions
hits = provider.search("py", limit=5)
for hit in hits:
    print(hit.text, hit.score)
# Output: python 0.9, pyramid 0.8
```

## Modern Autocomplete Providers (Whoosh-NG 2.0)

Whoosh-NG 2.0 introduces multiple autocomplete provider strategies: `InvertedIndexAutocomplete`, `NGramProvider`, and `FuzzySuggestProvider`. For full details on creating, registering, and switching providers, see the [Autocomplete Providers Guide](autocomplete-providers.md).

## Autocomplete Provider Integration in the Pipeline

Autocomplete providers operate in **two modes**: standalone (in-memory index of phrases) and registry-based (discovered via `AutocompleteRegistry`). The `AutocompletePlugin` registers the default `"inverted"` provider at startup.

### Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│  Registration (startup)                                         │
│                                                                 │
│  AutocompletePlugin.register(PluginManager)                     │
│    └── AutocompleteRegistry.register("inverted", provider)      │
│                                                                 │
│  The "inverted" provider is now available globally              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Mode 1: Standalone (in-memory index)                           │
│                                                                 │
│  provider = create_autocomplete("inverted")                     │
│  provider.add(["python", "java", "javascript"])                 │
│  hits = provider.search("py", limit=5)                          │
│  └── [AutocompleteHit(text="python", score=0.9), ...]           │
│                                                                 │
│  No Whoosh index required. Pure in-memory lookup.               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Mode 2: Registry-based (tied to a Whoosh index)                │
│                                                                 │
│  provider = AutocompleteRegistry.get("inverted")                │
│                                                                 │
│  # Populate from index terms                                    │
│  with ix.searcher() as s:                                       │
│      for term in s.reader().all_terms():                       │
│          provider.add_term(term, s.doc_freq(term))              │
│                                                                 │
│  # Query suggestions                                            │
│  hits = provider.suggest("py", maxdist=1, limit=5)              │
│  └── [AutocompleteHit(text="python", score=...), ...]           │
└─────────────────────────────────────────────────────────────────┘
```

### Full workflow: indexing + autocomplete

```python
from whoosh import index, fields
from whoosh_modern.autocomplete import create_autocomplete
from whoosh_modern.autocomplete.plugin import AutocompletePlugin
from whoosh.plugins.manager import PluginManager

# 1. Register autocomplete plugin at startup
manager = PluginManager()
AutocompletePlugin().register(manager)

# 2. Create index
schema = fields.Schema(
    title=fields.TEXT(stored=True),
    content=fields.TEXT,
)
ix = index.create_in("indexdir", schema)

# 3. Index documents
with ix.writer() as writer:
    writer.add_document(title="Python programming", content="Learn Python")
    writer.add_document(title="Java development", content="Learn Java")
    writer.add_document(title="JavaScript basics", content="Learn JS")
    writer.commit()

# 4. Build autocomplete provider from index terms
provider = create_autocomplete("inverted")

with ix.searcher() as searcher:
    reader = searcher.reader()
    for term in reader.all_terms():
        # Add term with its document frequency as score weight
        provider.add([term.decode("utf-8")])

# 5. Query autocomplete
hits = provider.search("py", limit=5)
for hit in hits:
    print(f"{hit.text} (score: {hit.score:.3f})")
# Output: python (score: 0.429)
```

### Provider strategies

| Provider | Strategy | Best for |
|----------|----------|----------|
| `InvertedIndexAutocomplete` | Prefix matching with scoring | Simple autocomplete, small vocabularies |
| `NGramProvider` | Character n-gram indexing | Substring matching, typo tolerance |
| `FuzzySuggestProvider` | Approximate matching via rapidfuzz | Typo-tolerant suggestions |

```python
# Prefix matching (default)
provider = create_autocomplete("inverted")
provider.add(["python", "pyramid", "pyodbc"])
hits = provider.search("py")
# → python, pyramid, pyodbc

# N-gram matching
provider = create_autocomplete("ngram", n=3)
provider.add(["python", "java", "javascript"])
hits = provider.search("pyt")
# → python (matched by "pyt" n-gram)

# Fuzzy matching
provider = create_autocomplete("fuzzy", max_distance=2, score_cutoff=60.0)
provider.add(["python", "pyramid", "pyodbc"])
hits = provider.search("pythn")  # typo: missing 'o'
# → python (fuzzy match)
```

### Integration with search middleware

Autocomplete providers can be combined with search middleware for real-time suggestions:

```python
from whoosh.middleware.chain import MiddlewareChain
from whoosh.middleware.wrappers import MiddlewareSearcher

provider = create_autocomplete("inverted")
provider.add(["python", "java", "javascript"])

# In a search handler
def suggest(query: str, limit: int = 5):
    hits = provider.search(query, limit=limit)
    return {"suggestions": [hit.text for hit in hits]}
```
