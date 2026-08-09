---
title: "Codecs API"
sidebar_position: 180
---

# Codecs API

Classes and interfaces for how Whoosh writes and reads the inverted index,
postings, and per-document values. The codecs module is a refactored package
exposing the same public API as the former monolithic module.

## Module Functions

### `default_codec`

```python
whoosh.codec.default_codec(*args, **kwargs) -> Codec
```

Returns the default codec used by the index. Currently returns a
`W3Codec` instance.

```python
from whoosh.codec import default_codec
codec = default_codec()
```

## Exceptions

### `OutOfOrderError`

```python
whoosh.codec.OutOfOrderError
```

Raised when documents are added to a field out of order. Fields must
receive documents in ascending docnum order.

## Base Classes

### `Codec`

```python
class whoosh.codec.Codec
```

Abstract base class for index codecs. Subclasses implement methods for
writing and reading the index format.

**Class Attributes:**
- `length_stats (bool)`: If `True`, the codec stores per-document field
  length statistics. Default `True`.

**Methods:**

#### `per_document_writer(storage, segment)`

Abstract. Returns a `PerDocumentWriter` for writing per-document values
(columns, term vectors) to the given segment.

#### `field_writer(storage, segment)`

Abstract. Returns a `FieldWriter` for writing postings to the given segment.

#### `postings_writer(dbfile, byteids=False)`

Abstract. Returns a `PostingsWriter` for writing posting lists to `dbfile`.

#### `postings_reader(dbfile, terminfo, format_, term=None, scorer=None)`

Abstract. Returns a `Matcher` for reading postings from `dbfile`.

#### `automata(storage, segment)`

Returns an `Automata` instance for spelling correction using automata-based
edit distance. Default returns a base `Automata()` object.

#### `terms_reader(storage, segment)`

Abstract. Returns a `TermsReader` for reading the term dictionary and
postings of the given segment.

#### `per_document_reader(storage, segment)`

Abstract. Returns a `PerDocumentReader` for reading per-document values
from the given segment.

#### `new_segment(storage, indexname)`

Abstract. Creates and returns a new `Segment` object for the given storage
and index name.

### `WrappingCodec`

```python
class whoosh.codec.WrappingCodec(child)
```

A `Codec` that delegates all operations to a child codec. Useful for
creating codec wrappers that modify or intercept specific operations.

**Constructor:**
- `child`: The underlying `Codec` instance to wrap.

All methods delegate to the child codec:
`per_document_writer()`, `field_writer()`, `postings_writer()`,
`postings_reader()`, `automata()`, `terms_reader()`, `per_document_reader()`,
`new_segment()`.

## Writer Classes

### `PerDocumentWriter`

```python
class whoosh.codec.PerDocumentWriter
```

Abstract base class for writing per-document values (columns, term vectors).

**Methods:**

#### `start_doc(docnum)`

Abstract. Called when starting to write a new document.

#### `add_field(fieldname, fieldobj, value, length)`

Abstract. Adds a field value to the current document.

#### `add_column_value(fieldname, columnobj, value)`

Abstract. Adds a column value. Raises `NotImplementedError` if the codec
doesn't support columns.

#### `add_vector_items(fieldname, fieldobj, items)`

Abstract. Adds term vector items.

#### `add_vector_matcher(fieldname, fieldobj, vmatcher)`

Convenience method that reads items from a `Matcher` and calls
`add_vector_items()`.

#### `finish_doc()`

Called when finishing a document. Default does nothing.

#### `close()`

Called when done writing. Default does nothing.

### `FieldWriter`

```python
class whoosh.codec.FieldWriter
```

Abstract base class for writing postings (inverted index) data.

**Methods:**

#### `add_postings(schema, lengths, items)`

Translates a generator of `(fieldname, btext, docnum, weight, vbytes)`
tuples into calls to `start_field()`, `start_term()`, `add()`,
`finish_term()`, and `finish_field()`.

**Parameters:**
- `schema`: The `Schema` object.
- `lengths`: Optional `FieldLengthTable` for document field lengths.
- `items`: Iterable of posting tuples.

#### `start_field(fieldname, fieldobj)`

