---
title: "Autocomplete"
nav_order: 260
---

# Autocomplete with Whoosh-NG

Whoosh-NG provides autocomplete functionality through the `whoosh_modern.autocomplete` module.

## Install

```bash
pip install "whoosh-ng[autocomplete]"
```

## Schema with Keyword Field for Terms

```python
from whoosh import index
from whoosh.fields import Schema, TEXT, KEYWORD

schema = Schema(
    title=TEXT(stored=True),
    tags=KEYWORD(stored=True, commas=True),
)

ix = index.create_in("autocomplete_index", schema)
```

## Index Documents

```python
with ix.writer() as w:
    w.add_document(title="Python Programming", tags="python,programming,language")
    w.add_document(title="JavaScript Basics", tags="javascript,programming,web")
    w.add_document(title="Machine Learning", tags="ml,ai,data-science")
    w.add_document(title="Deep Learning", tags="ml,ai,neural-networks")
    w.commit()
```

## Basic Autocomplete

```python
from whoosh_modern.autocomplete import create_autocomplete

# Create an autocomplete provider (supports "inverted" provider type)
provider = create_autocomplete("inverted")

# Add phrases to index
provider.add(["python", "programming", "javascript", "machine learning", "deep learning"])

# Search for suggestions
hits = provider.search("py", limit=5)
for hit in hits:
    print(hit.text, hit.score)
# Output: python 1.5, programming 0.2
```

## Real-time Suggestion Endpoint

```python
from fastapi import FastAPI
from whoosh_modern.autocomplete import create_autocomplete

app = FastAPI()
provider = create_autocomplete("inverted")

# Populate provider with terms from your index
# (typically done during indexing)
provider.add(["python", "programming", "javascript", "machine learning"])

@app.get("/suggest")
async def suggest(q: str, limit: int = 5):
    hits = provider.search(q, limit=limit)
    return {"suggestions": [hit.text for hit in hits]}
```

## Key Points

- Install with `pip install whoosh-ng[autocomplete]`.
- Use `KEYWORD` fields to store multi-value tags/terms.
- Use `create_autocomplete("inverted")` to create a provider.
- The `InvertedIndexAutocomplete` provider supports prefix matching with scoring.
- Each result is an `AutocompleteHit` with `text` and `score` attributes.
