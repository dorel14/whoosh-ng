---
title: "Analysis API"
nav_order: 100
---

# Analysis API

Classes and functions for turning text into indexable "tokens" (usually words).
Analysis is the first step in the indexing pipeline: an analyzer tokenizes text
and applies zero or more filters to the resulting token stream.

## Overview

Three general categories of objects make up the analysis pipeline:

- **Tokenizers** split text into individual tokens (words, n-grams, identifiers).
  Every tokenizer is callable: `tokenizer(text) -> iterator of Token objects`.
- **Filters** transform one token stream into another. Common operations include
  lowercasing, stop-word removal, stemming, and synonym expansion. Every filter
  is callable: `filter(token_generator) -> token_generator`.
- **Analyzers** compose a tokenizer and zero or more filters into a single unit.
  Every analyzer is callable and can be used directly as a field's `analyzer`
  argument.

Tokenizers and filters are combined using the `|` operator:

```python
my_analyzer = RegexTokenizer() | LowercaseFilter() | StopFilter()
```

The first item must be a tokenizer; subsequent items must be filters.

## Composition

### Composable

```python
class whoosh.analysis.Composable
```

Base class for tokenizers and filters, providing `|` composition.

**Attributes:**
- `is_morph (bool)`: Whether this object performs morphological transformation
  (e.g. stemming). Defaults to `False`.

**Methods:**

#### `__or__(self, other)`

Combines this object with `other` using `CompositeAnalyzer`.

```python
analyzer = RegexTokenizer() | LowercaseFilter() | StopFilter()
```

### CompositeAnalyzer

```python
class whoosh.analysis.CompositeAnalyzer
```

Composed analyzer created by chaining a tokenizer and filters with `|`.

**Example:**
```python
from whoosh.analysis import RegexTokenizer, LowercaseFilter, StopFilter

analyzer = RegexTokenizer() | LowercaseFilter() | StopFilter()
tokens = list(analyzer("Hello world, this is a test"))
```

## Token

```python
class whoosh.analysis.Token
```

Represents a single token (usually a word) extracted from source text.
Tokenizers yield the **same** `Token` object repeatedly (for performance), so
consumers must not hold references between iterations.

**Slots:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `text` | `str` | The text of this token |
| `pos` | `int` | Token position (if `positions=True`) |
| `startchar` | `int` | Start character offset (if `chars=True`) |
| `endchar` | `int` | End character offset (if `chars=True`) |
| `original` | `str` | Original text before filters (if `keeporiginal=True`) |
| `positions` | `bool` | Whether position info was requested |
| `chars` | `bool` | Whether character offsets were requested |
| `stopped` | `bool` | Set by `StopFilter` |
| `boost` | `float` | Token boost factor (default `1.0`) |
| `removestops` | `bool` | Whether stop words should be removed |
| `mode` | `str` | `'index'` or `'query'` |
| `boosts` | `dict` | Per-position boost values (if requested) |
| `tokenize` | `bool` | Whether tokenization should proceed |
| `matched` | `bool` | Used during highlighting |
| `fieldname` | `str` | Field name for this token |

**Methods:**

#### `copy()`

Returns a new `Token` with the same attribute values. Use this if you need to
retain a token between iterations.

```python
def remove_duplicates(stream):
    last = None
    for t in stream:
        if last != t.text:
            yield t
        last = t.text
```

## Utility Functions

### entoken

```python
whoosh.analysis.entoken(
    textstream,
    positions=False,
    chars=False,
    start_pos=0,
    start_char=0,
    **kwargs
) -> Iterator[Token]
```

Converts a sequence of strings into a stream of `Token` objects.

### unstopped

```python
whoosh.analysis.unstopped(tokenstream) -> Iterator[Token]
```

Removes tokens where `token.stopped` is `True`.

## Analyzers

### Analyzer (Base)

```python
class whoosh.analysis.Analyzer
```

Abstract base class for all analyzers. Subclasses implement `__call__`.

### CompositeAnalyzer

Created automatically when you use `|` to compose tokenizers and filters.

### Predefined Analyzers

#### IDAnalyzer

```python
whoosh.analysis.IDAnalyzer(lowercase=False) -> Analyzer
```

Yields the entire input as a single token. Deprecated; use `IDTokenizer` directly.

- `lowercase (bool)`: If True, add a `LowercaseFilter`.

