"""Tests for StemmerProfiler."""

from __future__ import annotations

from whoosh_modern.profiling.stemmer_profiler import StemmerProfiler, StemmerProfilerReport


class TestStemmerProfiler:
    """Tests for StemmerProfiler."""

    def test_no_stemmer_returns_empty_report(self) -> None:
        profiler = StemmerProfiler()
        report = profiler.profile([])
        assert isinstance(report, StemmerProfilerReport)

    def test_empty_documents_returns_empty_report(self) -> None:
        def stemmer(word: str) -> list[str]:
            return [word]

        profiler = StemmerProfiler(stemmer=stemmer)
        report = profiler.profile([])
        assert report.original_tokens == 0

    def test_profile_returns_report(self) -> None:
        def stemmer(word: str) -> list[str]:
            return [word]

        profiler = StemmerProfiler(stemmer=stemmer)
        report = profiler.profile(["hello world"])
        assert isinstance(report, StemmerProfilerReport)
        assert report.original_tokens > 0

    def test_expanding_stemmer_keeps_ratio_bounded(self) -> None:
        # A stemmer that returns multiple forms (expansion) for a single token
        # must not push reduction_ratio above 1.0.
        def expanding_stemmer(word: str) -> list[str]:
            return [word, word + "_variant"]

        profiler = StemmerProfiler(stemmer=expanding_stemmer)
        report = profiler.profile(["hello world"])
        assert report.stemmed_tokens > report.original_tokens
        assert 0.0 <= report.reduction_ratio <= 1.0
        assert report.reduction_ratio == 1.0
        assert report.estimated_size_reduction == 0.0
