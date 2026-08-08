---
title: "Stemmer Providers"
nav_order: 53
permalink: /en/guides/stemming-sprint-d/
lang: en
---

# Stemmer Providers

Module: `whoosh_modern.analysis.stemmer_providers`, `whoosh_modern.analysis.stemming_analyzer`, `whoosh_modern.linguistics.stemmers`
Version: 2.0.0

The stemmer provider system gives you flexible control over which stemming backend is used for text analysis. It supports auto-detection, explicit backend selection, and custom stemmer registration—all with a clean plugin-style API.

## Module Overview

```text
whoosh_modern.analysis
    ├── stemmer_providers.py   # StemmerProvider protocol, Internal/PyStemmer backends, register_stemmer, get_stemmer
    └── stemming_analyzer.py   # Enhanced StemmingAnalyzer with plugin support

whoosh_modern.linguistics.stemmers
    └── __init__.py            # Language-specific analyzers (FR/EN/DE/ES/IT)
```

## StemmerProvider Protocol

Located in `whoosh_modern.analysis.stemmer_providers`:

```python
from whoosh_modern.analysis.stemmer_providers import StemmerProvider

class MyStemmer(StemmerProvider):
    def stem(self, word: str) -> str:
        """Stem a single word."""
        ...

    @property
    def name(self) -> str:
        """Return the stemmer name."""
        return "my_stemmer"

    @property
    def language(self) -> str:
        """Return the language code."""
        return "english"
```

## Getting a Stemmer

### Auto-Detection (Recommended)

The `get_stemmer("auto", language)` function automatically selects the best available backend:

```python
from whoosh_modern.analysis.stemmer_providers import get_stemmer

# Auto-detect: prefers PyStemmer if installed, falls back to internal
stemmer = get_stemmer("auto", "english")
print(stemmer.stem("running"))  # "run"
print(stemmer.name)             # "pystemmer" or "internal"
```

**Priority order:**
1. **PyStemmer** (fastest, requires `pip install whoosh-ng[fast-stemming]`)
2. **Internal** stemmer (built-in Porter stemmer, always available)

### Explicit Backend Selection

```python
from whoosh_modern.analysis.stemmer_providers import get_stemmer

# Force internal stemmer
stemmer = get_stemmer("internal", "english")

# Force PyStemmer (requires installation)
stemmer = get_stemmer("pystemmer", "english")
```

### List Available Backends

```python
from whoosh_modern.analysis.stemmer_providers import list_available_backends

backends = list_available_backends()
print(backends)
# {'internal': 'available', 'pystemmer': 'available', 'my_custom': 'registered'}
```

| Backend       | Status String    | Requires                          |
|---------------|------------------|-----------------------------------|
| `internal`    | `"available"`    | None (always bundled)             |
| `pystemmer`   | `"available"` / `"not installed"` | `pip install whoosh-ng[fast-stemming]` |
| Custom        | `"registered"`   | Registered via `@register_stemmer` |

## Built-in Stemmer Providers

### InternalStemmerProvider

Wraps Whoosh's built-in Porter stemmer. Always available (no extra dependencies):

```python
from whoosh_modern.analysis.stemmer_providers import InternalStemmerProvider

stemmer = InternalStemmerProvider("english")
print(stemmer.stem("cats"))    # "cat"
print(stemmer.stem("running")) # "run"
```

### PyStemmerProvider

Wraps the `Stemmer` library for high-performance stemming. Supports all Snowball languages:

```python
from whoosh_modern.analysis.stemmer_providers import PyStemmerProvider

# Requires: pip install whoosh-ng[fast-stemming]
stemmer = PyStemmerProvider("english")
print(stemmer.stem("cats"))    # "cat"
```

**Note**: This provider calls `self._stemmer.stemWord(word)` to stem words. Ensure PyStemmer is installed or auto-detection will fall back to the internal stemmer.

### IdentityStemmerProvider

A no-op stemmer for testing or when stemming is not desired:

```python
from whoosh_modern.analysis.stemmer_providers import IdentityStemmerProvider

stemmer = IdentityStemmerProvider()
print(stemmer.stem("anything"))  # "anything"
```

## Registering a Custom Stemmer

Use the `@register_stemmer` decorator:

```python
from whoosh_modern.analysis.stemmer_providers import register_stemmer

@register_stemmer("simple")
class SimpleStemmer:
    def stem(self, word: str) -> str:
        # Simple suffix stripping
        if word.endswith("s") and len(word) > 3:
            return word[:-1]
        return word

    @property
    def name(self) -> str:
        return "simple"

    @property
    def language(self) -> str:
        return "english"

# Now use it
from whoosh_modern.analysis.stemmer_providers import get_stemmer

stemmer = get_stemmer("simple", "english")
print(stemmer.stem("cats"))  # "cat"
```

## StemmingAnalyzer (Enhanced)

Located in `whoosh_modern.analysis.stemming_analyzer`, this is the main entry point for creating language-aware analyzers:

```python
from whoosh_modern.analysis import StemmingAnalyzer

# Auto-detect best stemmer for English
analyzer = StemmingAnalyzer(stemmer="auto", language="english")

# Explicit internal stemmer
analyzer = StemmingAnalyzer(stemmer="internal", language="english")

# PyStemmer backend (if installed)
analyzer = StemmingAnalyzer(stemmer="pystemmer", language="french")

# Custom stemmer provider
analyzer = StemmingAnalyzer(stemmer=my_stemmer_instance)
```

### StemmingAnalyzer Parameters

