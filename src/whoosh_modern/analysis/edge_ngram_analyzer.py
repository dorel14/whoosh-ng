"""Edge n-gram analyzer for prefix matching.

A thin explicit wrapper around the core n-gram infrastructure, focused on
prefix generation only.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any

from whoosh.analysis.filters import LowercaseFilter, NgramFilter
from whoosh.analysis.tokenizers import RegexTokenizer, default_pattern


class EdgeNgramAnalyzer:
    """Analyzer producing edge n-grams only.

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
        """Analyze text and return a stream of edge n-gram tokens.

        Args:
            text: Input text.

        Returns:
            Generator of analyzed tokens.
        """
        return self._analyzer(text)


__all__ = ["EdgeNgramAnalyzer"]
