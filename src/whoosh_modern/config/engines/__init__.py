"""Specialized engines for the Whoosh-NG configuration system.

Each engine turns a merged :class:`WhooshNGConfig` into a concrete Whoosh-NG
component:

- :class:`SchemaEngine` — Whoosh ``Schema`` from ``fields``
- :class:`AnalyzerEngine` — analyzer mapping from ``fields``
- :class:`DataSourceEngine` — ``DataSource`` instance from ``data_source``
- :class:`StorageEngine` — ``SyncStorageProvider`` from ``storage``
- :class:`SearchModelEngine` — search-model mapping from ``fields``
- :class:`FacetEngine` — ``FacetManager`` from faceted fields
- :class:`PluginEngine` — ``PluginManager`` from plugin config
- :class:`APIEngine` — FastAPI app from search config
- :class:`VectorEngine` — ``VectorProvider`` from vector config
- :class:`EmbeddingEngine` — ``EmbeddingProvider`` from embedding config
- :class:`LanguageEngine` — ``LanguageDetector`` from language detection config

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from whoosh_modern.config.engines.analyzer import AnalyzerEngine
from whoosh_modern.config.engines.api import APIEngine
from whoosh_modern.config.engines.data_source import DataSourceEngine
from whoosh_modern.config.engines.embedding import EmbeddingEngine
from whoosh_modern.config.engines.facet import FacetEngine
from whoosh_modern.config.engines.language import LanguageEngine
from whoosh_modern.config.engines.plugin import PluginEngine
from whoosh_modern.config.engines.schema import SchemaEngine
from whoosh_modern.config.engines.search_model import SearchModelEngine
from whoosh_modern.config.engines.storage import StorageEngine
from whoosh_modern.config.engines.vector import VectorEngine

__all__ = [
    "AnalyzerEngine",
    "APIEngine",
    "DataSourceEngine",
    "EmbeddingEngine",
    "FacetEngine",
    "LanguageEngine",
    "PluginEngine",
    "SchemaEngine",
    "SearchModelEngine",
    "StorageEngine",
    "VectorEngine",
]
