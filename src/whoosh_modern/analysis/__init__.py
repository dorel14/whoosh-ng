"""Whoosh-NG analysis extensions.

Provides:
- Stemmer provider plugin system
- Enhanced analyzers with plugin support
- Compatibility validation

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

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
]
