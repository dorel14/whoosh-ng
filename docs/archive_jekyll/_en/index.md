---
title: "Whoosh-NG Documentation"
nav_order: 1
permalink: /en/
---

# Whoosh-NG Documentation

> **Latest release**: v4.3.0 | [View releases on GitHub](https://github.com/dorel14/whoosh-ng/releases) | Last updated: 2026-08-10

Welcome to the official documentation for **Whoosh-NG**, a pure-Python full-text indexing and search library modernized for 2025+.

## Language Selection

This documentation is available in two languages:

- **[English Documentation]({{ '/en/quickstart/' | relative_url }})** — Complete technical documentation in English (source language)
- **[Documentation Française]({{ '/fr/quickstart/' | relative_url }})** — Traduction française complète

Both versions are kept synchronized, with code examples remaining in English for consistency.

## Documentation Structure

### Core (Classic Whoosh)

- **[Quick Start]({{ '/en/quickstart/' | relative_url }})** — 5-minute tutorial
- **[Installation]({{ '/en/guides/installation/' | relative_url }})** — Setup instructions
- **[Core Concepts]({{ '/en/guides/core-concepts/' | relative_url }})** — Schemas, fields, search
- **[Indexing]({{ '/en/guides/indexing/' | relative_url }})** — Adding and updating documents
- **[Searching]({{ '/en/guides/searching/' | relative_url }})** — Query parsing and results
- **[Schema Design]({{ '/en/guides/schema/' | relative_url }})** — Field types and storage
- **[Query Language]({{ '/en/guides/query/' | relative_url }})** — Lucene-like query syntax
- **[Backends]({{ '/en/guides/backends/' | relative_url }})** — File, SQLite, memory storage
- **[Dates]({{ '/en/guides/dates/' | relative_url }})** — Date field handling
- **[Nested Documents]({{ '/en/guides/nested/' | relative_url }})** — Nested document support
- **[Glossary]({{ '/en/guides/glossary/' | relative_url }})** — Key terms and definitions
- **[Migration]({{ '/en/guides/migration/' | relative_url }})** — Migrating from classic Whoosh
- **[Legacy Cleanup]({{ '/en/guides/legacy-cleanup/' | relative_url }})** — Legacy code removal
- **[Translation Status]({{ '/en/guides/translation-status/' | relative_url }})** — i18n progress

### Modern (New Features)

- **[Middleware]({{ '/en/guides/middleware/' | relative_url }})** — Pipeline hooks and middleware
- **[Middleware & Plugin Pipeline]({{ '/en/guides/middleware-sprint-c/' | relative_url }})** — Hook-based pipeline
- **[Plugins]({{ '/en/guides/plugins/' | relative_url }})** — Extending Whoosh-NG
- **[Plugin System]({{ '/en/guides/plugins-sprint-c/' | relative_url }})** — PluginManager API
- **[Autocomplete]({{ '/en/guides/autocomplete/' | relative_url }})** — Autocomplete providers
- **[Autocomplete Providers]({{ '/en/guides/autocomplete-sprint-d/' | relative_url }})** — NGram, Fuzzy, InvertedIndex
- **[Vector Search]({{ '/en/guides/vector/' | relative_url }})** — NumPy, HNSW, Faiss
- **[Modern Indexing]({{ '/en/guides/modern-indexing/' | relative_url }})** — BatchIndexWriter, AnalyzerCache
- **[Monitoring]({{ '/en/guides/monitoring/' | relative_url }})** — Metrics and observability
- **[Performance]({{ '/en/guides/performance/' | relative_url }})** — Benchmarking and optimization
- **[Linguistics & Synonyms]({{ '/en/guides/linguistics-sprint-d/' | relative_url }})** — SynonymManager
- **[Stemming]({{ '/en/guides/stemming/' | relative_url }})** — Language stemmers
- **[Stemmer Providers]({{ '/en/guides/stemming-sprint-d/' | relative_url }})** — PyStemmer backends
- **[N-grams]({{ '/en/guides/ngrams/' | relative_url }})** — N-gram tokenization
- **[Storage Providers]({{ '/en/guides/storage-providers/' | relative_url }})** — Hybrid storage backends

### API Reference

- **[API Overview]({{ '/en/api/overview/' | relative_url }})** — Complete module reference
- **[Core API]({{ '/en/api/core/' | relative_url }})** — Index creation and management
- **[Fields]({{ '/en/api/fields/' | relative_url }})** — Schema and field type definitions
- **[Analysis]({{ '/en/api/analysis/' | relative_url }})** — Tokenizers, filters, and analyzers
- **[Highlight]({{ '/en/api/highlight/' | relative_url }})** — Formatters, fragmenters, scorers
- **[Spelling]({{ '/en/api/spelling/' | relative_url }})** — Spell checking and query correction
- **[Sorting]({{ '/en/api/sorting/' | relative_url }})** — Facets and sort key computation
- **[Collectors]({{ '/en/api/collectors/' | relative_url }})** — Result collection strategies
- **[Reading]({{ '/en/api/reading/' | relative_url }})** — Index readers and term vectors
- **[Matching]({{ '/en/api/matching/' | relative_url }})** — Matcher classes and utilities
- **[Codecs]({{ '/en/api/codecs/' | relative_url }})** — Index format codecs and segment management
- **[Formats]({{ '/en/api/formats/' | relative_url }})** — Posting format encoders/decoders
- **[Columns]({{ '/en/api/columns/' | relative_url }})** — Per-document column storage
- **[Idsets]({{ '/en/api/idsets/' | relative_url }})** — Document ID set implementations
- **[Automata]({{ '/en/api/automata/' | relative_url }})** — Finite state automata and FSTs
- **[Classify]({{ '/en/api/classify/' | relative_url }})** — Query expansion and clustering
- **[Language]({{ '/en/api/lang/' | relative_url }})** — Stemmers, stop words, and language utilities
- **[File DB / Storage]({{ '/en/api/filedb_storage/' | relative_url }})** — Storage and file I/O
- **[Writing API]({{ '/en/api/writing/' | relative_url }})** — IndexWriter interface
- **[Searching API]({{ '/en/api/searching/' | relative_url }})** — Searcher and Results
- **[Query API]({{ '/en/api/query/' | relative_url }})** — Query classes and parsers
- **[Events]({{ '/en/api/events/' | relative_url }})** — Event bus system
- **[Middleware API]({{ '/en/api/middleware/' | relative_url }})** — Middleware pipeline
- **[Plugins API]({{ '/en/api/plugins/' | relative_url }})** — Plugin system and registry
- **[Backends API]({{ '/en/api/backends/' | relative_url }})** — Storage backend abstractions
- **[Modern API]({{ '/en/api/modern/' | relative_url }})** — Modern extensions

### Examples

- **[Basic Indexing]({{ '/en/examples/basic-indexing/' | relative_url }})** — Document indexing examples
- **[Search Examples]({{ '/en/examples/search/' | relative_url }})** — Querying and retrieving results
- **[Search Models]({{ '/en/examples/search-models/' | relative_url }})** — Auto-mapping Python models to Whoosh schemas
- **[FastAPI Integration]({{ '/en/examples/fastapi-search/' | relative_url }})** — REST API with FastAPI
- **[Middleware Examples]({{ '/en/examples/middleware/' | relative_url }})** — Custom middleware patterns
- **[Middleware Pipeline]({{ '/en/examples/middleware-pipeline/' | relative_url }})** — Retry, cache, logging
- **[Movie Search App]({{ '/en/examples/movie-search/' | relative_url }})** — Complete movie search application
- **[Plugin Development]({{ '/en/examples/plugin-dev/' | relative_url }})** — Building plugins
- **[Data Sources]({{ '/en/examples/data-sources/' | relative_url }})** — SQLSource, RESTSource, GraphQLSource, FastCSVSource, JSONSource, ParquetSource, PandasSource, PolarsSource, SQLAlchemySource, PeeweeSource, TortoiseSource
- **[Schema Discovery]({{ '/en/examples/schema-discovery/' | relative_url }})** — Result-set introspection
- **[Facet Manager]({{ '/en/examples/facets/' | relative_url }})** — Auto-discovery and manual overrides
- **[Validation Framework]({{ '/en/examples/validation/' | relative_url }})** — 4-level validation
- **[SearchView]({{ '/en/examples/search-view/' | relative_url }})** — Full pipeline integration
- **[Autocomplete]({{ '/en/examples/autocomplete/' | relative_url }})** — Autocomplete provider examples
- **[Vector Search]({{ '/en/examples/vector-search/' | relative_url }})** — NumPy, HNSW, and Faiss integrations

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
  - [`llms.txt`]({{ '/llms.txt' | relative_url }}) — Index of all documentation pages
  - [`llms-full.txt`]({{ '/llms-full.txt' | relative_url }}) — Complete API documentation concatenated

## Contributing

Contributions are welcome! Please read our contributing guide for details on how to submit pull requests, add features, or report bugs.

## License

This project is licensed under the MIT License.
