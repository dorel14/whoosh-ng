"""Whoosh-NG linguistic engine: synonyms, stemmers, and language-specific analyzers."""

from __future__ import annotations

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
    "FrenchAnalyzer",
    "EnglishAnalyzer",
    "GermanAnalyzer",
    "SpanishAnalyzer",
    "ItalianAnalyzer",
]