Abstract. Called when starting a new field.

#### `start_term(text)`

Abstract. Called when starting a new term within a field.

#### `add(docnum, weight, vbytes, length=None)`

Abstract. Adds a posting to the current term.

#### `add_spell_word(fieldname, text)`

Called to add a word to the spelling index. Default does nothing.

#### `finish_term()`

Abstract. Called when finishing a term.

#### `finish_field()`

Called when finishing a field. Default does nothing.

#### `close()`

Called when done writing. Default does nothing.

### `PostingsWriter`

```python
class whoosh.codec.PostingsWriter
```

Abstract base class for writing posting lists (the inverted index).

**Methods:**

#### `start_postings(format_, terminfo)`

Abstract. Starts writing postings for a new term.

#### `add_posting(id_, weight, vbytes, length=None)`

Abstract. Adds a posting to the current term.

#### `finish_postings(allow_compact=True)`

Called when finished writing postings. Default does nothing.

#### `written()`

Abstract. Returns `True` if this writer has already written to disk.

## Reader Classes

### `FieldCursor`

```python
class whoosh.codec.FieldCursor
```

Abstract base class for iterating over terms in a field.

**Methods:**
- `first()`: Move to the first term.
- `find(string)`: Find a term matching or closest to `string`.
- `next()`: Move to the next term.
- `term()`: Returns the current term's text.

### `EmptyCursor`

```python
class whoosh.codec.EmptyCursor
```

A `FieldCursor` representing an empty field. All methods return `None` or
`False`.

### `TermsReader`

```python
class whoosh.codec.TermsReader
```

Abstract base class for reading the term dictionary and postings of a
segment.

**Methods:**
- `__contains__(term)`: Returns `True` if the term exists.
- `cursor(fieldname, fieldobj)`: Returns a `FieldCursor`.
- `terms()`: Yields `(fieldname, text)` tuples for all terms.
- `terms_from(fieldname, prefix)`: Yields terms from `fieldname` starting
  with `prefix`.
- `items()`: Yields `((fieldname, text), TermInfo)` tuples.
- `items_from(fieldname, prefix)`: Like `items()` but filtered by prefix.
- `term_info(fieldname, text)`: Returns a `TermInfo` for the term.
- `frequency(fieldname, text)`: Returns the total frequency.
- `doc_frequency(fieldname, text)`: Returns the document frequency.
- `matcher(fieldname, text, format_, scorer=None)`: Returns a `Matcher`.
- `indexed_field_names()`: Yields names of indexed fields.
- `close()`: Close the reader.

### `PerDocumentReader`

```python
class whoosh.codec.PerDocumentReader
```

Abstract base class for reading per-document values (columns, term vectors,
stored fields).

**Methods:**
- `close()`: Close the reader.
- `doc_count()`: Returns number of non-deleted documents.
- `doc_count_all()`: Returns total document count (including deleted).
- `has_deletions()`: Returns `True` if any documents are deleted.
- `is_deleted(docnum)`: Returns `True` if docnum is deleted.
- `deleted_docs()`: Yields docnums of deleted documents.
- `all_doc_ids()`: Yields docnums of all non-deleted documents.
- `supports_columns()`: Returns `True` if column storage is supported.
- `has_column(fieldname)`: Returns `True` if field has a column.
- `list_columns()`: Yields names of available columns.
- `column_reader(fieldname, column)`: Returns a column reader.
- `doc_field_length(docnum, fieldname)`: Returns field length for docnum.
- `field_length(fieldname)`: Returns total field length.
- `min_field_length(fieldname)`: Returns minimum field length.
- `max_field_length(fieldname)`: Returns maximum field length.
- `has_vector(docnum, fieldname)`: Returns `True` if docnum has a vector.
- `vector(docnum, fieldname, format_)`: Returns a `Matcher` for the vector.
- `stored_fields(docnum)`: Returns dict of stored field values.
- `all_stored_field()`: Yields stored fields for all documents.

### `MultiPerDocumentReader`

```python
class whoosh.codec.MultiPerDocumentReader(readers, offset=0)
```

