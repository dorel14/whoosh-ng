---
title: "Did you mean..."
sidebar_position: 12
Module: whoosh.spelling
Version: 2.7.4
---

# "Did you mean... ?" Correcting errors in user queries

## Overview

Whoosh can quickly suggest replacements for mis-typed words by returning a list
of words from the index (or a dictionary) that are close to the mis-typed word:

```python
with ix.searcher() as s:
    corrector = s.corrector("text")
    for mistyped_word in mistyped_words:
        print(corrector.suggest(mistyped_word, limit=3))
```

See the `whoosh.spelling.Corrector.suggest()` method documentation for
information on the arguments.

Currently the suggestion engine is more like a "typo corrector" than a real
"spell checker" since it doesn't do the kind of sophisticated phonetic matching
or semantic/contextual analysis a good spell checker might. However, it is
still very useful.

There are two main strategies for correcting words:

- Use the terms from an index field.
- Use words from a word list.

## Pulling suggestions from an indexed field

In Whoosh 2.7 and later, spelling suggestions are available on all fields.
However, if you have an analyzer that modifies the indexed words (such as
stemming), you can add `spelling=True` to a field to have it store separate
unmodified versions of the terms for spelling suggestions:

```python
ana = analysis.StemmingAnalyzer()
schema = fields.Schema(text=TEXT(analyzer=ana, spelling=True))
```

You can then use the `whoosh.searching.Searcher.corrector()` method to get a
corrector for a field:

```python
corrector = searcher.corrector("content")
```

The advantage of using the contents of an index field is that when you are
spell checking queries on that index, the suggestions are tailored to the
contents of the index. The disadvantage is that if the indexed documents
contain spelling errors, then the spelling suggestions will also be erroneous.

## Pulling suggestions from a word list

There are plenty of word lists available on the internet you can use to populate
the spelling dictionary. `word_list` can be a list of unicode strings, or a
file object with one word on each line.

```python
from whoosh.spelling import ListCorrector

# word_list must be a sorted list of unicode strings
corrector = ListCorrector(word_list)
```

## Merging two or more correctors

You can combine suggestions from two sources (for example, the contents of an
index field and a word list) using a `whoosh.spelling.MultiCorrector`:

```python
c1 = searcher.corrector("content")
c2 = spelling.ListCorrector(word_list)
corrector = MultiCorrector([c1, c2])
```

## Correcting user queries

You can spell-check a user query using the
`whoosh.searching.Searcher.correct_query()` method:

```python
from whoosh import qparser

# Parse the user query string
qp = qparser.QueryParser("content", myindex.schema)
q = qp.parse(qstring)

# Try correcting the query
with myindex.searcher() as s:
    corrected = s.correct_query(q, qstring)
    if corrected.query != q:
        print("Did you mean:", corrected.string)
```

The `correct_query` method returns an object with the following attributes:

- `query` — A corrected `whoosh.query.Query` tree. Compare it (`==`) with the
  original parsed query to check if the corrector changed anything.
- `string` — A corrected version of the user's query string.
- `tokens` — A list of corrected token objects representing the corrected terms.

You can use a `whoosh.highlight.Formatter` object to format the corrected query
string, for example the `HtmlFormatter` to format it as HTML:

```python
from whoosh import highlight

hf = highlight.HtmlFormatter()
corrected = s.correct_query(q, qstring, formatter=hf)
```

## See also

- [Highlighting](/core/highlight) — Format corrected query strings with a formatter
- [Query Language](/core/query) — Parsing user queries
- [API: spelling](../api/spelling) — Full `whoosh.spelling` reference
