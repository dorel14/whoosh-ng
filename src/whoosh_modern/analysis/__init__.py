"""Whoosh-NG analysis package: stemmers, n-grams, presets, and cached analyzers.

Author: dorel14
Version: 3.2.0
"""

from __future__ import annotations

from whoosh_modern.analysis.autocomplete_analyzer import AutoCompleteAnalyzer
from whoosh_modern.analysis.cached_stemming_analyzer import CachedStemmingAnalyzer
from whoosh_modern.analysis.edge_ngram_analyzer import EdgeNgramAnalyzer
from whoosh_modern.analysis.presets import AnalyzerPresets
from whoosh_modern.analysis.stemmer_providers import (
    IdentityStemmerProvider,
    InternalStemmerProvider,
    PyStemmerProvider,
    StemmerProvider,
    get_stemmer,
    list_available_backends,
    register_stemmer,
    validate_stemmer_compatibility,
)
from whoosh_modern.analysis.stemming_analyzer import StemmingAnalyzer

__all__ = [
    "StemmerProvider",
    "InternalStemmerProvider",
    "PyStemmerProvider",
    "IdentityStemmerProvider",
    "register_stemmer",
    "get_stemmer",
    "list_available_backends",
    "validate_stemmer_compatibility",
    "StemmingAnalyzer",
    "AutoCompleteAnalyzer",
    "EdgeNgramAnalyzer",
    "AnalyzerPresets",
    "CachedStemmingAnalyzer",
]
