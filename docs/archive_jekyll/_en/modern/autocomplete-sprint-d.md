---
title: "Autocomplete Providers"
nav_order: 54
permalink: /en/guides/autocomplete-sprint-d/
lang: en
---

# Autocomplete Providers

Module: `whoosh_modern.autocomplete`
Version: 2.0.0

The autocomplete module provides multiple provider strategies for query suggestion and type-ahead search. All providers implement a common interface so you can swap strategies at runtime. Providers are registered via the `AutocompleteRegistry` and loaded through entry points.

## Module Overview

```text
whoosh_modern.autocomplete
    ├── provider.py   # AutocompleteHit, AutocompleteProvider (Protocol)
    ├── ngram.py      # NGramProvider (character n-gram based)
    ├── edge_ngram.py # InvertedIndexAutocomplete (inverted index prefix matching)
    ├── fuzzy.py      # FuzzySuggestProvider (approximate matching via rapidfuzz)
    ├── factory.py    # create_autocomplete() factory
    └── plugin.py     # AutocompletePlugin (entry-point plugin)
```

## AutocompleteProvider (Base Class)

Located in `whoosh_modern.autocomplete.provider`:

```python
from whoosh_modern.autocomplete.provider import AutocompleteProvider, AutocompleteHit

class MyProvider(AutocompleteProvider):
    def add(self, phrases: Iterable[str]) -> None:
        """Add phrases to the provider's index."""
        ...

    def search(self, prefix: str, limit: int = 10) -> list[AutocompleteHit]:
        """Return autocomplete suggestions for the given prefix."""
        ...
```

### AutocompleteHit

A simple result object returned by providers:

```python
class AutocompleteHit:
    def __init__(self, text: str, score: float) -> None:
        self.text = text    # The matched phrase
        self.score = score  # Relevance score (higher = better)
```

## Built-in Providers

### InvertedIndexAutocomplete

Located in `whoosh_modern.autocomplete.edge_ngram`. Uses simple prefix matching against an in-memory list:

```python
from whoosh_modern.autocomplete.edge_ngram import InvertedIndexAutocomplete

provider = InvertedIndexAutocomplete()
provider.add(["python", "pyramid", "pytorch", "java", "javascript"])

hits = provider.search("py", limit=5)
for hit in hits:
    print(f"{hit.text} (score: {hit.score})")
# Output:
# python (score: 0.45)
# pyramid (score: 0.43)
# pytorch (score: 0.43)
```

**Scoring**: Exact prefix matches get a 1.5x bonus; base score is `1.0 / (len(phrase) + 1)`.

### NGramProvider

Located in `whoosh_modern.autocomplete.ngram`. Builds a character n-gram index for fuzzy substring matching:

```python
from whoosh_modern.autocomplete.ngram import NGramProvider

provider = NGramProvider(n=3)
provider.add(["python programming", "java development", "rust language"])

hits = provider.search("pyt", limit=5)
for hit in hits:
    print(f"{hit.text} (score: {hit.score})")
```

**Parameters:**

| Parameter | Type | Default | Description                          |
|-----------|------|---------|--------------------------------------|
| `n`       | `int` | `3`     | Size of character n-grams            |

**How it works**: N-grams are extracted from each phrase (lowercased). During search, n-grams from the prefix are matched against the index. Phrases with more matching n-gram occurrences receive higher scores.

### FuzzySuggestProvider

Located in `whoosh_modern.autocomplete.fuzzy`. Uses `rapidfuzz` for approximate string matching (typos, partial matches):

```python
from whoosh_modern.autocomplete.fuzzy import FuzzySuggestProvider

# Requires: pip install whoosh-ng[fuzzy]
provider = FuzzySuggestProvider(max_distance=2, score_cutoff=50.0)
provider.add(["python", "pyramid", "pytorch", "java", "javascript"])

hits = provider.search("pythn", limit=5)  # Typo in "python"
for hit in hits:
    print(f"{hit.text} (score: {hit.score})")
# Output: python (score: 0.95), ...
```

**Parameters:**

| Parameter       | Type  | Default  | Description                              |
|-----------------|-------|----------|------------------------------------------|
| `max_distance`  | `int` | `2`      | Maximum edit distance (unused by rapidfuzz directly, reserved for future use) |
| `score_cutoff`  | `float` | `50.0` | Minimum similarity score (0-100 scale)   |

**Note**: Requires `rapidfuzz` (`pip install whoosh-ng[fuzzy]`). Falls back to `ImportError` if not installed.

## Factory Function

Located in `whoosh_modern.autocomplete.factory`:

```python
from whoosh_modern.autocomplete import create_autocomplete

# Create any provider by name
provider = create_autocomplete("inverted")   # InvertedIndexAutocomplete
provider = create_autocomplete("ngram", n=3) # NGramProvider with custom n
provider = create_autocomplete("fuzzy", max_distance=2, score_cutoff=60.0)
```

