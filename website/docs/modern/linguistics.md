---
title: "Synonyms & Linguistics"
sidebar_position: 52
---

# Synonyms & Linguistics

Module: `whoosh_modern.linguistics.synonyms`, `whoosh_modern.linguistics.stemmers`
Version: 2.0.0

The linguistics module provides a comprehensive synonym expansion engine and language-specific text analyzers. It integrates with the middleware pipeline to expand queries and documents with synonyms at both index time and query time.

## Module Overview

```text
whoosh_modern.linguistics
    ├── synonyms/
    │   ├── provider.py       # SynonymProvider protocol + StaticSynonymProvider
    │   ├── yaml_provider.py  # YAMLSynonymProvider
    │   ├── json_provider.py  # JSONSynonymProvider
    │   ├── store.py          # SQLiteSynonymStore
    │   ├── compiler.py       # SynonymCompiler
    │   ├── manager.py        # SynonymManager
    │   ├── middleware.py     # SynonymExpansionMiddleware
    │   └── languages.py      # LANG_SYNONYMS (FR/EN/DE/ES/IT)
    └── stemmers/
        └── __init__.py       # Language-specific analyzers (FR/EN/DE/ES/IT)
```

## Synonym Providers

### SynonymProvider (Protocol)

The base protocol that all synonym providers implement:

```python
from whoosh_modern.linguistics.synonyms import SynonymProvider

class MyProvider(SynonymProvider):
    def get_synonyms(self, word: str) -> list[str]:
        """Return synonyms for the given word."""
        ...

    def add_synonym(self, word: str, synonyms: list[str]) -> None:
        """Add synonyms for the given word."""
        ...

    def remove_synonym(self, word: str, synonym: str) -> None:
        """Remove a synonym for the given word."""
        ...
```

### StaticSynonymProvider

In-memory provider backed by a dictionary:

```python
from whoosh_modern.linguistics.synonyms import StaticSynonymProvider

provider = StaticSynonymProvider({
    "car": ["automobile", "vehicle", "auto"],
    "house": ["home", "residence"],
})

print(provider.get_synonyms("car"))  # ['automobile', 'vehicle', 'auto']
```

### YAMLSynonymProvider

Loads synonyms from a YAML file:

```yaml
# synonyms.yaml
car:
  - automobile
  - vehicle
  - auto
house:
  - home
  - residence
```

```python
from whoosh_modern.linguistics.synonyms import YAMLSynonymProvider

# Requires: pip install pyyaml
provider = YAMLSynonymProvider("synonyms.yaml")
print(provider.get_synonyms("car"))  # ['automobile', 'vehicle', 'auto']
```

### JSONSynonymProvider

Loads synonyms from a JSON file:

```json
{
    "car": ["automobile", "vehicle", "auto"],
    "house": ["home", "residence"]
}
```

```python
from whoosh_modern.linguistics.synonyms import JSONSynonymProvider

provider = JSONSynonymProvider("synonyms.json")
print(provider.get_synonyms("car"))
```

### SQLiteSynonymStore

Persistent synonym store backed by SQLite:

```python
from whoosh_modern.linguistics.synonyms import SQLiteSynonymStore

store = SQLiteSynonymStore("synonyms.db")

# CRUD operations
store.add_synonym("car", ["automobile", "vehicle"])
print(store.get_synonyms("car"))  # ['automobile', 'vehicle']
store.remove_synonym("car", "automobile")
print(store.get_synonyms("car"))  # ['vehicle']
store.close()
```

### SynonymCompiler

Precompiles raw synonym data into a fast lookup format:

```python
from whoosh_modern.linguistics.synonyms import SynonymCompiler

compiler = SynonymCompiler({"car": ["automobile", "vehicle"]})
compiler.add("house", ["home", "residence"])
compiler.merge({"book": ["publication", "work"]})

compiled = compiler.compile()
print(compiled)
# {'car': ['automobile', 'vehicle'], 'house': ['home', 'residence'], 'book': ['publication', 'work']}
```

## SynonymManager

The `SynonymManager` is the high-level interface for managing synonyms. It wraps a `StaticSynonymProvider` internally and supports import/export:

```python
from whoosh_modern.linguistics.synonyms import SynonymManager

manager = SynonymManager({"car": ["automobile", "vehicle"]})

# CRUD
manager.add_synonyms("house", ["home", "residence"])
print(manager.get_synonyms("house"))  # ['home', 'residence']
manager.remove_synonym("house", "home")

# Import from external sources
manager.import_yaml("synonyms.yaml")   # Requires PyYAML
manager.import_json("synonyms.json")

# Export
manager.export_json("output.json")
```

### Import/Export Workflow

```python
# Import from YAML
manager = SynonymManager()
manager.import_yaml("my_synonyms.yaml")

# Export to JSON (e.g., for migration or backup)
manager.export_json("backup.json")
```

## Prebuilt Language Synonyms

The `LANG_SYNONYMS` dictionary contains starter synonym mappings for five languages:

