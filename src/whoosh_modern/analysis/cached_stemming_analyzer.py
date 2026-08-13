"""Cached stemming analyzer with LRU cache.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any


class CachedStemmingAnalyzer:
    """Analyzer wrapper with result cache.

    Caches analysis results per input text to avoid redundant processing
    of the same text by the underlying analyzer.

    Args:
        analyzer: The underlying analyzer to wrap.
        cache_size: Maximum number of cached analysis results.
    """

    def __init__(self, analyzer: Any = None, cache_size: int = 50000) -> None:
        self._analyzer = analyzer
        self._cache_size = cache_size
        self._cache: dict[str, list[str]] = {}

    def __call__(self, text: str) -> Any:
        """Analyze text with cached results.

        Args:
            text: Input text.

        Returns:
            List of analyzed token strings.
        """
        if self._analyzer is None:
            return []
        if text in self._cache:
            return self._cache[text]
        tokens = list(self._analyzer(text))
        result = [token.text for token in tokens]
        self._cache[text] = result
        if len(self._cache) > self._cache_size:
            self._cache.pop(next(iter(self._cache)))
        return result


__all__ = ["CachedStemmingAnalyzer"]
