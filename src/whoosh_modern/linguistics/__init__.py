"""Whoosh-NG linguistic engine: synonyms, stemmers, language detection, and dictionary indexing.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from whoosh_modern.linguistics.detection import (
    LangDetectProvider,
    LanguageDetector,
    StopwordDetector,
)
from whoosh_modern.linguistics.registry import LanguageProfile, LanguageRegistry, get_default_registry
from whoosh_modern.linguistics.stemmers import (
    EnglishAnalyzer,
    FrenchAnalyzer,
    GermanAnalyzer,
    ItalianAnalyzer,
    SpanishAnalyzer,
)
from whoosh_modern.linguistics.synonyms import (
    LANG_SYNONYMS,
    JSONSynonymProvider,
    SQLiteSynonymStore,
    StaticSynonymProvider,
    SynonymCompiler,
    SynonymExpansionMiddleware,
    SynonymManager,
    SynonymProvider,
    YAMLSynonymProvider,
)
from whoosh_modern.linguistics.wiktionary_indexer import WiktionaryIndexer

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
    "WiktionaryIndexer",
    "LanguageDetector",
    "StopwordDetector",
    "LangDetectProvider",
    "LanguageRegistry",
    "LanguageProfile",
    "get_default_registry",
    "FrenchAnalyzer",
    "EnglishAnalyzer",
    "GermanAnalyzer",
    "SpanishAnalyzer",
    "ItalianAnalyzer",
]
