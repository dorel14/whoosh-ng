"""Auto-complete analyzer for search-as-you-type.

Combines a ``RegexTokenizer``, ``LowercaseFilter``, and an edge n-gram
filter to produce prefixes suitable for autocomplete.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any

from whoosh.analysis.filters import LowercaseFilter, NgramFilter
from whoosh.analysis.tokenizers import RegexTokenizer, default_pattern


class AutoCompleteAnalyzer:
    """Analyzer producing edge n-grams for autocomplete.

    The analyzer lowercases tokens and generates edge n-grams with
    ``minsize=2`` and ``maxsize=10`` by default.

    Args:
        minsize: Minimum n-gram size.
        maxsize: Maximum n-gram size.
    """

    def __init__(self, minsize: int = 2, maxsize: int = 10) -> None:
        self._analyzer = (
            RegexTokenizer(default_pattern)
            | LowercaseFilter()
            | NgramFilter(minsize=minsize, maxsize=maxsize, at="start")
        )

    def __call__(self, text: str) -> Any:
        """Analyze text and return a stream of tokens.

        Args:
            text: Input text.

        Returns:
            Generator of analyzed tokens.
        """
        return self._analyzer(text)


__all__ = ["AutoCompleteAnalyzer"]
