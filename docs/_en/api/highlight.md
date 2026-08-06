---
title: "Highlight API"
nav_order: 120
---

# Highlight API

Classes and functions for highlighting matches in search result fragments.
The highlight module is a refactored package exposing the same public API as
the former monolithic module.

## Overview

The highlighting system has four components:

- **Fragmenters** split text into fragments.
- **Fragment Scorers** score fragments to determine which to display.
- **Formatters** render fragments as output (HTML, plain text, etc.).
- **Highlighter** ties these together and is used by `Searcher.highlights()`.

## Module-level Functions

### `highlight`

```python
whoosh.highlight.highlight(
    text: str,
    terms: list[str],
    analyzer,
    fragmenter,
    formatter,
    top: int = 3,
    scorer=None,
    minscore: int = 1,
    order=SCORE,
    mode: str = "query"
) -> str
```

Highlights the matched terms in `text` and returns a formatted string.

- `text`: The text to highlight.
- `terms`: A list of matched terms (strings).
- `analyzer`: The analyzer for the field.
- `fragmenter`: A `Fragmenter` instance or class.
- `formatter`: A `Formatter` instance or class.
- `top`: Maximum number of fragments to return.
- `scorer`: Optional fragment scorer (defaults to `BasicFragmentScorer`).
- `minscore`: Minimum score for a fragment to be included.
- `order`: Sort order for fragments (`FIRST`, `SCORE`, `LONGER`, `SHORTER`).
- `mode`: Analysis mode, typically `"query"` or `"index"`.

### `mkfrag`

```python
whoosh.highlight.mkfrag(
    text: str,
    tokens,
    startchar=None,
    endchar=None,
    charsbefore: int = 0,
    charsafter: int = 0
) -> Fragment
```

Returns a `Fragment` object based on `Token` objects in `tokens`.

### `get_text`

```python
whoosh.highlight.get_text(
    original: str,
    token,
    replace: bool
) -> str
```

Returns the text to use for a match when formatting. If `replace` is `False`,
returns the original text between `token.startchar` and `token.endchar`. If
`True`, returns `token.text`.

### `set_matched_filter`

```python
whoosh.highlight.set_matched_filter(
    tokens,
    termset: frozenset
) -> Iterator[Token]
```

Marks tokens as matched if their `text` attribute is in `termset`. Used for
phrase-agnostic highlighting.

### `set_matched_filter_phrases`

```python
whoosh.highlight.set_matched_filter_phrases(
    tokens,
    text: str,
    terms,
    phrases
) -> Iterator[Token]
```

Marks tokens as matched using phrase-aware logic. Highlights only tokens that
are part of matched phrases.

### `top_fragments`

```python
whoosh.highlight.top_fragments(
    fragments,
    count: int,
    scorer,
    order,
    minscore: int = 1
) -> list[Fragment]
```

Returns the best `count` fragments sorted by `order`, filtered by `minscore`.

## Constants

### `DEFAULT_CHARLIMIT`

```python
whoosh.highlight.DEFAULT_CHARLIMIT = 2**15
```

Default character limit for fragments.

### Sort Order Constants

```python
whoosh.highlight.FIRST   # Sort passages from earlier in the document first
whoosh.highlight.SCORE   # Sort higher scored passages first
whoosh.highlight.LONGER  # Sort longer passages first
whoosh.highlight.SHORTER # Sort shorter passages first
```

## Formatters

### `Formatter`

```python
class whoosh.highlight.Formatter
```

Base class for formatters. Subclasses implement `format_token()` to define
how matched tokens are rendered.

**Methods:**

- `format_token(text, token, replace=False)`: Returns formatted text for a
  matched token.
- `format_fragment(fragment, replace=False)`: Returns formatted text for a
  `Fragment`.
- `format(fragments, replace=False)`: Returns formatted text for a list of
  fragments, joined by `between`.

**Attributes:**
- `between`: String inserted between formatted fragments (default `"..."`).

### `NullFormatter`

```python
class whoosh.highlight.NullFormatter(Formatter)
```

A formatter that does not modify the string. Returns fragments unformatted.

### `UppercaseFormatter`

```python
class whoosh.highlight.UppercaseFormatter(between="...")
```

Formats matched terms in uppercase.

### `HtmlFormatter`

```python
class whoosh.highlight.HtmlFormatter(
    tagname="strong",
    between="...",
    classname="match",
    termclass="term",
    maxclasses=5,
    attrquote='"'
)
```

Wraps matched terms in HTML tags with CSS class names. Two classes are
applied to each match: `classname` (same for all matches) and `termclass`
(different for each term, e.g. `term0`, `term1`).

- `tagname`: The HTML tag to wrap matches (default `"strong"`).
- `between`: Text inserted between fragments.
- `classname`: CSS class applied to all matched term tags.
- `termclass`: CSS class prefix for per-term classes.
- `maxclasses`: Maximum number of distinct per-term class numbers.
- `attrquote`: Quote character for attribute values.

