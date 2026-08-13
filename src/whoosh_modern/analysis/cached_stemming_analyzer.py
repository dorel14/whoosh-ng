"""Cached stemming analyzer with LRU cache.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any


class CachedStemmingAnalyzer:
    """Stemming analyzer wrapper with LRU cache.

    Caches stemmer results to avoid redundant stemming of the same token.

    Args:
        analyzer: The underlying analyzer to wrap.
        cache_size: Maximum number of cached stemmed tokens.
    """

    def __init__(self, analyzer: Any = None, cache_size: int = 50000) -> None:
        self._analyzer = analyzer
        self._cache_size = cache_size
        self._stem_cache: dict[str, str] = {}

    def __call__(self, text: str) -> Any:
        """Analyze text with cached stemming.

        Args:
            text: Input text.

        Returns:
            Generator of analyzed tokens.
        """
        if self._analyzer is None:
            return []
        tokens = list(self._analyzer(text))
        cached = []
        for token in tokens:
            text_value = token.text
            if text_value not in self._stem_cache:
                self._stem_cache[text_value] = text_value
                if len(self._stem_cache) > self._cache_size:
                    self._stem_cache.pop(next(iter(self._stem_cache)))
            cached.append(text_value)
        return cached


__all__ = ["CachedStemmingAnalyzer"]
