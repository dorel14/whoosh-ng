---
title: "Spelling API"
nav_order: 130
---

# Spelling API

Functions and classes for correcting typos in user queries using edit-distance
(Damerau-Levenshtein) matching against the terms in the index.

## Corrector Objects

### `Corrector`

```python
class whoosh.spelling.Corrector
```

Base class for spelling correction objects. Concrete subclasses implement the
`_suggestions()` method.

**Methods:**

#### `suggest(text, limit=5, maxdist=2, prefix=0)`

Returns a list of suggested corrections for `text`, ranked by edit distance
then by frequency.

- `text`: The text to check. Will **not** be added to suggestions even if it
  appears in the index.
- `limit`: Maximum number of suggestions to return.
- `maxdist`: Maximum edit distance to look at (values > 2 are inefficient).
- `prefix`: Require suggestions to share this length of prefix with `text`.
  Increasing to even `1` dramatically speeds up suggestions.

#### `_suggestions(text, maxdist, prefix)`

Low-level method yielding `(score, suggestion)` tuples. Subclasses must
implement this.

### `ReaderCorrector`

```python
class whoosh.spelling.ReaderCorrector(reader, fieldname, fieldobj)
```

Suggests corrections based on terms in a specific field of an `IndexReader`.

**Ranks suggestions by edit distance, then by highest to lowest frequency.**

**Constructor:**
- `reader`: An `IndexReader` object.
- `fieldname`: The name of the field to get suggestions from.
- `fieldobj`: The `FieldType` for the field.

### `ListCorrector`

```python
class whoosh.spelling.ListCorrector(wordlist)
```

Suggests corrections based on a sorted list of strings.

**Constructor:**
- `wordlist`: A sorted list of words to match against.

### `MultiCorrector`

```python
class whoosh.spelling.MultiCorrector(correctors, op)
```

Merges suggestions from a list of sub-correctors.

**Constructor:**
- `correctors`: List of `Corrector` objects.
- `op`: A function (e.g., `max` or `operator.add`) to combine scores from
  multiple correctors for the same suggestion.

## Query Correction

### `Correction`

```python
class whoosh.spelling.Correction(q, qstring, corr_q, tokens)
```

Represents the corrected version of a user query string.

**Attributes:**
- `query`: The corrected `Query` object.
- `string`: The corrected user query string.
- `original_query`: The original `Query` object.
- `original_string`: The original user query string.
- `tokens`: List of token objects representing corrected words.

**Methods:**

#### `format_string(formatter)`

Highlights corrected words in the original query string using the given
`Formatter`.

```python
from whoosh import highlight

correction = searcher.correct_query(q, qstring)
hf = highlight.HtmlFormatter(classname="change")
html = correction.format_string(hf)
```

- `formatter`: A `Formatter` instance (or class, which will be instantiated).
- Returns: Formatted string, typically with corrections emphasized.

### `QueryCorrector`

```python
class whoosh.spelling.QueryCorrector(fieldname)
```

Base class for objects that correct words in a user query.

**Constructor:**
- `fieldname`: The default field name for corrections.

**Methods:**

#### `correct_query(q, qstring)`

Returns a `Correction` object representing the corrected form of the given
query.

- `q`: The original `Query` tree to be corrected.
- `qstring`: The original user query string (may be `None`).
- Returns: A `Correction` object.

#### `field()`

Returns the field name this corrector operates on.

### `SimpleQueryCorrector`

```python
class whoosh.spelling.SimpleQueryCorrector(
    correctors: dict,
    terms: list,
    aliases=None,
    prefix: int = 0,
    maxdist: int = 2
)
```

A simple query corrector based on a mapping of field names to `Corrector`
objects, and a list of `(fieldname, text)` tuples to correct.

**Constructor:**
- `correctors`: Dictionary mapping field names to `Corrector` objects.
- `terms`: Sequence of `(fieldname, text)` tuples representing terms to be
  corrected.
- `aliases`: Dictionary mapping field names in the query to field names for
  spelling suggestions.
- `prefix`: Suggested replacement words must share this number of initial
  characters. Default `0`.
- `maxdist`: Maximum edit distance for suggestions. Values > 2 may be slow.
