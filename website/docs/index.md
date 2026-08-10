---
title: "Whoosh-NG Documentation"
sidebar_position: 1
sidebars: docs
---

# Whoosh-NG Documentation

> **Latest release**: v4.3.0 | [View releases on GitHub](https://github.com/dorel14/whoosh-ng/releases) | Last updated: 2026-08-10

Welcome to the official documentation for **Whoosh-NG**, a pure-Python full-text indexing and search library modernized for 2025+.

## Language Selection

This documentation is available in two languages:

- **[English Documentation](/core/quickstart)** — Complete technical documentation in English (source language)
- **[Documentation Française](https://dorel14.github.io/whoosh-ng/core/quickstart)** — Traduction française complète

Both versions are kept synchronized, with code examples remaining in English for consistency.

## Documentation Structure

### Core (Classic Whoosh)

- **[Quick Start](/core/quickstart)** — 5-minute tutorial
- **[Installation](/core/installation)** — Setup instructions
- **[Core Concepts](/core/core-concepts)** — Schemas, fields, search
- **[Indexing](/core/indexing)** — Adding and updating documents
- **[Searching](/core/searching)** — Query parsing and results
- **[Schema Design](/core/schema)** — Field types and storage
- **[Query Language](/core/query)** — Lucene-like query syntax
- **[Backends](/core/backends)** — File, SQLite, memory storage
- **[Dates](/core/dates)** — Date field handling
- **[Nested Documents](/core/nested)** — Nested document support
- **[Glossary](/core/glossary)** — Key terms and definitions
- **[Migration](/core/migration)** — Migrating from classic Whoosh
- **[Legacy Cleanup](/core/legacy-cleanup)** — Legacy code removal
- **[Translation Status](/core/translation-status)** — i18n progress

### Modern (New Features)

- **[Middleware](/modern/middleware)** — Pipeline hooks and middleware
- **[Middleware & Plugin Pipeline](/modern/middleware-sprint-c)** — Hook-based pipeline
- **[Plugins](/modern/plugins)** — Extending Whoosh-NG
- **[Plugin System](/modern/plugins-sprint-c)** — PluginManager API
- **[Autocomplete](/modern/autocomplete)** — Autocomplete providers
- **[Autocomplete Providers](/modern/autocomplete-sprint-d)** — NGram, Fuzzy, InvertedIndex
- **[Vector Search](/modern/vector)** — NumPy, HNSW, Faiss
- **[Modern Indexing](/modern/modern-indexing)** — BatchIndexWriter, AnalyzerCache
- **[Monitoring](/modern/monitoring)** — Metrics and observability
- **[Performance](/modern/performance)** — Benchmarking and optimization
- **[Linguistics & Synonyms](/modern/linguistics-sprint-d)** — SynonymManager
- **[Stemming](/modern/stemming)** — Language stemmers
- **[Stemmer Providers](/modern/stemming-sprint-d)** — PyStemmer backends
- **[N-grams](/modern/ngrams)** — N-gram tokenization
- **[Storage Providers](/modern/storage-providers)** — Hybrid storage backends

### API Reference

- **[API Overview](/api/overview)** — Complete module reference
- **[Core API](/api/core)** — Index creation and management
- **[Fields](/api/fields)** — Schema and field type definitions
- **[Analysis](/api/analysis)** — Tokenizers, filters, and analyzers
- **[Highlight](/api/highlight)** — Formatters, fragmenters, scorers
- **[Spelling](/api/spelling)** — Spell checking and query correction
- **[Sorting](/api/sorting)** — Facets and sort key computation
- **[Collectors](/api/collectors)** — Result collection strategies
- **[Reading](/api/reading)** — Index readers and term vectors
- **[Matching](/api/matching)** — Matcher classes and utilities
- **[Codecs](/api/codecs)** — Index format codecs and segment management
- **[Formats](/api/formats)** — Posting format encoders/decoders
- **[Columns](/api/columns)** — Per-document column storage
- **[Idsets](/api/idsets)** — Document ID set implementations
- **[Automata](/api/automata)** — Finite state automata and FSTs
- **[Classify](/api/classify)** — Query expansion and clustering
- **[Language](/api/lang)** — Stemmers, stop words, and language utilities
- **[File DB / Storage](/api/filedb_storage)** — Storage and file I/O
- **[Writing API](/api/writing)** — IndexWriter interface
- **[Searching API](/api/searching)** — Searcher and Results
- **[Query API](/api/query)** — Query classes and parsers
- **[Events](/api/events)** — Event bus system
- **[Middleware API](/api/middleware)** — Middleware pipeline
- **[Plugins API](/api/plugins)** — Plugin system and registry
- **[Backends API](/api/backends)** — Storage backend abstractions
- **[Modern API](/api/modern)** — Modern extensions

### Examples

- **[Basic Indexing](/examples/basic-indexing)** — Document indexing examples
- **[Search Examples](/examples/search)** — Querying and retrieving results
- **[Search Models](/examples/search-models)** — Auto-mapping Python models to Whoosh schemas
- **[FastAPI Integration](/examples/fastapi-search)** — REST API with FastAPI
- **[Middleware Examples](/examples/middleware)** — Custom middleware patterns
- **[Middleware Pipeline](/examples/middleware-pipeline)** — Retry, cache, logging
- **[Movie Search App](/examples/movie-search)** — Complete movie search application
- **[Plugin Development](/examples/plugin-dev)** — Building plugins
- **[Data Sources](/examples/data-sources)** — SQLSource, RESTSource, GraphQLSource, FastCSVSource, JSONSource, ParquetSource, PandasSource, PolarsSource, SQLAlchemySource, PeeweeSource, TortoiseSource
- **[Schema Discovery](/examples/schema-discovery)** — Result-set introspection
- **[Facet Manager](/examples/facets)** — Auto-discovery and manual overrides
- **[Validation Framework](/examples/validation)** — 4-level validation
- **[SearchView](/examples/search-view)** — Full pipeline integration
- **[Autocomplete](/examples/autocomplete)** — Autocomplete provider examples
- **[Vector Search](/examples/vector-search)** — NumPy, HNSW, and Faiss integrations

## Quick Overview

Whoosh-NG combines classic Whoosh's pure-Python full-text search with modern features:

- **Pure Python** — No native dependencies, works anywhere Python runs
- **Embedded search engine** — No separate server required
- **Plugin architecture** — Extensible with vector search, autocomplete, and more
- **Middleware pipeline** — Cross-cutting concerns like metrics, caching, encryption
- **Vector search support** — NumPy, HNSW, and Faiss integrations
- **Async support** — Optional async/await support via extras

## Quick Links

- **Project Repository**: [GitHub - whoosh-ng](https://github.com/dorel14/whoosh-ng)
- **PyPI Package**: [whoosh-ng](https://pypi.org/project/whoosh-ng/)
- **Issue Tracker**: [GitHub Issues](https://github.com/dorel14/whoosh-ng/issues)
- **LLM-Friendly Docs**:
  - [`llms.txt`](/llms.txt) — Index of all documentation pages
  - [`llms-full.txt`](/llms-full.txt) — Complete API documentation concatenated

## Contributing

Contributions are welcome! Please read our contributing guide for details on how to submit pull requests, add features, or report bugs.

## License

This project is licensed under the MIT License.
