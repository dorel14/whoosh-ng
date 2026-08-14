---
title: "Modern"
sidebar_position: 20
sidebars: docs
---

# Modern

Whoosh-NG is more than a fork — it is the **evolution** of Whoosh for modern
Python applications. This section documents the optional, opt-in extensions that
make Whoosh-NG production-ready in today's stacks: semantic vector search,
a plugin architecture, a middleware pipeline, linguistics, and pluggable cloud
storage.

> All features here are **optional extras**: the core engine has zero mandatory
> third-party dependencies. Classic features live under [Core](/core).

## Highlights

```text
┌─────────────────────────────────────────────────────────────┐
│  Whoosh-NG Modern Extensions                                │
├─────────────────────────────────────────────────────────────┤
│  🔌 Plugins        → PluginManager, entry-point discovery   │
│  🧩 Middleware     → cross-cutting indexing/search hooks    │
│  🧠 Vector Search  → NumPy, HNSW, Faiss, Qdrant providers   │
│  🌐 Linguistics    → synonyms, language-aware analyzers      │
│  🔤 Stemming       → PyStemmer-backed provider system       │
│  ☁️  Storage        → S3, hybrid cache + remote backends     │
│  ⚡ Performance    → benchmarks and optimization guides     │
└─────────────────────────────────────────────────────────────┘
```

## Guides

| Guide | Description |
|-------|-------------|
| [Plugins](/modern/plugins) | The plugin architecture and how to register extensions |
| [Plugin System](/modern/plugins-advanced) | `PluginManager` API and lifecycle |
| [Middleware](/modern/middleware) | The middleware base classes and context |
| [Middleware & Plugin Pipeline](/modern/middleware-pipeline) | Compose cross-cutting concerns |
| [Autocomplete](/modern/autocomplete) | Autocomplete providers |
| [Autocomplete Providers](/modern/autocomplete-providers) | NGram, Fuzzy, InvertedIndex backends |
| [Vector Search](/modern/vector) | Semantic search with embeddings |
| [Modern Indexing](/modern/modern-indexing) | `BatchIndexWriter`, `AnalyzerCache` |
| [Monitoring](/modern/monitoring) | Metrics and observability |
| [Performance](/modern/performance) | Benchmarking and optimization |
| [Linguistics & Synonyms](/modern/linguistics) | `SynonymManager` and linguistic engine |
| [Stemmer Providers](/modern/stemming-providers) | PyStemmer backends and auto-detection |
| [Storage Providers](/modern/storage-providers) | Hybrid, S3, and async storage backends |
| [Embeddings](/modern/embeddings) | ONNX Runtime CPU-friendly embedding provider |
| [Auto-indexing](/modern/auto-indexing) | Schema discovery and data-source driven indexing |
| [SearchApplication](/modern/search-application) | Unified entry point for indexing and search |
| [Provider Integration](/modern/provider-integration) | End-to-end pipeline integration |
| [Configuration Engine](/modern/configuration-engine) | Typed configuration surface |

## Where to start

1. New to Whoosh-NG? Begin with [Core → Quickstart](/core/quickstart).
2. Want semantic search? Jump to [Vector Search](/modern/vector).
3. Building a web service? See [Plugins](/modern/plugins) and
   [Storage Providers](/modern/storage-providers).

> 💡 Tip: the classic [Stemming](/core/stemming) and [N-grams](/core/ngrams)
> guides now live under **Core**, since they are part of the original Whoosh
> feature set.
