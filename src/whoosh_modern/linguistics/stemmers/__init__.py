"""Whoosh-NG language-specific analyzers.

Provides ready-to-use analyzers for FR/EN/DE/ES/IT that combine:
- Snowball stemming (via whoosh.lang.snowball)
- Stopword removal (via whoosh.lang.stopwords)
"""

from __future__ import annotations

from contextlib import suppress
from typing import Any

from whoosh.analysis import StemmingAnalyzer as WhooshStemmingAnalyzer
from whoosh.lang import stopwords_for_language
from whoosh_modern.analysis.stemmer_providers import get_stemmer


def _build_analyzer(language: str) -> Any:
    stemmer = get_stemmer("auto", language)
    stoplist: list[str] = []
    with suppress(Exception):
        stoplist = stopwords_for_language(language)
    return WhooshStemmingAnalyzer(stemfn=stemmer.stem, stoplist=stoplist)


class FrenchAnalyzer:
    """French language analyzer (Snowball stemmer + stopwords)."""

    def __init__(self) -> None:
        self._analyzer = _build_analyzer("fr")

    def __call__(self, value: str, **kwargs: Any) -> list[Any]:
        return list(self._analyzer(value, **kwargs))


class EnglishAnalyzer:
    """English language analyzer (Snowball stemmer + stopwords)."""

    def __init__(self) -> None:
        self._analyzer = _build_analyzer("en")

    def __call__(self, value: str, **kwargs: Any) -> list[Any]:
        return list(self._analyzer(value, **kwargs))


class GermanAnalyzer:
    """German language analyzer (Snowball stemmer + stopwords)."""

    def __init__(self) -> None:
        self._analyzer = _build_analyzer("de")

    def __call__(self, value: str, **kwargs: Any) -> list[Any]:
        return list(self._analyzer(value, **kwargs))


class SpanishAnalyzer:
    """Spanish language analyzer (Snowball stemmer + stopwords)."""

    def __init__(self) -> None:
        self._analyzer = _build_analyzer("es")

    def __call__(self, value: str, **kwargs: Any) -> list[Any]:
        return list(self._analyzer(value, **kwargs))


class ItalianAnalyzer:
    """Italian language analyzer (Snowball stemmer + stopwords)."""

    def __init__(self) -> None:
        self._analyzer = _build_analyzer("it")

    def __call__(self, value: str, **kwargs: Any) -> list[Any]:
        return list(self._analyzer(value, **kwargs))


__all__ = [
    "FrenchAnalyzer",
    "EnglishAnalyzer",
    "GermanAnalyzer",
    "SpanishAnalyzer",
    "ItalianAnalyzer",
]