Combines multiple `PerDocumentReader` instances into one for multi-segment
indices.

**Constructor:**
- `readers`: List of `PerDocumentReader` instances.
- `offset`: Base document offset (usually `0`).

## Automata

### `Automata`

```python
class whoosh.codec.Automata
```

Provides static methods for automata-based term matching, used by the
spelling corrector.

**Static Methods:**

#### `levenshtein_dfa(uterm, maxdist, prefix=0)`

Returns a deterministic finite automaton (DFA) that matches all edit-distance
variants of `uterm` within `maxdist` edits, optionally requiring a minimum
shared prefix of length `prefix`.

#### `find_matches(dfa, cur)`

Given a DFA and a `FieldCursor`, yields all matching terms.

**Methods:**

#### `terms_within(fieldcur, uterm, maxdist, prefix=0)`

Returns an iterator of matching terms within the given edit distance of
`uterm`.

## Segment

### `Segment`

```python
class whoosh.codec.Segment
```

Represents a segment of the index. Instances are pickled into the TOC file
to describe on-disk files.

**Class Attributes:**
- `COMPOUND_EXT = ".seg"`: Extension for compound segment files.

**Instance Attributes:**
- `indexname`: Base name of the segment.
- `segid`: Random unique ID string.
- `compound (bool)`: Whether this segment uses compound file format.

**Methods:**
- `make_filename(ext)`: Returns `f"{segment_id()}{ext}"`.
- `list_files(storage)`: Lists all files belonging to this segment.
- `create_file(storage, ext, **kwargs)`: Creates a new file for this segment.
- `open_file(storage, ext, **kwargs)`: Opens a file for this segment.
- `create_compound_file(storage)`: Combines all segment files into a
  compound `.seg` file.
- `open_compound_file(storage)`: Opens the compound segment file.
- `doc_count_all()`: Abstract. Returns total document count.
- `doc_count()`: Returns non-deleted document count.
- `set_doc_count(doccount)`: Sets the document count.
- `has_deletions()`: Returns `True` if any documents are deleted.
- `deleted_count()`: Abstract. Returns number of deleted documents.
- `deleted_docs()`: Abstract. Yields docnums of deleted documents.
- `delete_document(docnum, delete=True)`: Abstract. Deletes/undeletes a
  document.
- `is_deleted(docnum)`: Abstract. Returns `True` if docnum is deleted.
- `should_assemble()`: Returns `True` by default. Override to control
  compound file behavior.
- `validate(storage)`: Checks on-disk integrity of this segment.
- `segment_id()`: Returns the unique segment identifier string.
- `is_compound()`: Returns `True` if this segment uses compound file format.

### `WrappingSegment`

```python
class whoosh.codec.WrappingSegment(child)
```

A `Segment` that delegates all operations to a child segment.

**Constructor:**
- `child`: The underlying `Segment` instance to wrap.

## W3 Codec (Default)

The `W3` codec ("Whoosh 3") is the default index format, storing postings in
compressed blocks for efficient reading and skipping.

### `W3Codec`

```python
class whoosh.codec.whoosh3.W3Codec(blocklimit=128, compression=3, inlinelimit=1)
```

The default codec. Uses compressed blocks and term inlining for efficient
storage and fast lookups.

**Constructor:**
- `blocklimit`: Number of postings per block (default `128`).
- `compression`: zlib compression level (default `3`, `0` = no compression).
- `inlinelimit`: Maximum number of postings to inline directly in the term
  info (default `1`).

**File Extensions:**
- `.trm`: Term dictionary
- `.pst`: Postings
- `.vps`: Vector postings
- `.col`: Per-document value columns

### `W3PerDocWriter`

Writer for per-document values using the W3 format. Handles columns,
stored fields, term vectors, and field lengths.

### `W3FieldWriter`

Writer for the inverted term index using the W3 format. Uses a
`OrderedHashWriter` for the term dictionary and posts to a postings file.

### `W3LeafMatcher`

```python
class whoosh.codec.whoosh3.W3LeafMatcher(postfile, startoffset, length, format_, term=None, byteids=None, scorer=None)
```

