"""Whoosh-NG synonym engine.

Provides:
- SynonymProvider protocol
- StaticSynonymProvider (in-memory)
- YAMLSynonymProvider (YAML file)
- JSONSynonymProvider (JSON file)
- SQLiteSynonymStore (persistent SQLite-backed)
- SynonymCompiler (precompile raw synonym data)
- SynonymManager (CRUD + import/export)
- SynonymExpansionMiddleware (hook into search/index pipeline)
- LANG_SYNONYMS (prebuilt FR/EN/DE/ES/IT dictionaries)

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from whoosh_modern.linguistics.synonyms.compiler import SynonymCompiler
from whoosh_modern.linguistics.synonyms.json_provider import JSONSynonymProvider
from whoosh_modern.linguistics.synonyms.languages import LANG_SYNONYMS
from whoosh_modern.linguistics.synonyms.manager import SynonymManager
from whoosh_modern.linguistics.synonyms.middleware import SynonymExpansionMiddleware
from whoosh_modern.linguistics.synonyms.provider import (
    StaticSynonymProvider,
    SynonymProvider,
)
from whoosh_modern.linguistics.synonyms.store import SQLiteSynonymStore
from whoosh_modern.linguistics.synonyms.yaml_provider import YAMLSynonymProvider

__all__ = [
    "SynonymProvider",
    "StaticSynonymProvider",
    "YAMLSynonymProvider",
    "JSONSynonymProvider",
    "SQLiteSynonymStore",
    "SynonymCompiler",
    "SynonymManager",
    "SynonymExpansionMiddleware",
    "LANG_SYNONYMS",
]
