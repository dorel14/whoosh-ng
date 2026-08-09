---
title: "API Reference"
sidebar_position: 60
sidebars: apiSidebar
---

# API Reference

The Whoosh-NG API reference is auto-generated from source code using
[pydoctor](https://pydoctor.readthedocs.io/), which parses Python modules
and generates HTML documentation from docstrings.

:::note
If the embedded documentation does not display, the API docs may not have
been generated yet in this deployment. [View on GitHub](https://github.com/dorel14/whoosh-ng/tree/master/website/static/api_docs) for the full API documentation, or check the
[API modules list](#api-modules) below for a structured overview.
:::

## API Modules

### Core API

| Module | Description |
|--------|-------------|
| `whoosh.index` | High-level index creation, opening, and management |
| `whoosh.fields` | Schema and field type definitions |
| `whoosh.writing` | Writer classes and merge policies |
| `whoosh.searching` | Searcher, Results, and collectors |
| `whoosh.query` | Query classes and parsers |
| `whoosh.qparser` | Query parser implementation |
| `whoosh.analysis` | Tokenizers, filters, and analyzers |
| `whoosh.highlight` | Search result highlighting |
| `whoosh.spelling` | Spelling correction |
| `whoosh.sorting` | Facets and sorting |
| `whoosh.event_bus` | Event system |
| `whoosh.hooks` | Hook system |
| `whoosh.middleware` | Middleware pipeline |
| `whoosh.plugins` | Plugin system and registry |
| `whoosh.backends` | Storage backends |

### Modern API

| Module | Description |
|--------|-------------|
| `whoosh_modern.data_sources` | Data source protocol and implementations |
| `whoosh_modern.views` | SearchView unified interface |
| `whoosh_modern.middleware` | Retry, cache, logging middleware |
| `whoosh_modern.facets` | FacetManager for auto-discovery |
| `whoosh_modern.validation` | 4-level validation framework |
| `whoosh_modern.indexing` | BatchIndexWriter, AnalyzerCache |
| `whoosh_modern.linguistics` | Linguistic engine (stemmers, synonyms) |
| `whoosh_modern.storage` | Storage providers (HybridStorage, etc.) |
| `whoosh_modern.vector` | NumpyProvider for vector similarity |
| `whoosh_modern.autocomplete` | Autocomplete provider plugins |
| `whoosh_fastapi` | FastAPI REST API endpoints |
| `whoosh_admin` | Admin UI dashboard |

:::info
For the full interactive API documentation, run:
```bash
pip install pydoctor
python scripts/generate_api_docs.py
```
Then open `website/static/api_docs/index.html` in your browser.
:::
