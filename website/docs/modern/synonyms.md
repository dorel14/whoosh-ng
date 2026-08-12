---
title: "Synonyms"
sidebar_position: 51
---

# Synonyms

Module: `whoosh_modern.linguistics.synonyms`
Version: 3.0.0

The synonyms engine provides query-time and index-time synonym expansion through a pluggable provider system. It supports static in-memory mappings, YAML/JSON files, SQLite persistence, and large-scale Wiktionary dictionaries.

## Provider Architecture

All synonym providers implement the `SynonymProvider` protocol:

```python
from whoosh_modern.linguistics.synonyms import SynonymProvider

class MyProvider(SynonymProvider):
    def get_synonyms(self, word: str) -> list[str]: ...
    def add_synonym(self, word: str, synonyms: list[str]) -> None: ...
    def remove_synonym(self, word: str, synonym: str) -> None: ...
```

## Built-in Providers

### StaticSynonymProvider

In-memory provider backed by a dictionary:

```python
from whoosh_modern.linguistics.synonyms import StaticSynonymProvider

provider = StaticSynonymProvider({
    "car": ["automobile", "vehicle"],
    "house": ["home", "residence"],
})
print(provider.get_synonyms("car"))  # ['automobile', 'vehicle']
```

### YAMLSynonymProvider

Loads synonyms from a YAML file:

```yaml
# synonyms.yaml
car:
  - automobile
  - vehicle
house:
  - home
  - residence
```

```python
from whoosh_modern.linguistics.synonyms import YAMLSynonymProvider

provider = YAMLSynonymProvider("synonyms.yaml")
print(provider.get_synonyms("car"))  # ['automobile', 'vehicle']
```

### JSONSynonymProvider

Loads synonyms from a JSON file:

```json
{
    "car": ["automobile", "vehicle"],
    "house": ["home", "residence"]
}
```

```python
from whoosh_modern.linguistics.synonyms import JSONSynonymProvider

provider = JSONSynonymProvider("synonyms.json")
print(provider.get_synonyms("car"))
```

### WiktionarySynonymProvider

Loads synonyms from a kaikki.org JSON Lines dictionary file:

```python
from whoosh_modern.linguistics.synonyms import WiktionarySynonymProvider

provider = WiktionarySynonymProvider(
    "src/whoosh_modern/linguistics/dictionaries/wiktionary/fr.json"
)
print(provider.get_synonyms("voiture"))  # ['automobile', 'véhicule']
```

Each line in the dictionary file is a JSON object:

```json
{"word": "voiture", "s": ["automobile", "véhicule"]}
{"word": "ordinateur", "s": ["pc", "machine"]}
```

The provider filters out:
- Words containing spaces (multi-word expressions)
- Entries with non-standard parts of speech
- Empty or missing synonym lists

### SQLiteSynonymStore

Persistent synonym store backed by SQLite:

```python
from whoosh_modern.linguistics.synonyms import SQLiteSynonymStore

store = SQLiteSynonymStore("synonyms.db")
store.add_synonym("car", ["automobile", "vehicle"])
print(store.get_synonyms("car"))  # ['automobile', 'vehicle']
store.close()
```

## SynonymManager

The `SynonymManager` is the high-level interface for managing synonyms:

```python
from whoosh_modern.linguistics.synonyms import SynonymManager

manager = SynonymManager({"car": ["automobile", "vehicle"]})

# CRUD
manager.add_synonyms("house", ["home", "residence"])
print(manager.get_synonyms("house"))  # ['home', 'residence']
manager.remove_synonym("house", "home")

# Import from external sources
manager.import_yaml("synonyms.yaml")       # Requires PyYAML
manager.import_json("synonyms.json")
manager.import_wiktionary("dictionaries/wiktionary/fr.json")

# Export
manager.export_json("output.json")
```

## Updating Wiktionary Dictionaries

Pre-generated dictionaries live in `src/whoosh_modern/linguistics/dictionaries/wiktionary/`:

```
wiktionary/
├── fr.json
├── en.json
├── de.json
├── es.json
├── it.json
├── manifest.json
└── README.md
```

To regenerate them from the latest kaikki.org dump:

```bash
python scripts/update_wiktionary_dictionaries.py --all
```

Or for a single language:

```bash
python scripts/update_wiktionary_dictionaries.py --lang fr
```

The script downloads `kaikki.org-dictionary-all.jsonl`, extracts synonyms by language, filters by allowed POS tags, and writes compact per-language JSON Lines files.

## SynonymExpansionMiddleware

Integrates synonym expansion into the middleware pipeline:

```python
from whoosh_modern.linguistics.synonyms import (
    SynonymManager,
    SynonymExpansionMiddleware,
)

manager = SynonymManager({
    "car": ["automobile", "vehicle"],
    "house": ["home", "residence"],
})
middleware = SynonymExpansionMiddleware(manager)
```

The middleware expands both search queries and indexed documents:

```python
# Query expansion
ctx = MiddlewareContext(operation="search")
ctx.query = "car"
ctx = middleware.before_search(ctx)
# ctx.query == "car automobile vehicle"

# Document expansion
ctx = MiddlewareContext(operation="index")
ctx.document = {"title": "house for sale"}
ctx = middleware.before_index(ctx)
# ctx.document["title"] == "house for sale home residence"
```

## Prebuilt Language Synonyms

`LANG_SYNONYMS` provides starter dictionaries for five languages:

```python
from whoosh_modern.linguistics.synonyms import LANG_SYNONYMS

french_syns = LANG_SYNONYMS["fr"]
print(french_syns["voiture"])  # ['automobile', 'véhicule']

english_syns = LANG_SYNONYMS["en"]
print(english_syns["car"])  # ['automobile', 'vehicle']
```

| Language | Code | Sample Entry                          |
|----------|------|---------------------------------------|
| French   | `fr` | `"voiture": ["automobile", "véhicule"]` |
| English  | `en` | `"car": ["automobile", "vehicle"]`    |
| German   | `de` | `"auto": ["wagen", "fahrzeug"]`       |
| Spanish  | `es` | `"coche": ["automóvil", "vehículo"]`  |
| Italian  | `it` | `"auto": ["automobile", "veicolo"]`   |

## Integration Example

```python
from whoosh_modern.linguistics import (
    LANG_SYNONYMS,
    SynonymExpansionMiddleware,
    SynonymManager,
)
from whoosh.middleware.chain import MiddlewareChain
from whoosh.middleware.wrappers import MiddlewareWriter, MiddlewareSearcher

# 1. Build synonym manager
syn_manager = SynonymManager(LANG_SYNONYMS["en"])
syn_manager.add_synonyms("search", ["query", "find", "lookup"])

# 2. Create middleware
syn_middleware = SynonymExpansionMiddleware(syn_manager)

# 3. Build middleware chain
chain = MiddlewareChain([syn_middleware])

# 4. Use with writer/searcher
with MiddlewareWriter(ix.writer(), chain) as writer:
    writer.add_document(title="How to search in Whoosh")

with MiddlewareSearcher(ix.searcher(), chain) as searcher:
    results = searcher.search("search")
```

## See Also

- [Linguistics Overview](linguistics.md) — Stemmers, language analyzers, and full pipeline integration
- [Middleware Pipeline](middleware-pipeline.md) — How middleware chains work
- [Stemming Providers](stemming-providers.md) — Language-specific stemmer backends
