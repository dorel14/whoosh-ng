"""Analyzer presets for common search patterns.

Author: dorel14
Version: 3.1.0
"""

from __future__ import annotations

from typing import Any

from whoosh.analysis.analyzers import StandardAnalyzer
from whoosh.analysis.filters import LowercaseFilter
from whoosh.analysis.tokenizers import RegexTokenizer
from whoosh_modern.analysis.autocomplete_analyzer import AutoCompleteAnalyzer
from whoosh_modern.analysis.edge_ngram_analyzer import EdgeNgramAnalyzer


class AnalyzerPresets:
    """Preconfigured analyzers for common search scenarios.

    Each factory method returns a ready-to-use analyzer instance for a
    specific use case. Use :meth:`get` to retrieve a preset by name.

    Args:
        name: Preset name for :meth:`get` (``autocomplete``,
            ``partial_match``, ``fuzzy``, ``code_search``,
            ``documentation``, ``ecommerce``, ``blog``, ``multilingual``).

    Example:
        >>> from whoosh_modern.analysis.stemmer_presets import AnalyzerPresets
        >>> analyzer = AnalyzerPresets.get("autocomplete")
        >>> tokens = analyzer("hello world")
    """

    @staticmethod
    def autocomplete() -> AutoCompleteAnalyzer:
        """Analyzer optimized for autocomplete.

        Returns:
            An :class:`AutoCompleteAnalyzer` instance.
        """
        return AutoCompleteAnalyzer()

    @staticmethod
    def partial_match() -> EdgeNgramAnalyzer:
        """Analyzer optimized for partial matching.

        Returns:
            An :class:`EdgeNgramAnalyzer` instance.
        """
        return EdgeNgramAnalyzer()

    @staticmethod
    def fuzzy() -> Any:
        """Analyzer optimized for fuzzy search.

        Returns:
            A standard analyzer suitable for fuzzy queries.
        """
        return StandardAnalyzer()

    @staticmethod
    def code_search() -> Any:
        """Analyzer optimized for code search.

        Returns:
            A case-sensitive analyzer for code identifiers.
        """
        return RegexTokenizer(r"\w+")

    @staticmethod
    def documentation() -> Any:
        """Analyzer optimized for documentation search.

        Returns:
            An analyzer with stopwords and light stemming.
        """
        return StandardAnalyzer(stoplist=set())

    @staticmethod
    def ecommerce() -> Any:
        """Analyzer optimized for ecommerce search.

        Returns:
            An analyzer preserving case and special characters.
        """
        return RegexTokenizer(r"\w+")

    @staticmethod
    def blog() -> Any:
        """Analyzer optimized for blog search.

        Returns:
            A standard analyzer with stopwords.
        """
        return StandardAnalyzer()

    @staticmethod
    def multilingual() -> Any:
        """Analyzer optimized for multilingual content.

        Returns:
            A multilingual analyzer instance.
        """
        from whoosh_modern.linguistics.analyzers import MultiLanguageAnalyzer

        return MultiLanguageAnalyzer()

    @classmethod
    def get(cls, name: str) -> Any:
        """Return a preset analyzer by name.

        Args:
            name: Preset name.

        Returns:
            The requested analyzer instance.

        Raises:
            ValueError: If the preset name is unknown.
        """
        presets = {
            "autocomplete": cls.autocomplete,
            "partial_match": cls.partial_match,
            "fuzzy": cls.fuzzy,
            "code_search": cls.code_search,
            "documentation": cls.documentation,
            "ecommerce": cls.ecommerce,
            "blog": cls.blog,
            "multilingual": cls.multilingual,
        }
        factory = presets.get(name)
        if factory is None:
            raise ValueError(f"Unknown analyzer preset: {name!r}")
        return factory()


__all__ = ["AnalyzerPresets"]
