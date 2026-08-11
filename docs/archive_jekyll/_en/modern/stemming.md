---
title: "Stemming and Stop Words"
nav_order: 32
permalink: /en/guides/stemming/
---

# Stemming and Stop Words

This guide covers using stemmers, stop-word filters, and language-specific
text analysis with Whoosh.

## Stemmers

A stemmer reduces words to their root form (e.g., "running" → "run",
"cats" → "cat"), so that different forms of the same word match in
searches.

### Using StemmerFilter

```python
from whoosh.analysis import RegexTokenizer, StemmerFilter
from whoosh.lang.porter import stem
from whoosh import fields

# English Porter stemmer
stem_analyzer = RegexTokenizer() | StemmerFilter(stemfn=stem)

schema = fields.Schema(
    title=fields.TEXT(stored=True),
    content=fields.TEXT(analyzer=stem_analyzer),
)
```

### Snowball Stemmers

Whoosh includes Snowball stemmers for multiple languages:

```python
from whoosh.analysis import StemmerFilter
from whoosh.lang.snowball import EnglishStemmer

stem_analyzer = RegexTokenizer() | StemmerFilter(stemfn=EnglishStemmer().stem)
```

### Language-Aware Stemmer Selection

```python
from whoosh.lang import stemmer_for_language, StemmerFilter
from whoosh.analysis import RegexTokenizer

stem = stemmer_for_language("en")
analyzer = RegexTokenizer() | StemmerFilter(stemfn=stem)

# Or use the analysis StemmingAnalyzer:
from whoosh.analysis import StemmingAnalyzer

analyzer = StemmingAnalyzer("en")
```

### Available Languages

```python
from whoosh.lang import languages, has_stemmer, has_stopwords

print(languages)  # ('ar', 'da', 'nl', 'en', 'fi', 'fr', ...)
print(has_stemmer("en"))  # True
print(has_stopwords("en"))  # True
```

## Stop Words

Stop words are common words (like "the", "a", "and") that are typically
filtered out during indexing since they appear in too many documents to be
useful for ranking.

### Using StopFilter

```python
from whoosh.analysis import RegexTokenizer, StopFilter
from whoosh.lang import stopwords_for_language

# English stop words
stop_words = set(stopwords_for_language("en"))
stop_analyzer = RegexTokenizer() | StopFilter(stoplist=stop_words)

schema = fields.Schema(
    content=fields.TEXT(analyzer=stop_analyzer),
)
```

### Combining Stemming and Stop Words

```python
from whoosh.analysis import StemmingAnalyzer

# StemmingAnalyzer automatically loads stemmer and stopwords for the language
analyzer = StemmingAnalyzer("en")

schema = fields.Schema(
    content=fields.TEXT(analyzer=analyzer),
)
```

### Custom Stop Words

```python
from whoosh.analysis import RegexTokenizer, StopFilter

# Custom stop words list
custom_stops = frozenset(["the", "a", "an", "foo", "bar"])
analyzer = RegexTokenizer() | StopFilter(stoplist=custom_stops)
```

## StemmingAnalyzer (Recommended)

The `StemmingAnalyzer` combines tokenizer, stemming, and stop word filtering:

```python
from whoosh.analysis import StemmingAnalyzer

# Automatically uses the correct stemmer and stop words for the language
analyzer = StemmingAnalyzer("en")

# You can override defaults
analyzer = StemmingAnalyzer("en",
                            use_stopwords=True,
                            use_stems=True)
```

### StemmingAnalyzer Options

- `lang`: Language code (e.g., `"en"`, `"fr"`, `"de"`)
- `use_stopwords`: Whether to load and apply stop words (default `True`)
- `use_stems`: Whether to apply stemming (default `True`)
- `args`: Arguments passed to the tokenizer
- `kwargs`: Keyword arguments for the stemmer or stopwords

## Language-Specific Considerations

### Arabic (ISRI Stemmer)

```python
from whoosh.analysis import StemmerFilter
from whoosh.lang.isri import ISRIStemmer

stem_analyzer = RegexTokenizer() | StemmerFilter(stemfn=ISRIStemmer().stem)
```

### Double Metaphone for Phonetic Matching

```python
from whoosh.analysis import RegexTokenizer, DoubleMetaphoneFilter

analyzer = RegexTokenizer() | DoubleMetaphoneFilter()
```

## Query-Side Stemming

The analyzer is applied at both index time and query time (via the query
parser), so stemming is automatically applied to search terms:

```python
from whoosh.qparser import QueryParser

# If the index uses stemming, queries are stemmed too
qp = QueryParser("content", schema=ix.schema)
q = qp.parse("running cats")  # Will match "run", "cat", etc.
```

## N-gram Analysis

For substring and prefix matching, use N-gram analyzers:

```python
from whoosh.analysis import NgramWordAnalyzer

analyzer = NgramWordAnalyzer(minsize=2, maxsize=4)
schema = fields.Schema(content=fields.TEXT(analyzer=analyzer))
```

See the [N-grams Guide](ngrams.md) for more details.

## Modern Stemmer Providers (Whoosh-NG 2.0)

Whoosh-NG 2.0 introduces a plugin-style stemmer provider system with auto-detection, PyStemmer support, and language-specific analyzers. For full details, see the [Stemmer Providers Guide](stemming-providers.md).

## Stemmer Provider Integration in the Pipeline

The `StemmerProvider` system integrates at **two levels**: field-level analyzers and
pipeline middleware. Understanding both is key to avoiding double-stemming.

### Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│  StemmingAnalyzer (field-level, in Schema)                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ RegexTokenizer() │ StopFilter │ StemmingAnalyzer          │  │
│  │                    (stop words)    │                       │  │
│  │                                   ▼                       │  │
│  │                         stemfn = provider.stem            │  │
│  │                                   │                       │  │
│  │                                   ▼                       │  │
│  │                         Token(stemmed=True)                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Applied by Whoosh core at index time AND query time            │
│  (via QueryParser). Automatic, no middleware needed.             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  StemmingMiddleware (pipeline-level)                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ before_index(context)                                     │  │
│  │   └── stem all str values in context.document             │  │
│  │                                                             │  │
│  │ before_search(context)                                     │  │
│  │   └── stem context.query if stem_query=True                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Hooked into MiddlewareChain. Manual opt-in.                    │
└─────────────────────────────────────────────────────────────────┘
```

### Level 1: Field-level (automatic)

The `StemmingAnalyzer` wraps Whoosh's built-in `StemmingAnalyzer` and injects
a `StemmerProvider`'s `.stem` method as the `stemfn`. Whoosh core applies it
automatically to the field at both index time and query time.

```python
from whoosh.fields import Schema, TEXT
from whoosh_modern.analysis import StemmingAnalyzer, get_stemmer

# Auto-detect best stemmer (PyStemmer preferred)
stemmer = get_stemmer("auto", "english")

# Create analyzer with the provider's stem function
analyzer = StemmingAnalyzer(stemmer=stemmer)

schema = Schema(
    title=TEXT(stored=True),
    content=TEXT(analyzer=analyzer),
)

# At index time: "running cats" → ["run", "cat"]
# At query time: QueryParser also uses the same analyzer
# so "running cats" matches documents containing "run cat"
```

**Pros**: Automatic, no middleware configuration needed, consistent index/query behavior.

**Cons**: Requires the analyzer to be set on each `TEXT` field. Harder to change at runtime.

### Level 2: Middleware-level (opt-in)

`StemmingMiddleware` applies stemming at the pipeline level, operating on raw
string values in `context.document` and `context.query` before Whoosh's analyzers
see them.

```python
from whoosh_modern.middleware import StemmingMiddleware
from whoosh_modern.analysis import get_stemmer
from whoosh.middleware.chain import MiddlewareChain
from whoosh.middleware.wrappers import MiddlewareWriter

stemmer = get_stemmer("auto", "english")

chain = MiddlewareChain([
    StemmingMiddleware(
        stemmer=stemmer.stem,
        fields=["title", "content"],  # None = all str fields
        stem_query=True,
    ),
])

with MiddlewareWriter(ix.writer(), chain) as writer:
    writer.add_document(title="Running cats", content="Fast dogs")
    # before_index stems: "Running cats" → "run cat"
    writer.commit()
```

**Pros**: Works on any field without modifying the schema. Can be toggled at runtime.

**Cons**: Must be manually wired into the pipeline. Risk of double-stemming if the field also uses `StemmingAnalyzer`.

### Full pipeline example: index + search

```python
from whoosh import index, fields
from whoosh.qparser import QueryParser
from whoosh_modern.analysis import StemmingAnalyzer, get_stemmer
from whoosh_modern.middleware import StemmingMiddleware
from whoosh.middleware.chain import MiddlewareChain
from whoosh.middleware.wrappers import MiddlewareWriter, MiddlewareSearcher

# 1. Schema with field-level analyzer
stemmer = get_stemmer("auto", "english")
schema = fields.Schema(
    title=fields.TEXT(stored=True, analyzer=StemmingAnalyzer(stemmer=stemmer)),
    content=fields.TEXT(analyzer=StemmingAnalyzer(stemmer=stemmer)),
)

ix = index.create_in("indexdir", schema)

# 2. Index with middleware (no double-stemming because
#    we don't use StemmingMiddleware when fields already have StemmingAnalyzer)
with ix.writer() as writer:
    writer.add_document(title="Running cats", content="Fast dogs")
    writer.commit()

# 3. Search: QueryParser applies the same analyzer to the query
with ix.searcher() as searcher:
    qp = QueryParser("content", schema)
    q = qp.parse("running cats")
    results = searcher.search(q)
    # "running" is stemmed to "run" by the analyzer
    # "cats" is stemmed to "cat" by the analyzer
    # Matches document with "run" and "cat"
```

### Avoiding double-stemming

```python
# WRONG: double stemming
schema = Schema(
    content=TEXT(analyzer=StemmingAnalyzer(stemmer="auto")),
)
chain = MiddlewareChain([
    StemmingMiddleware(stemmer=get_stemmer("auto").stem),  # Don't do this!
])
# Result: "running" → "run" (analyzer) → "run" (middleware) — harmless but wasteful

# CORRECT: choose ONE level
# Option A: field-level only (recommended for static schemas)
schema = Schema(content=TEXT(analyzer=StemmingAnalyzer(stemmer="auto")))
# No StemmingMiddleware needed

# Option B: middleware-only (for dynamic fields)
schema = Schema(content=TEXT)  # No analyzer
chain = MiddlewareChain([StemmingMiddleware(stemmer=get_stemmer("auto").stem)])
```

### Custom stemmer provider

```python
from whoosh_modern.analysis import register_stemmer, get_stemmer

@register_stemmer("my_stemmer")
class MyStemmer:
    def stem(self, word: str) -> str:
        return word.lower().rstrip("s")

# Use it like any built-in backend
stemmer = get_stemmer("my_stemmer", "english")
analyzer = StemmingAnalyzer(stemmer=stemmer)
```
