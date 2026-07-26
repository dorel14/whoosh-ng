---
color_scheme: dark
title: "Autocomplete"
parent: "Examples"
nav_order: 3
---

# Autocomplete with Whoosh‑NG

This example demonstrates **autocomplete/suggestion** functionality using the `whoosh_modern.autocomplete` plugin.

## 1. Install

```bash
pip install "whoosh-ng[autocomplete]"
```

## 2. Schema with Keyword Field for Terms

```python
from whoosh import index
from whoosh.fields import Schema, TEXT, KEYWORD
from whoosh_modern.autocomplete.plugin import AutocompletePlugin
from whoosh.plugins.manager import PluginManager

schema = Schema(
    title=TEXT(stored=True),
    tags=KEYWORD(stored=True, commas=True),
)

ix = index.create_in("autocomplete_index", schema)
```

## 3. Register the Plugin

```python
# Register autocomplete plugin
AutocompletePlugin().register(PluginManager())
```

## 4. Index Documents

```python
with ix.writer() as w:
    w.add_document(title="Python Programming", tags="python,programming,language")
    w.add_document(title="JavaScript Basics", tags="javascript,programming,web")
    w.add_document(title="Machine Learning", tags="ml,ai,data-science")
    w.add_document(title="Deep Learning", tags="ml,ai,neural-networks")
    w.commit()
```

## 5. Use Inverted Index for Suggestions

```python
from whoosh_modern.autocomplete.factory import create_autocomplete
from whoosh.registry import AutocompleteRegistry
from whoosh.search import searcher

# Get the registered autocomplete provider
provider = AutocompleteRegistry.get("inverted")

# Index terms from the 'tags' field
with ix.searcher() as s:
    for term in s.lexicon("tags"):
        provider.add_term(term, s.doc_count_all())

# Get suggestions
suggestions = provider.suggest("py", maxdist=1, limit=5)
print(suggestions)  # ['python', 'programming']
```

## 6. Real-time Suggestion Endpoint

```python
from fastapi import FastAPI
from whoosh_modern.autocomplete.factory import create_autocomplete

app = FastAPI()
provider = create_autocomplete("inverted")

@app.get("/suggest")
async def suggest(q: str, limit: int = 5):
    return {"suggestions": provider.suggest(q, limit=limit)}
```

## Key points

- Install with `pip install whoosh-ng[autocomplete]`.
- Use `KEYWORD` fields to store multi-value tags/terms.
- Register `AutocompletePlugin` to enable suggestions.
- The inverted index provider supports fuzzy matching (`maxdist`).
