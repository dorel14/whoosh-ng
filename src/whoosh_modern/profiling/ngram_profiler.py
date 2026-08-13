"""N-gram performance profiler.

Measures the impact of n-gram settings on index size and performance.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from whoosh.analysis.ngrams import NgramWordAnalyzer


@dataclass
class NgramProfilerReport:
    """N-gram profiling report.

    Attributes:
        ngrams_generated: Total number of n-grams generated.
        avg_per_term: Average number of n-grams per token.
        estimated_size_mb: Estimated index size in megabytes.
        postings_expansion_ratio: Ratio of postings to original documents.
        recommended_minsize: Recommended minimum n-gram size.
        recommended_maxsize: Recommended maximum n-gram size.
    """

    ngrams_generated: int = 0
    avg_per_term: float = 0.0
    estimated_size_mb: float = 0.0
    postings_expansion_ratio: float = 0.0
    recommended_minsize: int = 2
    recommended_maxsize: int = 10


class NgramProfiler:
    """Profiles n-gram generation impact.

    Args:
        analyzer: Optional analyzer to use for profiling.
    """

    def __init__(self, analyzer: Any = None) -> None:
        """Initialize the profiler.

        Args:
            analyzer: Optional analyzer to use for profiling. Defaults to
                ``NgramWordAnalyzer(3, at="start")``.
        """
        self._analyzer = analyzer or NgramWordAnalyzer(3, at="start")

    def profile(self, documents: list[str]) -> NgramProfilerReport:
        """Profile n-gram generation for a corpus.

        Args:
            documents: List of document texts to profile.

        Returns:
            A :class:`NgramProfilerReport` with profiling metrics.
        """
        start = time.perf_counter()
        total_ngrams = 0
        total_tokens = 0
        for text in documents:
            tokens = list(self._analyzer(text))
            total_tokens += len(tokens)
            total_ngrams += sum(1 for _ in tokens)
        elapsed = time.perf_counter() - start

        report = NgramProfilerReport(
            ngrams_generated=total_ngrams,
            avg_per_term=total_ngrams / total_tokens if total_tokens else 0.0,
            estimated_size_mb=total_ngrams * 0.001,
            postings_expansion_ratio=total_ngrams / len(documents) if documents else 0.0,
        )
        if total_tokens > 1000:
            report.recommended_minsize = 2
            report.recommended_maxsize = 8
        return report


__all__ = ["NgramProfiler", "NgramProfilerReport"]