#### KeywordAnalyzer

```python
whoosh.analysis.KeywordAnalyzer(
    lowercase=False,
    commas=False
) -> Analyzer
```

Splits on whitespace or commas. Suitable for field values that are lists of
keywords.

- `lowercase (bool)`: Lowercase each token.
- `commas (bool)`: Split on commas instead of whitespace.

**Example:**
```python
from whoosh.analysis import KeywordAnalyzer

an = KeywordAnalyzer(lowercase=True, commas=True)
list(an("Hello, WORLD, test"))
# => ["hello", "world", "test"]
```

#### RegexAnalyzer

```python
whoosh.analysis.RegexAnalyzer(
    expression=r"\w+(\.?\w+)*",
    gaps=False
) -> Analyzer
```

Deprecated; use `RegexTokenizer` directly.

#### SimpleAnalyzer

```python
whoosh.analysis.SimpleAnalyzer(
    expression=default_pattern,
    gaps=False
) -> Analyzer
```

Composes `RegexTokenizer` with `LowercaseFilter`.

- `expression`: Regex pattern for tokens.
- `gaps`: If True, split on the expression instead of matching it.

**Example:**
```python
an = SimpleAnalyzer()
list(an("Hello there, this is a TEST"))
# => ["hello", "there", "this", "is", "a", "test"]
```

#### StandardAnalyzer

```python
whoosh.analysis.StandardAnalyzer(
    expression=default_pattern,
    stoplist=STOP_WORDS,
    minsize=2,
    maxsize=None,
    gaps=False
) -> Analyzer
```

Composes `RegexTokenizer`, `LowercaseFilter`, and optional `StopFilter`.

- `expression`: Regex pattern for tokens.
- `stoplist`: Words to remove (set to `None` to disable).
- `minsize`: Minimum token length (default `2`).
- `maxsize`: Maximum token length (default `None`, no limit).
- `gaps`: If True, split on the expression instead of matching it.

**Example:**
```python
an = StandardAnalyzer()
list(an("Testing is testing and testing"))
# => ["testing", "testing", "testing"]
```

#### StemmingAnalyzer

```python
whoosh.analysis.StemmingAnalyzer(
    expression=default_pattern,
    stoplist=STOP_WORDS,
    minsize=2,
    maxsize=None,
    gaps=False,
    stemfn=stem,
    ignore=None,
    cachesize=50000
) -> Analyzer
```

Composes `RegexTokenizer`, `LowercaseFilter`, optional `StopFilter`, and
`StemFilter`.

- `expression`: Regex pattern for tokens.
- `stoplist`: Words to remove (set to `None` to disable).
- `minsize`: Minimum token length (default `2`).
- `maxsize`: Maximum token length.
- `gaps`: If True, split on the expression instead of matching it.
- `stemfn`: Stemming function (default: Porter stemmer for English).
- `ignore`: Words to not stem (set).
- `cachesize`: Stem cache size (default `50000`). Use `-1` for unbounded,
  `None` for no cache.

**Example:**
```python
an = StemmingAnalyzer()
list(an("Testing is testing and testing"))
# => ["test", "test", "test"]
```

#### FancyAnalyzer

```python
whoosh.analysis.FancyAnalyzer(
    expression=r"\s+",
    stoplist=STOP_WORDS,
    minsize=2,
    gaps=True,
    splitwords=True,
    splitnums=True,
    mergewords=False,
    mergenums=False
) -> Analyzer
```

Composes `RegexTokenizer`, `IntraWordFilter`, `LowercaseFilter`, and `StopFilter`.
Splits on whitespace and breaks compound words into subwords.

**Example:**
```python
an = FancyAnalyzer()
list(an("Should I call getInt or get_real?"))
# => ["should", "call", "get", "int", "get", "real"]
```

#### LanguageAnalyzer

```python
whoosh.analysis.LanguageAnalyzer(
    lang,
    expression=default_pattern,
    gaps=False,
    cachesize=50000
) -> Analyzer
```

Configures a language-specific analyzer with `LowercaseFilter`, `StopFilter`,
and `StemFilter`.

- `lang`: Language code (e.g., `"en"`, `"es"`, `"fr"`).
- `expression`: Regex pattern for tokens.
- `gaps`: If True, split on the expression instead of matching it.
- `cachesize`: Stem cache size.

