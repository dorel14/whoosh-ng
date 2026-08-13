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

# Each analyzer is an instance of LanguageAnalyzer and is callable: it returns a list of tokens
analyzer = EnglishAnalyzer
tokens = analyzer("The running cats")
# tokens are stemmed: ["run", "cat"] (stop words removed)

# Backward-compatible "class-style" usage also works: calling the analyzer
# with no arguments returns a fresh analyzer instance, so historical code
# written as EnglishAnalyzer()(text) keeps working unchanged.
tokens = EnglishAnalyzer()("The running cats")
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

## Language Registry

The `LanguageRegistry` maps language codes to `LanguageProfile` instances, centralizing analyzer, stemmer, synonym provider, and language detector resolution.

```python
from whoosh_modern.linguistics.registry import (
    LanguageRegistry,
    LanguageProfile,
    StemmerRegistry,
    get_default_registry,
)

# Use the pre-populated default registry (FR/EN/DE/ES/IT)
registry = get_default_registry()

# Resolve a language profile
profile = registry.resolve("fr")
print(profile.language)   # "fr"
print(profile.analyzer)   # FrenchAnalyzer instance

# Register a custom language profile
custom = LanguageProfile(
    language="pt",
    analyzer=...,  # your analyzer
    stemmer=...,   # your stemmer
)
registry.register(custom)

# StemmerRegistry adds stemmer-specific helpers
stem_registry = StemmerRegistry(registry._profiles.values())
stemmer = stem_registry.get_stemmer("fr")
```

## Multi-Language Analyzer

`MultiLanguageAnalyzer` applies multiple language analyzers simultaneously for multilingual indexing.

```python
from whoosh_modern.linguistics.analyzers import MultiLanguageAnalyzer

# Default: FR/EN/DE/ES/IT
analyzer = MultiLanguageAnalyzer()

# Custom language set
analyzer = MultiLanguageAnalyzer(languages=["fr", "en"])

tokens = analyzer("hello bonjour")
# Returns combined tokens from all configured analyzers
```

## Language Auto-Detection

`StopwordDetector` and `LangDetectProvider` enable automatic language detection:

```python
from whoosh_modern.linguistics.detection import StopwordDetector

detector = StopwordDetector(supported_languages=["fr", "en", "de"])
lang = detector.detect("Ceci est un texte en français")
print(lang)  # "fr"
```

Use with `SearchApplication` for automatic language resolution:

```python
from whoosh_modern import SearchApplication
from whoosh_modern.linguistics.detection import StopwordDetector

app = SearchApplication(
    source=my_source,
    language_detector=StopwordDetector(),
)

# FieldConfig supports language="auto"
# The detector resolves the language per document
```

## Explain Analyzer

`ExplainAnalyzer` exposes the tokenization/stemming pipeline for Search Studio:

```python
from whoosh_modern.linguistics.explain import ExplainAnalyzer

explainer = ExplainAnalyzer(EnglishAnalyzer)
result = explainer.explain("The running cats")

print(result.text)       # "The running cats"
print(result.tokens)     # ["run", "cat"]
```

## Debugging Analysis with ExplainAnalyzer

`ExplainAnalyzer` wraps any existing analyzer and returns an
`AnalysisExplanation` describing how a text is transformed. It is useful
for debugging complex analyzer chains, especially when mixing multilingual
analyzers, stopword filters, or dictionary stem overrides.

```python
from whoosh_modern.linguistics.explain import ExplainAnalyzer
from whoosh.analysis import StandardAnalyzer

explainer = ExplainAnalyzer(StandardAnalyzer())
explanation = explainer.explain("A quick brown fox jumps over the lazy dog")

print(f"Original text: {explanation.text}")
print(f"Final tokens : {explanation.tokens}")

print("\nStep-by-step explanations:")
for step in explanation.explanations:
    print(
        f"  - {step.step}: '{step.original}' -> '{step.result}'"
    )
```

Example output:

```text
Original text: A quick brown fox jumps over the lazy dog
Final tokens : ['quick', 'brown', 'fox', 'jumps', 'lazy', 'dog']

Step-by-step explanations:
  - tokenize: 'A' -> 'A'
  - lowercase: 'A' -> 'a'
  - stop: 'a' -> ''
  - tokenize: 'quick' -> 'quick'
  - lowercase: 'quick' -> 'quick'
  ...
```

### Interpreting the output

- `explanation.text` — the original input text.
- `explanation.tokens` — the final token list after all analyzer steps.
- `explanation.explanations` — a chronological list of
  `TokenExplanation` objects showing each transformation step.

Use this when:
- an analyzer pipeline behaves differently than expected,
- you need to verify which stopwords or stemming rules are applied,
- you want to compare behavior across languages with `MultiLanguageAnalyzer`.

## Dictionary Stem Override

Override Snowball stemming with business dictionaries:

```python
from whoosh_modern.linguistics.dictionary_stem_override import DictionaryStemOverride

override = DictionaryStemOverride({
    "voiture": "voitur",
    "maison": "maison",
})

print(override.stem("voiture"))  # "voitur"
print(override.stem("maison"))   # "maison"

# Add rules dynamically
override.add_rule("chien", "chien")
```

Use with `SearchApplication`:

```python
from whoosh_modern import SearchApplication

app = SearchApplication(
    source=my_source,
    dictionary_stem_overrides={"voiture": "voitur"},
)
```

## Cached Stemming Analyzer

`CachedStemmingAnalyzer` wraps language analyzers with LRU caching:

```python
from whoosh_modern.analysis.cached_stemming_analyzer import CachedStemmingAnalyzer
from whoosh_modern.linguistics.stemmers import FrenchAnalyzer

cached = CachedStemmingAnalyzer(FrenchAnalyzer, cache_size=50000)
tokens = cached("les maisons")
```

## Stemmer Profiler

Measure stemming impact on vocabulary and performance:

```python
from whoosh_modern.profiling.stemmer_profiler import StemmerProfiler

profiler = StemmerProfiler(stemmer=my_stemmer)
report = profiler.profile(["document 1", "document 2", ...])

print(report.original_tokens)        # Total tokens before stemming
print(report.stemmed_tokens)         # Unique tokens after stemming
print(report.reduction_ratio)        # Vocabulary reduction ratio
print(report.estimated_size_reduction)  # Estimated index size reduction %
print(report.avg_stem_time_ms)       # Average stemming time per token
```

## Analyzer Presets

Preconfigured analyzers for common search scenarios:

```python
from whoosh_modern.analysis.stemmer_presets import AnalyzerPresets

# Autocomplete
autocomplete_analyzer = AnalyzerPresets.autocomplete()

# Partial match
partial_analyzer = AnalyzerPresets.partial_match()

# Ecommerce
ecommerce_analyzer = AnalyzerPresets.ecommerce()

# Blog
blog_analyzer = AnalyzerPresets.blog()

# Multilingual
multilingual_analyzer = AnalyzerPresets.multilingual()

# Get by name
analyzer = AnalyzerPresets.get("autocomplete")
```

## See Also

- [Synonyms](synonyms.md) — Synonym providers, manager, and Wiktionary dictionaries
- [Stemming Guide](stemming-providers.md) — Stemmer providers and language analyzers
- [Middleware Guide](middleware-pipeline.md) — Middleware pipeline integration
- [Provider Integration Guide](provider-integration.md) — Complete pipeline guide for all providers
- [API: Linguistics](../api/modern.md) — Full API reference
