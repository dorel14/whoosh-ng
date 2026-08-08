---
title: "Glossary"
nav_order: 34
permalink: /en/guides/glossary/
---

# Glossary

A glossary of key terms used in Whoosh.

## Analysis

The process of converting text into tokens (individual units like words or
terms) for indexing. Involves tokenization, normalization (lowercasing,
stemming), and filtering (stop word removal, etc.).

## Analyzer

A chain of `Tokenizer` and `Filter` objects that processes text into
tokens. Examples include `RegexTokenizer`, `NgramTokenizer`, `LowercaseFilter`,
`StopFilter`, and `StemmerFilter`.

## Compound File

A file format that combines multiple index segment files into a single
`.seg` file. This can improve performance on some filesystems by reducing
file handle usage. Configured via the codec's `should_assemble` setting.

## Document

A single record in the index, similar to a row in a database. A document
contains fields (analogous to columns).

## Field

A named attribute of a document. Fields have a type (defined by `FieldType`)
that determines how the field's value is indexed and stored.

## Field Type

The class (e.g., `TEXT`, `ID`, `NUMERIC`, `DATETIME`, `BOOLEAN`) that
defines how a field's value is tokenized, stored, indexed, and made
sortable/facetable.

## Filter

An `Analyzer` component that processes, transforms, or filters tokens
after tokenization. Examples: `LowercaseFilter`, `StopFilter`,
`StemmerFilter`.

## Format

A `Format` object controls how posting information (term frequency, positions,
character offsets) is encoded for each field in the inverted index.
Examples: `Existence`, `Frequency`, `Positions`, `Characters`.

## Fragmentation

The process of selecting text spans around matched terms for highlighting.

## Highlighter

The `whoosh.highlight` module, which provides formatters, fragmenters, and
scorers for highlighting search terms in documents.

## Index

The collection of segment files that store the inverted index, document
data, and metadata (the table of contents, or TOC).

## IndexWriter

The `IndexWriter` class is used to create and modify the index. It buffers
document additions and deletions and commits them to disk.

## Inverted Index

The core data structure of a search engine: for each unique term, it stores a
list of documents (and positions) where that term appears.

## Matcher

An object that iterates over matching documents in the postings list for a
query. Matchers can be combined (union, intersection, etc.) for compound
queries.

## Posting

A single entry in the inverted index: a (document ID, term frequency, value)
tuple for a given term.

## Schema

Defines the fields, their types, and indexing options for an index. A schema
is passed to `Storage.create_index()`.

## Scorer

An object that computes a relevance score for a document given a query and
term weights. Different weighting models (BM25, TF-IDF, etc.) use different
scorers.

## Segment

A self-contained portion of the inverted index. An index may consist of
multiple segments. Segments are merged periodically (during optimize or
merge operations) to improve performance.

## Sort Key

A value computed per-document (via a `FacetType` and its `Categorizer`)
used to order results during sorting and faceting.

## Stemming

The process of reducing words to their root form (e.g., "running" → "run",
"cats" → "cat") to improve recall by matching inflected forms.

## Stop Words

High-frequency, low-information words (e.g., "the", "a", "and") that are
typically filtered out during indexing.

## Term

A unique (field name, token text) pair in the inverted index.

## Term Vector

Optional per-document data structure storing the terms (and optionally
positions and character offsets) that appear in a document's field, enabling
features like highlighting and pseudo-relevance feedback.

## Tokenizer

An `Analyzer` component that splits input text into tokens. Examples:
`RegexTokenizer`, `PathTokenizer`, `NgramTokenizer`.

## Whoosh Query

Whoosh's own query syntax, parsed by `QueryParser`. Supports fielded
search, phrase queries, wildcards, ranges, and more.