Available languages: `ar`, `da`, `nl`, `en`, `fi`, `fr`, `de`, `hu`, `it`,
`no`, `pt`, `ro`, `ru`, `es`, `sv`, `tr`.

See `whoosh.lang` for `has_stemmer()` and `has_stopwords()` helper functions.

## Tokenizers

All tokenizers inherit from `Tokenizer`.

### Tokenizer

```python
class whoosh.analysis.Tokenizer
```

Base class for tokenizers. Each tokenizer is callable and yields `Token`
objects.

### RegexTokenizer

```python
class whoosh.analysis.RegexTokenizer(
    expression=default_pattern,
    gaps=False
)
```

Uses a regular expression to extract tokens from text. Each match of the
expression equals one token; group 0 (the entire match) is used as the text.

- `expression`: Compiled regex or pattern string.
- `gaps`: If True, split on the expression rather than matching it.

**Example:**
```python
from whoosh.analysis import RegexTokenizer

rext = RegexTokenizer()
list(rext("hi there 3.141 big-time under_score"))
# => ["hi", "there", "3.141", "big", "time", "under_score"]
```

### IDTokenizer

```python
class whoosh.analysis.IDTokenizer
```

Yields the entire input string as a single token. Used for indexed but
untokenized fields (e.g., document paths).

### CharsetTokenizer

```python
class whoosh.analysis.CharsetTokenizer(charmap)
```

Tokenizes and translates text according to a character mapping dictionary.
Characters that map to `None` are treated as token break characters.

- `charmap`: Mapping from integer character codes to unicode characters
  (as used by `unicode.translate()`).

### PathTokenizer

```python
class whoosh.analysis.PathTokenizer(expression="[^/]+")
```

Tokenizes path strings into hierarchical prefixes. Given `"/a/b/c"`, yields
`["/a", "/a/b", "/a/b/c"]`.

### NgramTokenizer

```python
class whoosh.analysis.NgramTokenizer(minsize, maxsize=None)
```

Splits input text into N-grams instead of words. Unlike `RegexTokenizer`, this
tokenizer does not use a regex, so grams may include whitespace and punctuation.

- `minsize`: Minimum N-gram size.
- `maxsize`: Maximum N-gram size (defaults to `minsize`).

**Example:**
```python
from whoosh.analysis import NgramTokenizer

ngt = NgramTokenizer(4)
list(ngt("hi there"))
# => ["hi t", "i th", " the", "ther", "here"]
```

### CachedRegexTokenizer

```python
class whoosh.analysis.CachedRegexTokenizer(
    expression=default_pattern,
    gaps=False,
    maxsize=8192
)
```

A `RegexTokenizer` wrapper that caches tokenization results for repeated
strings, trading memory for speed.

- `expression`: Regex pattern.
- `gaps`: If True, split on the expression.
- `maxsize`: Maximum cache size (LRU eviction when exceeded).

### SpaceSeparatedTokenizer

```python
whoosh.analysis.SpaceSeparatedTokenizer() -> RegexTokenizer
```

Returns a `RegexTokenizer` that splits on whitespace.

### CommaSeparatedTokenizer

```python
whoosh.analysis.CommaSeparatedTokenizer() -> CompositeAnalyzer
```

Returns a composed analyzer that splits on commas and strips whitespace.

## Filters

All filters inherit from `Filter`.

### Filter

```python
class whoosh.analysis.Filter
```

Base class for filters. Subclasses implement `__call__(self, tokens)` which
takes a token generator and returns a token generator.

- `is_morph (bool)`: Set to `True` for morphological filters (e.g., stemming).
  This allows the filter to be bypassed during query analysis if desired.

### STOP_WORDS

```python
whoosh.analysis.STOP_WORDS
```

A frozenset of common English stop words: `"a"`, `"an"`, `"and"`, `"the"`, etc.
Used as the default stoplist for `StopFilter` and `StandardAnalyzer`.

### url_pattern

```python
whoosh.analysis.url_pattern
```

A compiled regex useful for URL filtering.

### LowercaseFilter

```python
class whoosh.analysis.LowercaseFilter
```

Lowercases token text using `unicode.lower()`.

**Example:**
```python
rext = RegexTokenizer() | LowercaseFilter()
list(rext("This is a TEST"))
# => ["this", "is", "a", "test"]
```

