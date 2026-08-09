---
title: "N-grams"
nav_order: 33
permalink: /en/guides/ngrams/
---

# N-grams

This guide covers N-gram tokenization and analysis for substring matching,
prefix queries, and autocomplete functionality.

## What Are N-grams?

An N-gram is a contiguous sequence of N characters (or tokens) from a string.
For example, the 2-grams of "hello" are: "he", "el", "ll", "lo".

N-gram analysis is useful for:
- Substring search (finding "ell" within "hello")
- Autocomplete / typeahead suggestions
- Fuzzy matching without edit distance computation

## NgramTokenizer

The `NgramTokenizer` splits text into character-level N-grams:

```python
from whoosh.analysis import NgramTokenizer
from whoosh import fields

tokenizer = NgramTokenizer(minsize=2, maxsize=4)

schema = fields.Schema(
    content=fields.TEXT(analyzer=tokenizer),
)
```

### NgramTokenizer Parameters

- `minsize`: Minimum N-gram length (default `2`)
- `maxsize`: Maximum N-gram length (default `4`)

With the example above, the text "hello" produces these 2-4-grams:
`he, hel, hell, el, ell, ello, l, ll, llo, l, lo, o`

## NgramFilter

The `NgramFilter` creates word-level N-grams from tokenized text:

```python
from whoosh.analysis import RegexTokenizer, NgramFilter

analyzer = RegexTokenizer() | NgramFilter(maxsize=2)
```

This produces word-level grams: for "hello world", it produces ("hello",)
and ("hello", "world").

## NgramWordAnalyzer

A convenience analyzer that combines `NgramTokenizer` with `LowercaseFilter`:

```python
from whoosh.analysis import NgramWordAnalyzer

analyzer = NgramWordAnalyzer(minsize=2, maxsize=4)

schema = fields.Schema(
    content=fields.TEXT(analyzer=analyzer),
)
```

## Use Cases

### Substring Search

With N-gram analysis, you can match substrings:

```python
from whoosh.qparser import QueryParser

# Index text with N-grams
# Searching for "ell" matches "hello" because "ell" is a substring
qp = QueryParser("content", schema=ix.schema)
q = qp.parse("ell")
results = searcher.search(q)
```

### Prefix Matching

Set `maxsize` equal to a large value to effectively create prefix N-grams:

```python
from whoosh.analysis import NgramWordAnalyzer

# Create N-grams where each word's prefixes become searchable tokens
# e.g., "hello" -> "h", "he", "hel", "hell", "hello"
analyzer = NgramWordAnalyzer(minsize=1, maxsize=10)
```

### Autocomplete

N-gram indexes are commonly used for autocomplete/typeahead. For more
advanced autocomplete with edge n-grams, consider:

```python
from whoosh.analysis import RegexTokenizer, NgramFilter
from whoosh.query import Prefix

# Index with standard tokenization, then use Prefix queries for autocomplete
analyzer = RegexTokenizer()
schema = fields.Schema(
    title=fields.TEXT(stored=True, analyzer=analyzer),
    content=fields.TEXT(analyzer=analyzer),
)

# For autocomplete, query with Prefix
from whoosh.qparser import QueryParser
qp = QueryParser("title", schema=ix.schema)
q = Prefix("title", "hel")  # Find documents where title starts with "hel"
```

## Comparison with Edge N-grams

Some search engines support "edge n-grams" (only generating N-grams from the
beginning of words). This is more space-efficient for autocomplete:

- Full N-grams: "hello" → "he", "el", "ll", "lo", "hel", "ell", ...
- Edge N-grams: "hello" → "h", "he", "hel", "hell", "hello"

Whoosh's `NgramTokenizer` generates full (bidirectional) N-grams. For
edge-ngram-like behavior, use the `minsize` and `maxsize` parameters
strategically, or use `Prefix` queries against a standard tokenized field.

## Performance Considerations

- N-gram indexes are typically much larger than standard indexes
- Each original token produces multiple N-gram tokens, increasing index size
- Choose `minsize` and `maxsize` carefully to balance search quality against
  index size
- For autocomplete, consider using `Prefix` queries with a
  non-N-gram field for better performance
