"""Whoosh-NG language-specific analyzers.

Provides ready-to-use analyzers for FR/EN/DE/ES/IT. These are thin aliases over
:func:`whoosh.analysis.analyzers.LanguageAnalyzer`, which already composes a
``RegexTokenizer``, ``LowercaseFilter``, a language-aware ``StopFilter`` and a
language-aware ``StemFilter`` (Snowball). Using the core analyzer fixes a bug in
the previous hand-rolled implementations, where non-English text was silently
stemmed with the English Porter algorithm.

Each name is an *instance* of the composed analyzer, ready to be passed to a
schema field or called directly::

    tokens = [t.text for t in FrenchAnalyzer("les maisons")]

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from whoosh.analysis.analyzers import CompositeAnalyzer, LanguageAnalyzer

FrenchAnalyzer: CompositeAnalyzer = LanguageAnalyzer("fr")
"""French analyzer (lowercase + French stopwords + French Snowball stemmer)."""

EnglishAnalyzer: CompositeAnalyzer = LanguageAnalyzer("en")
"""English analyzer (lowercase + English stopwords + English Snowball stemmer)."""

GermanAnalyzer: CompositeAnalyzer = LanguageAnalyzer("de")
"""German analyzer (lowercase + German stopwords + German Snowball stemmer)."""

SpanishAnalyzer: CompositeAnalyzer = LanguageAnalyzer("es")
"""Spanish analyzer (lowercase + Spanish stopwords + Spanish Snowball stemmer)."""

ItalianAnalyzer: CompositeAnalyzer = LanguageAnalyzer("it")
"""Italian analyzer (lowercase + Italian stopwords + Italian Snowball stemmer)."""

__all__ = [
    "FrenchAnalyzer",
    "EnglishAnalyzer",
    "GermanAnalyzer",
    "SpanishAnalyzer",
    "ItalianAnalyzer",
]