### StopFilter

```python
class whoosh.analysis.StopFilter(
    stoplist=STOP_WORDS,
    minsize=2,
    maxsize=None,
    renumber=True,
    lang=None
)
```

Marks and optionally removes stop words from the token stream.

- `stoplist`: Set of words to filter out (defaults to `STOP_WORDS`).
- `minsize`: Minimum token length; shorter tokens are removed (default `2`).
- `maxsize`: Maximum token length; longer tokens are removed (default `None`).
- `renumber`: Renumber positions to account for removed tokens (default `True`).
- `lang`: If set, loads stop words for the given language code.

**Example:**
```python
from whoosh.analysis import RegexTokenizer, StopFilter

stopper = RegexTokenizer() | StopFilter()
list(stopper("this is a test"))
# => ["test"]
```

### StripFilter

```python
class whoosh.analysis.StripFilter
```

Calls `unicode.strip()` on each token's text.

### CharsetFilter

```python
class whoosh.analysis.CharsetFilter(charmap)
```

Translates token text using `unicode.translate()` with the given character map.
Useful for case folding and accent folding.

- `charmap`: Dictionary mapping character ordinals to unicode characters.

**Example:**
```python
from whoosh.support.charset import accent_map

rext = RegexTokenizer() | CharsetFilter(accent_map)
list(rext("café"))
# => ["cafe"]
```

### DelimitedAttributeFilter

```python
class whoosh.analysis.DelimitedAttributeFilter(
    delimiter="^",
    attribute="boost",
    default=1.0,
    type=float
)
```

Looks for delimiter characters in token text and extracts data after the
delimiter into a named token attribute.

- `delimiter`: Separator character (default `"^"`).
- `attribute`: Attribute name on the token (default `"boost"`).
- `default`: Default value if no delimiter is found (default `1.0`).
- `type`: Type to cast the extracted value (default `float`).

**Example:**
```python
from whoosh.analysis import RegexTokenizer, DelimitedAttributeFilter

daf = DelimitedAttributeFilter()
an = RegexTokenizer(r"\S+") | daf
for t in an(u"image 3.14^2 render"):
    print(t.text, t.boost)
# image 1.0
# 3.14 2.0
# render 1.0
```

### SubstitutionFilter

```python
class whoosh.analysis.SubstitutionFilter(pattern, replacement)
```

Performs regex substitution on token text using `re.sub()`.

- `pattern`: Pattern string or compiled regex.
- `replacement`: Replacement text.

**Example:**
```python
from whoosh.analysis import RegexTokenizer, SubstitutionFilter

# Remove hyphens
ana = RegexTokenizer(r"\S+") | SubstitutionFilter("-", "")
```

### MultiFilter

```python
class whoosh.analysis.MultiFilter(**kwargs)
```

Selects between two or more sub-filters based on the `mode` attribute of the
token stream. Useful for using different filters during indexing vs. querying.

- Keyword arguments map mode names to filter instances.

**Example:**
```python
from whoosh.analysis import MultiFilter, IntraWordFilter

iwf_index = IntraWordFilter(mergewords=True, mergenums=True)
iwf_query = IntraWordFilter(mergewords=False, mergenums=False)
mf = MultiFilter(index=iwf_index, query=iwf_query)
```

### TeeFilter

```python
class whoosh.analysis.TeeFilter(*filters)
```

Interleaves the results of two or more filter chains. Requires at least two
filters. Note: this filter is slow because it creates token copies.

**Example:**
```python
# Lowercase in one branch, reverse in another
f1 = LowercaseFilter()
f2 = ReverseTextFilter()
ana = RegexTokenizer(r"\S+") | TeeFilter(f1, f2)
```

### ReverseTextFilter

```python
class whoosh.analysis.ReverseTextFilter
```

Reverses the text of each token.

**Example:**
```python
an = RegexTokenizer() | ReverseTextFilter()
list(an("hello there"))
# => ["olleh", "ereht"]
```

### PassFilter

```python
class whoosh.analysis.PassFilter
```

Identity filter; passes tokens through unchanged.

### LoggingFilter

```python
class whoosh.analysis.LoggingFilter(logger=None)
```

Prints debug log entries for every token that passes through.

- `logger`: Logger instance (defaults to `whoosh.analysis` logger).

## Intraword Filters

