---
color_scheme: dark
title: "Whoosh-NG Documentation"
nav_order: 0
permalink: /whoosh-ng
---

# Whoosh-NG Documentation

> **Version**: Latest | Last updated: 2026-07-12

Welcome to the official documentation for **Whoosh-NG**, a pure-Python full-text indexing and search library modernized for 2025+.

## Language Selection

This documentation is available in two languages:

- **[English Documentation](/en/quickstart/)** — Complete technical documentation in English (source language)
- **[Documentation Française](/fr/quickstart/)** — Traduction française complète

Both versions are kept synchronized, with code examples remaining in English for consistency.

## Documentation Structure

### Getting Started

- **[Installation](/en/guides/installation/)** — Setup instructions and configuration
- **[Quick Start](/en/quickstart/)** — 5-minute tutorial to create your first index
- **[Core Concepts](/en/guides/core-concepts/)** — Understanding schemas, fields, and search

### User Guides

- **[Indexing](/en/guides/indexing/)** — Adding, updating, and deleting documents
- **[Searching](/en/guides/searching/)** — Query parsing, highlighting, and facets
- **[Schema Design](/en/guides/schema/)** — Field types, storage, and indexing options
- **[Query Language](/en/guides/query/)** — Lucene-like query syntax
- **[Middleware](/en/guides/middleware/)** — Pipeline hooks and custom middleware
- **[Backends](/en/guides/backends/)** — File, SQLite, and memory storage
- **[Plugins](/en/guides/plugins/)** — Extending Whoosh-NG with plugins
- **[Autocomplete](/en/guides/autocomplete/)** — Autocomplete providers
- **[Vector Search](/en/guides/vector/)** — NumPy, HNSW, and Faiss integration
- **[Monitoring](/en/guides/monitoring/)** — Metrics and observability
- **[Migration](/en/guides/migration/)** — Migrating from classic Whoosh

### API Reference

- **[API Overview](/en/api/overview/)** — Complete module reference
- **[Core API](/en/api/core/)** — Index creation and management
- **[Fields](/en/api/fields/)** — Schema and field type definitions
- **[Writing API](/en/api/writing/)** — IndexWriter interface
- **[Searching API](/en/api/searching/)** — Searcher and Results
- **[Query API](/en/api/query/)** — Query classes and parsers
- **[Events](/en/api/events/)** — Event bus system
- **[Middleware API](/en/api/middleware/)** — Middleware pipeline
- **[Plugins API](/en/api/plugins/)** — Plugin system and registry
- **[Backends API](/en/api/backends/)** — Storage backend abstractions
- **[Modern API](/en/api/modern/)** — Modern extensions

### Examples

- **[Basic Indexing](/en/examples/basic-indexing/)** — Document indexing examples
- **[Search Examples](/en/examples/search/)** — Querying and retrieving results
- **[FastAPI Integration](/en/examples/fastapi/)** — REST API with FastAPI
- **[Middleware Examples](/en/examples/middleware/)** — Custom middleware patterns
- **[Plugin Development](/en/examples/plugin-dev/)** — Building plugins

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