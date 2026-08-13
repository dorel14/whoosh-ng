"""Stemmer performance profiler.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass
class StemmerProfilerReport:
    """Stemmer profiling report.

    Attributes:
        original_tokens: Number of original tokens.
        stemmed_tokens: Number of unique stemmed tokens.
        reduction_ratio: Ratio of stemmed to original tokens.
        estimated_size_reduction: Estimated index size reduction percentage.
        avg_stem_time_ms: Average stemming time per token in milliseconds.
    """

    original_tokens: int = 0
    stemmed_tokens: int = 0
    reduction_ratio: float = 0.0
    estimated_size_reduction: float = 0.0
    avg_stem_time_ms: float = 0.0


class StemmerProfiler:
    """Profiles stemming impact on vocabulary and performance.

    Args:
        stemmer: Optional stemmer function to profile.
    """

    def __init__(self, stemmer: Any = None) -> None:
        """Initialize the stemmer profiler.

        Args:
            stemmer: Optional stemmer function to profile. If ``None``,
                :meth:`profile` returns an empty report.
        """
        self._stemmer = stemmer

    def profile(self, documents: list[str]) -> StemmerProfilerReport:
        """Profile stemming for a corpus.

        Args:
            documents: List of document texts to profile.

        Returns:
            A :class:`StemmerProfilerReport` with profiling metrics.
        """
        if not documents or self._stemmer is None:
            return StemmerProfilerReport()

        start = time.perf_counter()
        original_tokens = 0
        stemmed_tokens = 0
        for text in documents:
            for token in text.split():
                original_tokens += 1
                stemmed = self._stemmer(token)
                stemmed_tokens += len(set(stemmed)) if isinstance(stemmed, list) else 1
        elapsed = time.perf_counter() - start

        report = StemmerProfilerReport(
            original_tokens=original_tokens,
            stemmed_tokens=stemmed_tokens,
            reduction_ratio=stemmed_tokens / original_tokens if original_tokens else 0.0,
            estimated_size_reduction=max(0.0, 1.0 - stemmed_tokens / original_tokens) * 100
            if original_tokens
            else 0.0,
            avg_stem_time_ms=(elapsed / original_tokens * 1000) if original_tokens else 0.0,
        )
        return report


__all__ = ["StemmerProfiler", "StemmerProfilerReport"]