### IntraWordFilter

```python
class whoosh.analysis.IntraWordFilter(
    delims="-_'\"()!@#$%^&*[]{}<>\\|;:,./?`~+=",
    splitwords=True,
    splitnums=True,
    mergewords=False,
    mergenums=False
)
```

Splits words into subwords and performs optional merging. Based on
WordDelimiterFilter in Solr.

- `delims`: String of delimiter characters.
- `splitwords`: Split at case transitions (e.g., `PowerShot` → `Power`, `Shot`).
- `splitnums`: Split at letter-number transitions (e.g., `SD500` → `SD`, `500`).
- `mergewords`: Merge consecutive alphabetic subwords.
- `mergenums`: Merge consecutive numeric subwords.

### CompoundWordFilter

```python
class whoosh.analysis.CompoundWordFilter(wordset, keep_compound=True)
```

Breaks compound tokens into their constituent parts if they match words in the
given wordset. Useful for agglutinative languages and trademarks.

- `wordset`: A set (or any `__contains__` object) of known words.
- `keep_compound`: If True, keep the original compound token in the stream.

### BiWordFilter

```python
class whoosh.analysis.BiWordFilter(sep="-")
```

Merges adjacent tokens into bigram tokens. Useful for pseudo-phrase searching.

- `sep`: Separator string for bigrams.

### ShingleFilter

```python
class whoosh.analysis.ShingleFilter(size=2, sep="-")
```

Merges N adjacent tokens into multi-word tokens (shingles).

- `size`: Number of tokens to combine.
- `sep`: Separator string.

**Note:** For `size=2`, `BiWordFilter` is faster.

## Morphological Filters

### StemFilter

```python
class whoosh.analysis.StemFilter(
    stemfn=stem,
    lang=None,
    ignore=None,
    cachesize=50000
)
```

Stems tokens using the Porter stemming algorithm (or a language-specific
stemmer if `lang` is specified).

- `stemfn`: Stemming function (default: Porter stemmer).
- `lang`: Language code to override `stemfn` with a Snowball stemmer.
- `ignore`: Set of words to not stem (defaults to stemming all words).
- `cachesize`: Cache size for stemmed words. Use `-1` for unbounded,
  `None` for no cache.

**Example:**
```python
from whoosh.analysis import RegexTokenizer, StemFilter

stemmer = RegexTokenizer() | StemFilter()
list(stemmer("fundamentally willows"))
# => ["fundament", "willow"]
```

### PyStemmerFilter

```python
class whoosh.analysis.PyStemmerFilter(
    lang="english",
    ignore=None,
    cachesize=10000
)
```

Subclass of `StemFilter` that uses the third-party `py-stemmer` library.
Requires the py-stemmer package to be installed.

**Methods:**
- `algorithms()`: Returns available stemming algorithms from py-stemmer.

### DoubleMetaphoneFilter

```python
class whoosh.analysis.DoubleMetaphoneFilter(
    primary_boost=1.0,
    secondary_boost=0.5,
    combine=False
)
```

Encodes tokens using Lawrence Philips's Double Metaphone algorithm. Useful
for phonetic matching of names and places.

- `primary_boost`: Boost factor for the primary code token.
- `secondary_boost`: Boost factor for the secondary code token.
- `combine`: If True, keep the original token alongside the encoded tokens.

## N-gram Filters and Analyzers

### NgramFilter

```python
class whoosh.analysis.NgramFilter(minsize, maxsize=None, at=None)
```

Splits token text into N-grams of varying sizes.

- `minsize`: Minimum N-gram size.
- `maxsize`: Maximum N-gram size (defaults to `minsize`).
- `at`: `'start'` for prefix grams, `'end'` for suffix grams, or `None`
  for all position grams.

### NgramAnalyzer

```python
whoosh.analysis.NgramAnalyzer(minsize, maxsize=None) -> Analyzer
```

Composes `NgramTokenizer` with `LowercaseFilter`.

### NgramWordAnalyzer

```python
whoosh.analysis.NgramWordAnalyzer(
    minsize,
    maxsize=None,
    tokenizer=None,
    at=None
) -> Analyzer
```

Composes `RegexTokenizer`, `LowercaseFilter`, and `NgramFilter`. Use this
when you want sub-word n-grams (without whitespace) rather than raw
character n-grams.
