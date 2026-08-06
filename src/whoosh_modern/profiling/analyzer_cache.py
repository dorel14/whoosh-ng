"""Analyzer cache for Whoosh-NG.

Provides an LRU cache for analyzer results. Fields to cache can be
chosen manually or selected automatically from profiling data based
on repetition ratio.
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable
from typing import Any


class AnalyzerCache:
    """LRU cache for analyzer results.

    Caches tokenized/analyzed results for repeated field values
    to avoid redundant analysis work.

    Example::

        cache = AnalyzerCache(maxsize=50000)
        analyzer = StandardAnalyzer()

        # During indexing
        for doc in docs:
            for field_name, value in doc.items():
                cache_key = f"{field_name}:{value}"
                if cache_key in cache:
                    tokens = cache[cache_key]
                else:
                    tokens = list(analyzer(value))
                    cache[cache_key] = tokens
    """

    def __init__(self, maxsize: int = 50000) -> None:
        self._maxsize = maxsize
        self._cache: OrderedDict[str, list[Any]] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> list[Any] | None:
        """Get cached tokens for a field value."""
        if key in self._cache:
            self._hits += 1
            self._cache.move_to_end(key)
            return self._cache[key]
        self._misses += 1
        return None

    def put(self, key: str, tokens: list[Any]) -> None:
        """Store tokens in the cache."""
        if key in self._cache:
            self._cache.move_to_end(key)
            self._cache[key] = tokens
        else:
            self._cache[key] = tokens
            if len(self._cache) > self._maxsize:
                self._cache.popitem(last=False)

    def get_or_compute(self, key: str, compute_fn: Callable[[], list[Any]]) -> list[Any]:
        """Get cached tokens or compute and cache them."""
        cached = self.get(key)
        if cached is not None:
            return cached
        tokens = compute_fn()
        self.put(key, tokens)
        return tokens

    @property
    def hits(self) -> int:
        return self._hits

    @property
    def misses(self) -> int:
        return self._misses

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    @property
    def size(self) -> int:
        return len(self._cache)

    @property
    def maxsize(self) -> int:
        return self._maxsize

    def clear(self) -> None:
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def report(self) -> str:
        lines: list[str] = []
        lines.append("Analyzer Cache Report")
        lines.append("=" * 50)
        lines.append(f"  Size: {self.size}/{self._maxsize}")
        lines.append(f"  Hits: {self._hits}")
        lines.append(f"  Misses: {self._misses}")
        lines.append(f"  Hit rate: {self.hit_rate:.1%}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "size": self.size,
            "maxsize": self._maxsize,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self.hit_rate, 4),
        }

    @classmethod
    def from_profiling(
        cls,
        cache_analysis: dict[str, Any],
        min_repetition_ratio: float = 2.0,
        maxsize: int = 50000,
    ) -> AnalyzerCache:
        """Create an AnalyzerCache sized from profiling data.

        Uses the repetition ratio from cache analysis to estimate
        the optimal cache size.

        :param cache_analysis: output from CacheAnalyzer.to_dict()
        :param min_repetition_ratio: minimum ratio to consider caching
        :param maxsize: maximum cache size
        :returns: configured AnalyzerCache instance
        """
        fields_data = cache_analysis.get("fields", {})
        _total_unique = cache_analysis.get("total_unique_values", 0)

        if not fields_data:
            return cls(maxsize=maxsize)

        estimated_size = 0
        for _field_name, stats in fields_data.items():
            ratio = stats.get("repetition_ratio", 1.0)
            if ratio >= min_repetition_ratio:
                unique = stats.get("unique", 0)
                estimated_size += unique

        suggested_size = min(estimated_size, maxsize)
        return cls(maxsize=suggested_size)


class FieldAnalyzerCache:
    """Field-specific analyzer cache with automatic key generation.

    Wraps an analyzer and caches results per field, automatically
    generating cache keys from field name and value.

    Example::

        field_cache = FieldAnalyzerCache(analyzer, fields=["Country", "City"])
        for doc in docs:
            for field in ["Country", "City"]:
                tokens = field_cache.analyze(field, doc[field])
    """

    def __init__(
        self,
        analyzer: Any,
        fields: list[str],
        cache_size: int = 50000,
    ) -> None:
        self._analyzer = analyzer
        self._fields = set(fields)
        self._cache = AnalyzerCache(maxsize=cache_size)

    def analyze(self, field_name: str, value: Any) -> list[Any]:
        """Analyze a field value, using cache if available.

        :param field_name: name of the field being analyzed
        :param value: field value to analyze
        :returns: list of tokens
        """
        if field_name not in self._fields:
            return list(self._analyzer(str(value)))

        cache_key = f"{field_name}:{value}"
        return self._cache.get_or_compute(
            cache_key,
            lambda: list(self._analyzer(str(value))),
        )

    def invalidate(self, field_name: str, value: Any) -> None:
        """Invalidate a specific cache entry.

        :param field_name: name of the field
        :param value: field value to invalidate
        """
        cache_key = f"{field_name}:{value}"
        self._cache._cache.pop(cache_key, None)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    @property
    def cache(self) -> AnalyzerCache:
        """Return the underlying cache."""
        return self._cache

    @property
    def hit_rate(self) -> float:
        """Return cache hit rate."""
        return self._cache.hit_rate

    def report(self) -> str:
        """Return a human-readable report."""
        lines: list[str] = []
        lines.append("Field Analyzer Cache Report")
        lines.append("=" * 50)
        lines.append(f"  Fields: {sorted(self._fields)}")
        lines.append(f"  Cache size: {self._cache.size}/{self._cache.maxsize}")
        lines.append(f"  Hit rate: {self._cache.hit_rate:.1%}")
        lines.append(f"  Hits: {self._cache.hits}")
        lines.append(f"  Misses: {self._cache.misses}")
        return "\n".join(lines)