**Methods:**
- `clean()`: Clears the internal term-to-classname mapping dictionary.

### `GenshiFormatter`

```python
class whoosh.highlight.GenshiFormatter(qname="strong", between="...")
```

Formats matched terms as Genshi event streams (requires the Genshi library).

## Fragmenters

### `Fragmenter`

```python
class whoosh.highlight.Fragmenter
```

Base class for fragmenters. Subclasses implement `fragment_tokens()` and/or
`fragment_matches()`.

**Methods:**
- `must_retokenize()`: Returns `True` if this fragmenter needs to re-tokenize
  the text (calls `fragment_tokens` with all tokens). Returns `False` if it can
  work from matched token positions alone (calls `fragment_matches`).

### `WholeFragmenter`

```python
class whoosh.highlight.WholeFragmenter(charlimit=DEFAULT_CHARLIMIT)
```

Does not fragment text. Returns the entire text as one fragment. Useful for
highlighting short fields.

```python
results.fragmenter = WholeFragmenter()
```

### `SentenceFragmenter`

```python
class whoosh.highlight.SentenceFragmenter(
    maxchars: int = 200,
    sentencechars=".!?",
    charlimit=DEFAULT_CHARLIMIT
)
```

Breaks text at sentence-ending punctuation (`.`, `!`, `?`).

- `maxchars`: Maximum characters per fragment.
- `sentencechars`: Characters that indicate sentence boundaries.
- `charlimit`: Maximum character position to process.

**Note:** Should be used with an analyzer that does not remove stop words.

### `ContextFragmenter`

```python
class whoosh.highlight.ContextFragmenter(
    maxchars: int = 200,
    surround: int = 20,
    charlimit=DEFAULT_CHARLIMIT
)
```

The default fragmenter. Finds matched terms and includes `surround` characters
of context before and after each match.

- `maxchars`: Maximum characters per fragment.
- `surround`: Number of context characters to include around matches.
- `charlimit`: Maximum character position to process.

### `PinpointFragmenter`

```python
class whoosh.highlight.PinpointFragmenter(
    maxchars: int = 200,
    surround: int = 20,
    autotrim: bool = False,
    charlimit=DEFAULT_CHARLIMIT
)
```

A non-retokenizing fragmenter that builds fragments from character positions of
matched terms. Faster than `ContextFragmenter` because it doesn't need to
re-tokenize text.

- `maxchars`: Maximum characters per fragment.
- `surround`: Number of context characters around matches.
- `autotrim`: If `True`, trims fragments to the nearest spaces.
- `charlimit`: Maximum character position to process.

### `NullFragmeter`

Alias for `WholeFragmenter`.

### `Fragment`

```python
class whoosh.highlight.Fragment(
    text: str,
    matches,
    startchar: int = 0,
    endchar: int = -1
)
```

Represents a fragment (excerpt) from a hit document. Stores the start and end
character offsets and the list of matched term objects.

**Attributes:**
- `text`: The original source text.
- `matches`: List of objects with `startchar` and `endchar` attributes.
- `startchar`: Start index of the fragment.
- `endchar`: End index of the fragment.
- `matched_terms`: Set of text values of matched terms.

**Methods:**
- `overlaps(fragment)`: Returns `True` if this fragment overlaps the given one.
- `overlapped_length(fragment)`: Returns the combined length of overlapping
  fragments.

### `FragmentScorer`

```python
class whoosh.highlight.FragmentScorer
```

Base class for fragment scoring objects. Subclasses implement `__call__()`
to score a `Fragment`.

### `BasicFragmentScorer`

```python
class whoosh.highlight.BasicFragmentScorer
```

Scores fragments by summing the boosts of matched terms, then multiplying by
the number of distinct matched terms (favors diversity).

## Highlighter

### `Highlighter`

```python
class whoosh.highlight.Highlighter(
    fragmenter=None,
    scorer=None,
    formatter=None,
    always_retokenize: bool = False,
    order=SCORE
)
```

Main highlighter object used by `Searcher.highlights()`.

- `fragmenter`: Fragmenter instance (defaults to `ContextFragmenter`).
- `scorer`: Fragment scorer (defaults to `BasicFragmentScorer`).
- `formatter`: Formatter instance (defaults to `HtmlFormatter(tagname="b")`).
- `always_retokenize`: If `True`, always re-tokenize text instead of using
  character offsets from postings.
- `order`: Sort order for fragments.

**Methods:**
- `highlight_hit(hitobj, fieldname, top=3, minscore=1, strict_phrase=False)`:
  Returns the highlighted string for a single hit in a given field.
- `can_load_chars(results, fieldname)`: Returns `True` if the field supports
  "pinpoint" highlighting using stored character offsets.