**Available providers:**

| Name        | Class                    | Optional Dependency |
|-------------|--------------------------|---------------------|
| `"inverted"`| `InvertedIndexAutocomplete` | None              |
| `"ngram"`   | `NGramProvider`          | None               |
| `"fuzzy"`   | `FuzzySuggestProvider`   | `rapidfuzz`        |

## Registering with the AutocompleteRegistry

Providers are registered into `whoosh.registry.AutocompleteRegistry` (a `Registry` instance):

```python
from whoosh.registry import AutocompleteRegistry
from whoosh_modern.autocomplete import create_autocomplete

# Register a provider
provider = create_autocomplete("ngram", n=3)
AutocompleteRegistry.register("ngram-suggester", provider, owner="my_app")

# Retrieve it later
suggester = AutocompleteRegistry.get("ngram-suggester")

# List all registered providers
print(AutocompleteRegistry.list_keys())
```

## AutocompletePlugin (Entry Point)

Located in `whoosh_modern.autocomplete.plugin`, this is the built-in plugin registered via the `whoosh_ng.plugins` entry-point group:

```python
from whoosh_modern.autocomplete.plugin import AutocompletePlugin

# Automatically loaded by PluginManager.load_plugins()
# Registers "inverted" provider in AutocompleteRegistry
```

### Entry Point Declaration

In `pyproject.toml`:

```toml
[project.entry-points."whoosh_ng.plugins"]
whoosh_autocomplete = "whoosh_modern.autocomplete.plugin:AutocompletePlugin"
```

### Plugin Details

```python
class AutocompletePlugin(Plugin):
    name = "whoosh_autocomplete"
    version = "3.0.0"

    def register(self, manager):
        # Registers InvertedIndexAutocomplete as "inverted"
        AutocompleteRegistry.register(
            "inverted", create_autocomplete("inverted"), self.name
        )

    def register_hooks(self):
        # Registers an on_search hook (currently a no-op)
        from whoosh.hooks import hookimpl, register_hook
        register_hook("on_search", hookimpl(on_search))
```

## Usage Examples

### Basic Usage

```python
from whoosh_modern.autocomplete import create_autocomplete

# Create and populate a provider
provider = create_autocomplete("inverted")
provider.add([
    "python programming",
    "python tutorial",
    "java tutorial",
    "javascript framework",
])

# Search for suggestions
hits = provider.search("py", limit=3)
for hit in hits:
    print(f"{hit.text}: {hit.score:.3f}")
```

### Using Fuzzy Matching with Typo Tolerance

```python
from whoosh_modern.autocomplete import create_autocomplete

provider = create_autocomplete("fuzzy", score_cutoff=70.0)
provider.add(["python", "pytorch", "tensorflow", "keras"])

# Even with a typo, relevant suggestions are returned
hits = provider.search("pyton", limit=5)
for hit in hits:
    print(hit.text, hit.score)
```

### Using N-Gram Matching for Partial Words

```python
from whoosh_modern.autocomplete import create_autocomplete

# Use 3-grams for better substring matching
provider = create_autocomplete("ngram", n=3)
provider.add(["machine learning", "deep learning", "neural networks"])

# Finds phrases containing the n-grams of "machin"
hits = provider.search("machin", limit=5)
```

### Integration with Search

```python
from whoosh_modern.autocomplete import create_autocomplete

# Build the autocomplete provider
provider = create_autocomplete("inverted")
provider.add(["python", "java", "javascript", "go", "rust"])

# Use in a search endpoint
def suggest(prefix: str, limit: int = 5):
    hits = provider.search(prefix, limit=limit)
    return [{"text": h.text, "score": h.score} for h in hits]

# In your FastAPI/REST endpoint:
# GET /api/suggest?q=py&limit=5
# Response: [{"text": "python", "score": 0.45}, ...]
```

## Comparison of Providers

| Provider              | Matching       | Strengths                    | Weaknesses                | Dependency    |
|-----------------------|----------------|------------------------------|---------------------------|---------------|
| `inverted`            | Prefix         | Simple, fast, no deps        | No typo tolerance         | None          |
| `ngram`               | N-gram overlap | Substring matching, flexible | Slower than prefix        | None          |
| `fuzzy`               | Edit distance  | Typo tolerance, flexible     | Requires rapidfuzz        | `rapidfuzz`   |

## Installation

```bash
# Core autocomplete (inverted + n-gram)
pip install whoosh-ng

# With fuzzy matching
pip install whoosh-ng[fuzzy]

# Full modern analysis
pip install whoosh-ng[modern]
```

## See Also

- [Plugin System Guide](plugins-sprint-c.md) — Plugin registration and discovery
- [Middleware Guide](middleware-sprint-c.md) — Middleware pipeline integration
- [API: Modern](../api/modern.md) — Full API reference for autocomplete extensions
