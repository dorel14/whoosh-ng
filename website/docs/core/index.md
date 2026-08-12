---
title: "Core"
sidebar_position: 1
sidebars: docs
---

# Core

Whoosh-NG builds on the battle-tested foundations of the original **Whoosh**
library. This section documents the **classic full-text search features** that
have powered Whoosh for over a decade — the engine, schema, analyzers, scoring,
and all the concepts you need to build a reliable search experience.

> These features are stable, backwards-compatible with Whoosh 1.x/2.x, and live
> in the `whoosh` package. New, optional extensions (vector search, plugins,
> middleware, storage providers) are documented under [Modern](/modern).

## What you'll find here

| Guide | Description |
|-------|-------------|
| [Quickstart](/core/quickstart) | Index your first documents in five minutes |
| [Installation](/core/installation) | Install Whoosh-NG and its optional extras |
| [Introduction to Whoosh](/core/intro) | What Whoosh is and what it can do for you |
| [Core Concepts](/core/core-concepts) | Index, Schema, Writer, Searcher, and data flow |
| [About Analyzers](/core/analysis) | Tokenizers, filters, and the analysis pipeline |
| [Schema Design](/core/schema) | Field types and how to model your documents |
| [Indexing](/core/indexing) | Add, update, and delete documents |
| [Searching](/core/searching) | Run queries, work with results, sort and filter |
| [Query Language](/core/query) | The Whoosh query syntax and `QueryParser` |
| [Stemming & Stop Words](/core/stemming) | Reduce words to roots and filter noise |
| [N-grams](/core/ngrams) | Substring, prefix, and autocomplete matching |
| [Dates & Numeric Ranges](/core/dates) | Range queries and faceting on numbers/dates |
| [Sorting](/core/sorting) | Facets and sort keys for ordering results |
| [Highlighting](/core/highlight) | Build highlighted result excerpts |
| [Did you mean...](/core/spelling) | Correct typos in user queries |
| [Query Expansion & Keywords](/core/keywords) | Key-term extraction and "more like this" |
| [Nested Documents](/core/nested) | Parent-child document hierarchies |
| [Concurrency & Locking](/core/threads) | Threads, write locks, and index versioning |
| [Batch Indexing](/core/batch) | Tips for speeding up large batch indexes |
| [Field Caches](/core/fieldcaches) | Caching behavior for sorting and faceting |
| [Whoosh Recipes](/core/recipes) | Handy code snippets for common tasks |

## Classic analysis pipeline

Whoosh turns raw text into searchable tokens through a composable pipeline:

```
Text  →  Tokenizer  →  Filters (lowercase, stop words, stemming)  →  Indexed terms
```

The [Stemming & Stop Words](/core/stemming) and [N-grams](/core/ngrams) guides
show how to customize this pipeline for your language and use case.

## Reference

- [Glossary](/core/glossary) — Key terms used throughout the documentation
- [Migration Guide](/core/migration) — Upgrading from Whoosh or Whoosh-Reloaded
- [Legacy Cleanup Strategy](/core/legacy-cleanup) — How the modern typed surface is evolving

## Next steps

Ready for the new stuff? Head over to [Modern](/modern) to discover vector
search, the plugin system, middleware pipelines, and pluggable storage.
