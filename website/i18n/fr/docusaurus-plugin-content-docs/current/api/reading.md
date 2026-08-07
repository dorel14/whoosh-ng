---
title: 'Reading API'
sidebar_position: 0
---

> **Note de traduction** : Cette page n'est pas encore traduite en français.
> Le contenu anglais est affiché ci-dessous en attendant la traduction.

<!-- Creez une version francaise de ce fichier et supprimez ce message. -->


# Reading API

Classes and functions for reading from an index. The reading module is a
refactored package exposing the same public API as the former monolithic
module.

## Overview

The reading module provides classes for accessing documents, terms, and
postings in an index. The main entry points are `IndexReader` objects obtained
from a searcher. These readers allow you to enumerate terms, access stored
fields, iterate postings, and get term frequencies.

## Core Classes

### `IndexReader`

```python
class whoosh.reading.IndexReader
```

Abstract base class for reading index data. Concrete subclasses include
`SegmentReader` and `MultiReader` (which wraps multiple segment readers).

### `MultiReader`

```python
class whoosh.reading.MultiReader(readers, base=None)
```

Combines multiple `IndexReader` instances into one. All docnums are treated
as relative to the combined index.

**Constructor:**
- `readers`: A list of `IndexReader` instances.
- `base`: Optional list of cumulative document count offsets for each reader.

**Methods:**

#### `doc_frequency(fieldname, text)`

Returns the total number of documents that have the given term in the given
field across all sub-readers.

#### `documents()`

Yields dictionaries of stored fields for each document in the index.

#### `stored_fields(docnum)`

Returns a dictionary of stored field values for the given document number
(index-wide docnum).

```python
r = my_index.reader()
print(r.stored_fields(20))
```

#### `all_stored_fields()`

Yields a `(docnum, stored_fields)` tuple for each document in the index.

#### `terms(fieldname)`

Yields `(fieldname, text)` tuples for every term in the given field.

#### `terms_from(segmentreader,fieldnameprefix)`

Low-level method for multi-reader.

#### `has_termvector(docnum, fieldname)`

Returns `True` if the document has a term vector for the given field.

#### `term_vector(docnum, fieldname)`

Returns a `TermVector` for the given document and field.

#### `is_deleted(docnum)`

Returns `True` if the given document (index-wide docnum) is deleted.

#### `all_doc_ids()`

Returns a sorted array of non-deleted document IDs.

#### `min_spam(fieldname)`

Returns the minimum spam value for the given field.

#### `set_spam(fieldname)`

Returns the set spam value for the given field.

#### `has_exact_length(docnum)`

Returns `True` if the exact length is known for `docnum`.

#### `doc_field_length(docnum, fieldname=None, default=1)`

Returns the length of the given field in the given document.

```python
r = my_index.reader()
length = r.doc_field_length(20, "content")
```

#### `max_field_length(fieldname)`

Returns the maximum length of the given field across all documents.

#### `iter_fieldname`

Low-level method for multi-reader.

#### `lexicon(fieldname)`

Returns an array of all unique terms in the given field, sorted.

#### `expanded_lexicon(fieldname)`

Low-level method that yields terms without the overhead of building an array.

#### `term_info(fieldname, text)`

Returns a `TermInfo` object for the given term, or `None` if the term does
not appear in the index.

#### `terminfos(fieldname)`

Yields `(text, TermInfo)` pairs for the given field.

#### `postings(fieldname, text, stype=None)`

Returns a `Matcher` for the postings list of the given term.

```python
r = my_index.reader()
m = r.postings("content", "whoosh")
for docnum, score in m:
    print("doc %d has term" % docnum)
```

#### `_all_postings(fieldname)`

Low-level. Yields `(text, matcher)` pairs for all terms in a field.

#### `_posting_fragments()`

Low-level.

#### `has_vector(docnum, fieldname)`

Returns `True` if the given field has a term vector in the given document.

#### `vectors(docnum)`

Yields `(fieldname, TermVector)` pairs for all term vectors in the document.

#### `all_items(fieldname)`

Yields `(term, weight, docfreq)` tuples for every term in the given field.

#### `frequency(fieldname, text)`

Returns the total frequency of the term across all documents.

#### `idf(term)`

Returns an iterator of `(docnum, idf)` pairs for the given term.

#### `spelling`

Returns a `SpellingAnalyzer` for the given field.

#### `doc_term(slicenum, fieldname, word)`

Returns `(df, weight)` for `word` in `fieldname` in segment `slicenum`.

#### `doc_diff(slicenum, fieldname, text, num)`

Returns `(df, weight)` for `word` in `fieldname` in segment `slicenum`.

### `SegmentReader`

```python
class whoosh.reading.SegmentReader(segment, schema, storage, base=True)
```

Reader for a single segment of the index.

**Constructor:**
- `segment`: The `Segment` object.
- `schema`: The `Schema` object.
- `storage`: The `Storage` instance.
- `base`: Base document number offset (usually `True`, meaning compute it).

### `MultiID3Reader`

```python
class whoosh.reading.MultiID3Reader(readers, base)
```

Combines multiple readers that have ID3 codec.

### `TermInfo`

```python
class whoosh.reading.TermInfo(
    df=0,
    weight=0,
    minlength=0,
    maxlen=0,
    maxnum=0,
    numdocs=0,
    scorable=True
)
```

Information about a term in the index.

**Attributes:**
- `df`: Document frequency (number of documents containing the term).
- `weight`: Total term frequency across all documents.
- `minlength`: Minimum document length where the term appears.
- `maxlength`: Maximum document length where the term appears. This is `0`
  if lengths are not stored.
- `maxnum`: Maximum number of occurrences per document.
- `numdocs`: Number of documents where the term has a non-zero contribution
  to the score.
- `scorable`: Whether this term is scorable.

## Term Vector

### `TermVector`

```python
class whoosh.reading.TermVector(docnum, fieldname, format_, terms, store_term_vector)
```

Represents the term vector for a single document/field pair.

**Methods:**

#### `tokens(text=None)`

Yields `(t, w, v, p)` tuples for terms in this field.

- `t`: The term string.
- `w`: The term weight (frequency in this document).
- `v`: The list of positions where the term occurs. (`None` if positions
  are not stored.)
- `p`: The list of characters where the term occurs. (`None` if character
  vectors are not stored.)

#### `items(text=None)`

Like `tokens()` but includes term strings in the result.

```python
tv = my_index.reader().term_vector(0, "content")
for token, frequency, positions, chars in tv.tokens():
    print(token, frequency, positions)
```

**Parameters:**
- `text`: Optional `Bytes` object. If given, only yield terms starting with
  this text (used for multi-byte tokenization).

## Reader Utilities

### `get_storage`

```python
whoosh.reading.get_storage(searcher) -> Storage
```

Returns the storage object associated with the searcher.

### `get_index_schema`

```python
whoosh.reading.get_index_schema(searcher) -> Schema
```

Returns the schema object associated with the searcher.

### `load_termdocs`

```python
whoosh.reading.load_termdocs(reader, fieldname, text) -> list
```

Returns a list of document numbers that have the given term.

### `read_pattern`

```python
whoosh.reading.read_pattern(reader, fieldname, expression) -> list
```

Returns sorted term list from `reader.lexicon(fieldname)` filtered to those
matching `expression`.

### `read_terminfo`

```python
whoosh.reading.read_terminfo(reader, fieldname, text) -> TermInfo or None
```

Returns a `TermInfo` for the given term, or `None` if not found.