Reads on-disk postings from the postings file and presents the
`Matcher` interface. Supports block-level skipping and lazy block loading.

**Optimization methods:**
- `block_min_id()`: Returns the first doc ID in the current block.
- `block_max_id()`: Returns the last doc ID in the current block.
- `block_min_length()`: Returns the minimum field length in the current block.
- `block_max_length()`: Returns the maximum field length in the current block.
- `block_max_weight()`: Returns the maximum weight in the current block.
- `skip_to_quality(minquality)`: Skips blocks exceeding a quality threshold.

### `W3TermsReader`

Reader for the term dictionary using the W3 format. Uses an
`OrderedHashReader` for fast lookups.

### `W3TermInfo`

```python
class whoosh.codec.whoosh3.W3TermInfo
```

Stores term statistics and posting location information. Supports inlining
small posting sets directly in the term dictionary for fast lookups.

**Flags:**
- `_FLAG_OFFSET` (0): Postings stored at an offset in the postings file.
- `_FLAG_INLINE_PICKLE` (1): Postings inlined as a pickled tuple.
- `_FLAG_INLINE_COMPACT` (2): Single posting compactly inlined.
- `_FLAG_INLINE_COMPACT_SHORT` (3): Multiple postings compactly inlined.

**Methods:**
- `add_block(block)`: Merges block statistics into this term info.
- `set_extent(offset, length)`: Sets offset and length of postings in file.
- `extent()`: Returns `(offset, length)`.
- `set_inlined(ids, weights, values)`: Sets inlined posting data.
- `set_compact_inline(id_, weight, value)`: Sets single inlined posting.
- `set_compact_short_inline(ids, weights, values)`: Sets multiple compact
  inlined postings.
- `is_inlined()`: Returns `True` if postings are inlined.
- `inlined_postings()`: Returns `(ids, weights, values)` tuples for inlined
  postings.
- `to_bytes()` / `from_bytes()`: Serialize/deserialize.

### `W3Segment`

```python
class whoosh.codec.whoosh3.W3Segment(codec, indexname, doccount=0, segid=None, deleted=None)
```

Segment class for the W3 codec. Stores a reference to the codec, document
count, and deleted document set.

## Plain Text Codec (Debugging)

### `PlainTextCodec`

```python
class whoosh.codec.plaintext.PlainTextCodec
```

A codec that stores the index as human-readable plain text. Intended for
debugging and manual inspection, not for production use.

**Class Attributes:**
- `length_stats = False`

**File extensions:**
- `.dcs`: Document (stored fields, columns, vectors)
- `.trm`: Term dictionary (plain text)

### `PlainPerDocWriter`

Plain text writer for per-document values.

### `PlainPerDocReader`

Plain text reader for per-document values.

### `PlainFieldWriter`

Plain text writer for the inverted index.

### `PlainTermsReader`

Plain text reader for the term dictionary.

### `PlainSegment`

```python
class whoosh.codec.plaintext.PlainSegment(indexname)
```

Segment class for the plain text codec. Does not support compound files
(`should_assume()` returns `False`).

## Memory Codec

### `MemoryCodec`

```python
class whoosh.codec.memory.MemoryCodec
```

An in-memory-only codec for testing. Stores all data in Python objects
rather than on disk.

**Class Attributes:**
- `storage`: A `RamStorage` instance.
- `segment`: A `MemSegment` instance.

**Methods:**
- `writer(schema)`: Returns a `MemWriter`.
- `reader(schema)`: Returns a `SegmentReader`.

### `MemWriter`

```python
class whoosh.codec.memory.MemWriter
```

A `SegmentWriter` subclass that commits immediately without merging.

### `MemPerDocWriter`

In-memory writer for per-document values.

### `MemPerDocReader`

In-memory reader for per-document values.

### `MemFieldWriter`

In-memory writer for the inverted index.

### `MemTermsReader`

In-memory reader for the term dictionary.

### `MemSegment`

```python
class whoosh.codec.memory.MemSegment(codec, indexname)
```

In-memory segment storing all data in Python dictionaries (inverted index,
stored fields, lengths, vectors, term infos). Uses a `Lock` for thread-safe
access.
