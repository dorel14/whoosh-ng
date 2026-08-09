"""Whoosh-NG language-specific analyzers.

Provides ready-to-use analyzers for FR/EN/DE/ES/IT that combine:
- Snowball stemming (via whoosh.lang.snowball)
- Stopword removal (via whoosh.lang.stopwords)

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from contextlib import suppress
from typing import Any

from whoosh.analysis import StemmingAnalyzer as WhooshStemmingAnalyzer
from whoosh.lang import stopwords_for_language
from whoosh_modern.analysis.stemmer_providers import get_stemmer


def _build_analyzer(language: str) -> Any:
    """Build a Whoosh stemming analyzer for the given language.

    Args:
        language: The language code (e.g. ``"fr"``, ``"en"``) used to
            select the appropriate Snowball stemmer and stopword list.

    Returns:
        A configured ``StemmingAnalyzer`` instance for the specified language.
    """
    stemmer = get_stemmer("auto", language)
    stoplist: list[str] = []
    with suppress(Exception):
        stoplist = stopwords_for_language(language)
    return WhooshStemmingAnalyzer(stemfn=stemmer.stem, stoplist=stoplist)


class FrenchAnalyzer:
    """French language analyzer (Snowball stemmer + stopwords)."""

    def __init__(self) -> None:
        """Initialize the French analyzer with a Snowball stemmer and French stopwords."""
        self._analyzer = _build_analyzer("fr")

    def __call__(self, value: str, **kwargs: Any) -> list[Any]:
        """Tokenize and analyze the input text.

        Args:
            value: The input text string to analyze.
            **kwargs: Additional keyword arguments passed to the underlying
                analyzer.

        Returns:
            A list of analyzed tokens.
        """
        return list(self._analyzer(value, **kwargs))


class EnglishAnalyzer:
    """English language analyzer (Snowball stemmer + stopwords)."""

    def __init__(self) -> None:
        """Initialize the English analyzer with a Snowball stemmer and English stopwords."""
        self._analyzer = _build_analyzer("en")

    def __call__(self, value: str, **kwargs: Any) -> list[Any]:
        """Tokenize and analyze the input text.

        Args:
            value: The input text string to analyze.
            **kwargs: Additional keyword arguments passed to the underlying
                analyzer.

        Returns:
            A list of analyzed tokens.
        """
        return list(self._analyzer(value, **kwargs))


class GermanAnalyzer:
    """German language analyzer (Snowball stemmer + stopwords)."""

    def __init__(self) -> None:
        """Initialize the German analyzer with a Snowball stemmer and German stopwords."""
        self._analyzer = _build_analyzer("de")

    def __call__(self, value: str, **kwargs: Any) -> list[Any]:
        """Tokenize and analyze the input text.

        Args:
            value: The input text string to analyze.
            **kwargs: Additional keyword arguments passed to the underlying
                analyzer.

        Returns:
            A list of analyzed tokens.
        """
        return list(self._analyzer(value, **kwargs))


class SpanishAnalyzer:
    """Spanish language analyzer (Snowball stemmer + stopwords)."""

    def __init__(self) -> None:
        """Initialize the Spanish analyzer with a Snowball stemmer and Spanish stopwords."""
        self._analyzer = _build_analyzer("es")

    def __call__(self, value: str, **kwargs: Any) -> list[Any]:
        """Tokenize and analyze the input text.

        Args:
            value: The input text string to analyze.
            **kwargs: Additional keyword arguments passed to the underlying
                analyzer.

        Returns:
            A list of analyzed tokens.
        """
        return list(self._analyzer(value, **kwargs))


class ItalianAnalyzer:
    """Italian language analyzer (Snowball stemmer + stopwords)."""

    def __init__(self) -> None:
        """Initialize the Italian analyzer with a Snowball stemmer and Italian stopwords."""
        self._analyzer = _build_analyzer("it")

    def __call__(self, value: str, **kwargs: Any) -> list[Any]:
        """Tokenize and analyze the input text.

        Args:
            value: The input text string to analyze.
            **kwargs: Additional keyword arguments passed to the underlying
                analyzer.

        Returns:
            A list of analyzed tokens.
        """
        return list(self._analyzer(value, **kwargs))


__all__ = [
    "FrenchAnalyzer",
    "EnglishAnalyzer",
    "GermanAnalyzer",
    "SpanishAnalyzer",
    "ItalianAnalyzer",
]
