---
title: "Stemming and Stop Words"
sidebar_position: 7
Module: whoosh.analysis, whoosh.lang
Version: 2.7.4
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
