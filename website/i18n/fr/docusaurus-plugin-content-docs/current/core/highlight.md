---
title: "Highlighting"
sidebar_position: 11
Module: whoosh.highlight
Version: 2.7.4
---
> **Note de traduction** : Cette page n'est pas encore traduite en francais.
> Le contenu anglais est affiche ci-dessous en attendant la traduction.

<!-- Creez une version francaise de ce fichier et supprimez ce message. -->


# Highlighting search result excerpts

## Overview

The highlighting system works as a pipeline, with four component types.

- **Fragmenters** chop up the original text into *fragments*, based on the
  locations of matched terms in the text.
- **Scorers** assign a score to each fragment, allowing the system to rank the
  best fragments by whatever criterion.
- **Order functions** control in what order the top-scoring fragments are
  presented to the user. For example, you can show the fragments in the order
  they appear in the document (`FIRST`) or show higher-scoring fragments first
  (`SCORE`).
- **Formatters** turn the fragment objects into human-readable output, such as
  an HTML string.

## Requirements

Highlighting requires that you have the text of the indexed document available.
You can keep the text in a stored field, or if the original text is available in
a file, database column, etc, just reload it on the fly. Note that you might
need to process the text to remove e.g. HTML tags, wiki markup, etc.

## How to

Get search results and use the `highlights()` method on the
`whoosh.searching.Hit` object to get highlighted snippets:

```python
results = mysearcher.search(myquery)
for hit in results:
    print(hit["title"])
    # Assume "content" field is stored
    print(hit.highlights("content"))
```

If the field is not stored, you need to retrieve the text of the field some
other way, then supply it with the `text` argument:

```python
results = mysearcher.search(myquery)
for hit in results:
    print(hit["title"])
    # Assume the "path" stored field contains a path to the original file
    with open(hit["path"]) as fileobj:
        filecontents = fileobj.read()
    print(hit.highlights("content", text=filecontents))
```

## The character limit

By default, Whoosh only pulls fragments from the first 32K characters of the
text. This prevents very long texts from bogging down the highlighting process
too much. You can change the character limit on the results object:

```python
results = mysearcher.search(myquery)
results.fragmenter.charlimit = 100000
```

To turn off the character limit:

```python
results.fragmenter.charlimit = None
```

If you instantiate a custom fragmenter, you can set the character limit directly:

```python
sf = highlight.SentenceFragmenter(charlimit=100000)
results.fragmenter = sf
```

## Customizing the highlights

### Number of fragments

Use the `top` keyword argument to control the number of fragments returned:

```python
# Show a maximum of 5 fragments from the document
print(hit.highlights("content", top=5))
```

### Fragment size

The default fragmenter has a `maxchars` attribute (default 200) controlling the
maximum length of a fragment, and a `surround` attribute (default 20)
controlling the maximum number of characters of context to add at the beginning
and end of a fragment:

```python
# Allow larger fragments
results.fragmenter.maxchars = 300
# Show more context before and after
results.fragmenter.surround = 50
```

### Fragmenter

A fragmenter controls how to extract excerpts from the original text. The
`highlight` module has the following pre-made fragmenters:

- `whoosh.highlight.ContextFragmenter` (the default) â€” a "smart" fragmenter
  that finds matched terms and pulls in surround text. Only yields fragments
  that contain matched terms.
- `whoosh.highlight.SentenceFragmenter` â€” tries to break the text into
  fragments based on sentence punctuation.
- `whoosh.highlight.WholeFragmenter` â€” returns the entire text as one
  "fragment". Useful for short bits of text.

```python
my_cf = highlight.ContextFragmenter(maxchars=100, surround=30)
results.fragmenter = my_cf
```

### Scorer

A scorer is a callable that takes a `whoosh.highlight.Fragment` object and
returns a sortable value (where higher values represent better fragments). The
default scorer adds up the number of matched terms in the fragment, and adds a
"bonus" for the number of *different* matched terms.

```python
def StandardDeviationScorer(fragment):
    """Gives higher scores to fragments where the matched terms are close together."""
    return 0 - stddev([t.pos for t in fragment.matched])

results.scorer = StandardDeviationScorer
```

### Order

The order is a function that takes a fragment and returns a sortable value used
to sort the highest-scoring fragments before presenting them to the user.

- `FIRST` (the default) â€” show fragments in document order.
- `SCORE` â€” show highest scoring fragments first.
- `LONGER` / `SHORTER` â€” longer/shorter fragments first (less generally useful).

```python
results.order = highlight.SCORE
```

### Formatter

A formatter controls how the highest scoring fragments are turned into a
formatted bit of text. The `highlight` module contains:

- `whoosh.highlight.HtmlFormatter` â€” outputs HTML with a class attribute around
  matched terms.
- `whoosh.highlight.UppercaseFormatter` â€” converts matched terms to UPPERCASE.

The easiest way to create a custom formatter is to subclass `highlight.Formatter`
and override `format_token`:

```python
class BracketFormatter(highlight.Formatter):
    """Puts square brackets around the matched terms."""

    def format_token(self, text, token, replace=False):
        tokentext = highlight.get_text(text, token, replace)
        return "[%s]" % tokentext

brf = BracketFormatter()
results.formatter = brf
```

## Highlighter object

Rather than setting attributes on the results object, you can create a reusable
`whoosh.highlight.Highlighter` object:

```python
hi = highlight.Highlighter(fragmenter=my_cf, scorer=sds)
for hit in results:
    print(hit["title"])
    print(hi.highlight_hit(hit))
```

## Speeding up highlighting

Recording which terms matched in which documents during the search may make
highlighting faster:

```python
# Record per-document term matches
results = searcher.search(myquery, terms=True)
```

### PinpointFragmenter

Instead of re-tokenizing the document text, Whoosh can look up the character
positions of the matched terms in the index. To use
`whoosh.highlight.PinpointFragmenter` and avoid re-tokenizing:

1. Index the field with character information (requires re-indexing):

   ```python
   schema = fields.Schema(content=fields.TEXT(stored=True, chars=True))
   ```

2. Record per-document term matches:

   ```python
   results = searcher.search(myquery, terms=True)
   ```

3. Set the `PinpointFragmenter` as the fragmenter:

   ```python
   results.fragmenter = highlight.PinpointFragmenter()
   ```

Use the `autotrim` option to strip whitespace before the first space and after
the last space in the fragments:

```python
results.fragmenter = highlight.PinpointFragmenter(autotrim=True)
```

## Using the low-level API

```python
from whoosh.highlight import highlight

excerpts = highlight(
    text, terms, analyzer, fragmenter, formatter, top=3,
    scorer=BasicFragmentScorer, minscore=1, order=FIRST,
)
```

| Argument | Description |
|----------|-------------|
| `text` | The original text of the document. |
| `terms` | A sequence or set containing the query words to match. |
| `analyzer` | The analyzer to use to break the document text into tokens. |
| `fragmenter` | A `Fragmenter` object. |
| `formatter` | A `Formatter` object. |
| `top` | The number of fragments to include in the output. |
| `scorer` | A `FragmentScorer` object. |
| `minscore` | The minimum score a fragment must have to be included. |
| `order` | An ordering function for the "top" fragments. |

## See also

- [Searching](/core/searching) â€” The `search()` method and `Hit` objects
- [API: highlight](../api/highlight) â€” Full `whoosh.highlight` reference

