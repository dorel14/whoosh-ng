---
title: "Whoosh-NG Documentation"
nav_order: 1
permalink: /
---

# Whoosh-NG Documentation

> **Version**: Latest | Last updated: 2026-07-26

Welcome to the official documentation for **Whoosh-NG**, a pure-Python full-text indexing and search library modernized for 2025+.

## Language Selection

This documentation is available in two languages:

- **[English Documentation]({{ '/en/quickstart/' | relative_url }})** — Complete technical documentation in English (source language)
- **[Documentation Française]({{ '/fr/quickstart/' | relative_url }})** — Traduction française complète

Both versions are kept synchronized, with code examples remaining in English for consistency.

## Documentation Structure

### Getting Started

- **[Installation]({{ '/en/guides/installation/' | relative_url }})** — Setup instructions and configuration
- **[Quick Start]({{ '/en/quickstart/' | relative_url }})** — 5-minute tutorial to create your first index
- **[Core Concepts]({{ '/en/guides/core-concepts/' | relative_url }})** — Understanding schemas, fields, and search

### User Guides

- **[Indexing]({{ '/en/guides/indexing/' | relative_url }})** — Adding, updating, and deleting documents
- **[Searching]({{ '/en/guides/searching/' | relative_url }})** — Query parsing, highlighting, and facets
- **[Schema Design]({{ '/en/guides/schema/' | relative_url }})** — Field types, storage, and indexing options
- **[Query Language]({{ '/en/guides/query/' | relative_url }})** — Lucene-like query syntax
- **[Middleware]({{ '/en/guides/middleware/' | relative_url }})** — Pipeline hooks and custom middleware
- **[Backends]({{ '/en/guides/backends/' | relative_url }})** — File, SQLite, and memory storage
- **[Plugins]({{ '/en/guides/plugins/' | relative_url }})** — Extending Whoosh-NG with plugins
- **[Autocomplete]({{ '/en/guides/autocomplete/' | relative_url }})** — Autocomplete providers
- **[Vector Search]({{ '/en/guides/vector/' | relative_url }})** — NumPy, HNSW, and Faiss integration
- **[Monitoring]({{ '/en/guides/monitoring/' | relative_url }})** — Metrics and observability
- **[Migration]({{ '/en/guides/migration/' | relative_url }})** — Migrating from classic Whoosh

### API Reference

- **[API Overview]({{ '/en/api/overview/' | relative_url }})** — Complete module reference
- **[Core API]({{ '/en/api/core/' | relative_url }})** — Index creation and management
- **[Fields]({{ '/en/api/fields/' | relative_url }})** — Schema and field type definitions
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
- **[FastAPI Integration]({{ '/en/examples/fastapi/' | relative_url }})** — REST API with FastAPI
- **[Middleware Examples]({{ '/en/examples/middleware/' | relative_url }})** — Custom middleware patterns
- **[Plugin Development]({{ '/en/examples/plugin-dev/' | relative_url }})** — Building plugins

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

## Contributing

Contributions are welcome! Please read our contributing guide for details on how to submit pull requests, add features, or report bugs.

## License

This project is licensed under the MIT License.
