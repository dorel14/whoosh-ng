"""Tests for StemmerProfiler."""

from __future__ import annotations

import pytest

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
