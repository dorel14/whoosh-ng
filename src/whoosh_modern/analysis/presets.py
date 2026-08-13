"""Analyzer presets for common search patterns.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any

from whoosh.analysis.analyzers import StandardAnalyzer
from whoosh.analysis.filters import LowercaseFilter
from whoosh.analysis.tokenizers import RegexTokenizer
from whoosh_modern.analysis.autocomplete_analyzer import AutoCompleteAnalyzer
from whoosh_modern.analysis.edge_ngram_analyzer import EdgeNgramAnalyzer


class AnalyzerPresets:
    """Preconfigured analyzers for common search scenarios."""

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

    @classmethod
    def get(cls, name: str) -> Any:
        """Return a preset analyzer by name.

        Args:
            name: Preset name (``autocomplete``, ``partial_match``,
                ``fuzzy``, or ``code_search``).

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
        }
        factory = presets.get(name)
        if factory is None:
            raise ValueError(f"Unknown analyzer preset: {name!r}")
        return factory()


__all__ = ["AnalyzerPresets"]