| Parameter   | Type                          | Default                  | Description                      |
|-------------|-------------------------------|--------------------------|----------------------------------|
| `expression`| Regex pattern                 | default token pattern    | Tokenization regex              |
| `stoplist`  | Iterable of stop words        | `whoosh.analysis.STOP_WORDS` | Stop words to filter         |
| `minsize`   | `int`                         | `2`                      | Minimum token length            |
| `maxsize`   | `int \| None`                 | `None`                   | Maximum token length            |
| `gaps`      | `bool`                        | `False`                  | Split on expression vs. match  |
| `stemmer`   | `str \| StemmerProvider`      | `"auto"`                 | Stemmer backend                 |
| `language`  | `str`                         | `"english"`              | Language code                   |
| `ignore`    | `set[str] \| None`            | `None`                   | Words to skip                   |
| `cachesize` | `int`                         | `50000`                  | Stem cache size                 |

### Using with Field Types

```python
from whoosh_modern.analysis import StemmingAnalyzer
from whoosh.fields import Schema, TEXT

# English stemmer with stop words
en_analyzer = StemmingAnalyzer("auto", language="english")

# French stemmer
fr_analyzer = StemmingAnalyzer("auto", language="french")

schema = Schema(
    title=TEXT(stored=True),
    content_en=TEXT(analyzer=en_analyzer),
    content_fr=TEXT(analyzer=fr_analyzer),
)
```

## Language-Specific Analyzers

Pre-built analyzers for five languages, available in `whoosh_modern.linguistics.stemmers`:

```python
from whoosh_modern.linguistics.stemmers import (
    EnglishAnalyzer,
    FrenchAnalyzer,
    GermanAnalyzer,
    SpanishAnalyzer,
    ItalianAnalyzer,
)

# Each is callable and returns a list of tokens
en = EnglishAnalyzer()
tokens = en("The quick brown foxes")
# tokens are stemmed: ["quick", "brown", "fox"] (stop words like "the" removed)
```

### Available Language Analyzers

| Class             | Language  | Module                              |
|-------------------|-----------|-------------------------------------|
| `EnglishAnalyzer` | English   | `whoosh_modern.linguistics.stemmers` |
| `FrenchAnalyzer`  | French    | `whoosh_modern.linguistics.stemmers` |
| `GermanAnalyzer`  | German    | `whoosh_modern.linguistics.stemmers` |
| `SpanishAnalyzer` | Spanish   | `whoosh_modern.linguistics.stemmers` |
| `ItalianAnalyzer` | Italian   | `whoosh_modern.linguistics.stemmers` |

Each internally uses `get_stemmer("auto", language)` to select the best available backend and applies language-specific stop words.

## Stemmer Compatibility Validation

Validate that a stemmer provider works correctly with a set of test words:

```python
from whoosh_modern.analysis.stemmer_providers import (
    get_stemmer,
    validate_stemmer_compatibility,
)

stemmer = get_stemmer("auto", "english")
report = validate_stemmer_compatibility(stemmer, ["running", "cats", "jumps", "houses"])

print(report["total_words"])   # 4
print(report["successful"])    # 4 (or fewer if errors)
print(report["failed"])        # 0
print(report["results"])       # [{'word': 'running', 'stemmed': 'run', 'success': True}, ...]
```

### Compatibility Report Structure

| Field          | Type       | Description                          |
|----------------|------------|--------------------------------------|
| `provider`     | `str`      | Stemmer provider name                |
| `language`     | `str`      | Language code                        |
| `total_words`  | `int`      | Total test words                     |
| `successful`   | `int`      | Words stemmed successfully           |
| `failed`       | `int`      | Words that failed                    |
| `results`      | `list[dict]` | Per-word results with `word`, `stemmed`, `success` |

## Integration with StemmingMiddleware

The stemmer providers can be used with the `StemmingMiddleware` from `whoosh_modern.middleware.analyzer`:

```python
from whoosh_modern.analysis.stemmer_providers import get_stemmer
from whoosh_modern.middleware.analyzer import StemmingMiddleware

stemmer = get_stemmer("auto", "english")
middleware = StemmingMiddleware(
    stemmer=stemmer.stem,
    fields=["title", "content"],  # Only stem these fields
    stem_query=True,              # Also stem the search query
)
```

## Migration from Classic Whoosh

### Old API (Whoosh 1.x/2.x)

```python
from whoosh.analysis import StemmingAnalyzer as OldAnalyzer
analyzer = OldAnalyzer("en")  # Hardcoded to "english"
```

### New API (Whoosh-NG 2.0)

```python
from whoosh_modern.analysis import StemmingAnalyzer

# Auto-detect backend (preferred)
analyzer = StemmingAnalyzer("auto", language="en")

# Or use a language-specific analyzer
from whoosh_modern.linguistics.stemmers import EnglishAnalyzer
analyzer = EnglishAnalyzer()
```

> **Note**: The old `StemmingAnalyzer("en")` hardcoded the language to `"english"`. The new `StemmingAnalyzer(stemmer, language)` parameter is explicit and supports all Snowball languages via PyStemmer.

## Installation

```bash
# Without PyStemmer (uses internal stemmer, slower)
pip install whoosh-ng

# With PyStemmer (recommended, faster)
pip install whoosh-ng[fast-stemming]

# Full modern analysis
pip install whoosh-ng[modern]
```

## See Also

- [Stemming and Stop Words Guide](stemming.md) — Classic Whoosh stemming guide
- [Synonyms & Linguistics Guide](linguistics-sprint-d.md) — Synonym expansion engine
- [API: Modern](../api/modern.md) — Full API reference for analysis extensions
