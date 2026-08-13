"""Tests for EPIC 6.7 Sprint LNG-5: ExplainAnalyzer + CachedStemmingAnalyzer."""

from __future__ import annotations

import pytest

from whoosh_modern.linguistics.explain import AnalysisExplanation, ExplainAnalyzer, TokenExplanation
from whoosh_modern.analysis.cached_stemming_analyzer import CachedStemmingAnalyzer


class TestExplainAnalyzer:
    """Tests for ExplainAnalyzer."""

    def test_explain_returns_explanation(self) -> None:
        analyzer = ExplainAnalyzer()
        result = analyzer.explain("hello world")
        assert isinstance(result, AnalysisExplanation)

    def test_explain_text_preserved(self) -> None:
        analyzer = ExplainAnalyzer()
        result = analyzer.explain("hello world")
        assert result.text == "hello world"

    def test_explain_with_underlying_analyzer(self) -> None:
        from whoosh.analysis.analyzers import StandardAnalyzer

        analyzer = ExplainAnalyzer(StandardAnalyzer())
        result = analyzer.explain("hello world")
        assert isinstance(result.tokens, list)


class TestCachedStemmingAnalyzer:
    """Tests for CachedStemmingAnalyzer."""

    def test_no_analyzer_returns_empty(self) -> None:
        cached = CachedStemmingAnalyzer()
        result = cached("hello")
        assert result == []

    def test_caches_results(self) -> None:
        from whoosh.analysis.analyzers import StandardAnalyzer

        cached = CachedStemmingAnalyzer(StandardAnalyzer(), cache_size=100)
        cached("hello world")
        cached("hello world")
        assert len(cached._stem_cache) > 0