```python
from whoosh_modern.linguistics.synonyms import LANG_SYNONYMS

# Available languages: fr, en, de, es, it
french_syns = LANG_SYNONYMS["fr"]
print(french_syns["voiture"])  # ['automobile', 'véhicule']

english_syns = LANG_SYNONYMS["en"]
print(english_syns["car"])  # ['automobile', 'vehicle']

# Bootstrap a SynonymManager with a language
manager = SynonymManager(LANG_SYNONYMS["fr"])
```

| Language | Code | Sample Entry                          |
|----------|------|---------------------------------------|
| French   | `fr` | `"voiture": ["automobile", "véhicule"]` |
| English  | `en` | `"car": ["automobile", "vehicle"]`    |
| German   | `de` | `"auto": ["wagen", "fahrzeug"]`       |
| Spanish  | `es` | `"coche": ["automóvil", "vehículo"]`  |
| Italian  | `it` | `"auto": ["automobile", "veicolo"]`   |

> **Note**: These are minimal starter dictionaries for demonstration. Production deployments should load from curated or domain-specific sources.

## SynonymExpansionMiddleware

Integrates synonym expansion into the middleware pipeline. It expands both search queries and indexed document fields:

```python
from whoosh_modern.linguistics.synonyms import (
    SynonymManager,
    SynonymExpansionMiddleware,
)

# Create a manager with your synonyms
manager = SynonymManager({
    "car": ["automobile", "vehicle"],
    "house": ["home", "residence"],
})

# Create the middleware
middleware = SynonymExpansionMiddleware(manager)

# Register with the PluginManager or MiddlewareChain
from whoosh.plugins.manager import PluginManager
PluginManager._default.register_middleware("synonym", middleware)
```

### How It Works

- **`before_search`**: Expands `context.query` by appending synonyms for each token
- **`before_index`**: Expands string values in `context.document` by appending synonyms

```python
# Before: query = "car"
# After:  query = "car automobile vehicle"

# Before: document = {"title": "house for sale"}
# After:  document = {"title": "house for sale home residence"}
```

## Language-Specific Stemming Analyzers

Located in `whoosh_modern.linguistics.stemmers`, these analyzers combine tokenization, stemming, and stop-word removal:

```python
from whoosh_modern.linguistics.stemmers import (
    EnglishAnalyzer,
    FrenchAnalyzer,
    GermanAnalyzer,
    SpanishAnalyzer,
    ItalianAnalyzer,
)

# Each analyzer is callable and returns a list of tokens
analyzer = EnglishAnalyzer()
tokens = analyzer("The running cats")
# tokens are stemmed: ["run", "cat"] (stop words removed)
```

### Stemmer Backend Selection

Under the hood, the stemmers use `whoosh_modern.analysis.stemmer_providers`:

```python
from whoosh_modern.analysis.stemmer_providers import (
    get_stemmer,
    register_stemmer,
    list_available_backends,
)

# Auto-detect best available stemmer (PyStemmer preferred)
stemmer = get_stemmer("auto", "english")

# Explicit backend
stemmer = get_stemmer("internal", "english")   # Whoosh's built-in stemmer
stemmer = get_stemmer("pystemmer", "english")   # PyStemmer (faster)

# List available backends
print(list_available_backends())
# {'internal': 'available', 'pystemmer': 'available', ...}

# Register a custom stemmer
@register_stemmer("my_stemmer")
class MyStemmer:
    def stem(self, word: str) -> str:
        return word.lower()
```

| Backend       | Requires                          | Speed   |
|---------------|-----------------------------------|---------|
| `auto`        | None (falls back automatically)  | Fastest available |
| `internal`    | None (built-in Porter stemmer)   | Medium  |
| `pystemmer`   | `pip install whoosh-ng[fast-stemming]` | Fast |

## Integration Example: Full Pipeline

```python
from whoosh_modern.linguistics import (
    EnglishAnalyzer,
    LANG_SYNONYMS,
    SynonymExpansionMiddleware,
    SynonymManager,
)
from whoosh.middleware.chain import MiddlewareChain
from whoosh.middleware.wrappers import MiddlewareWriter, MiddlewareSearcher

# 1. Build synonym manager with English synonyms
syn_manager = SynonymManager(LANG_SYNONYMS["en"])
syn_manager.add_synonyms("search", ["query", "find", "lookup"])

# 2. Create synonym expansion middleware
syn_middleware = SynonymExpansionMiddleware(syn_manager)

# 3. Build middleware chain
chain = MiddlewareChain([syn_middleware])

# 4. Wrap writer and searcher
with MiddlewareWriter(ix.writer(), chain) as writer:
    writer.add_document(title="How to search in Whoosh")

with MiddlewareSearcher(ix.searcher(), chain) as searcher:
    # Query "search" is expanded to "search query find lookup"
    results = searcher.search("search")
```

## See Also

- [Stemming Guide](stemming-providers.md) — Stemmer providers and language analyzers
- [Middleware Guide](middleware-pipeline.md) — Middleware pipeline integration
- [Provider Integration Guide](provider-integration.md) — Complete pipeline guide for all providers
- [API: Linguistics](../api/modern.md) — Full API reference
