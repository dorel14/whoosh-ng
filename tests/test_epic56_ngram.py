"""Tests for EPIC 5.6 Sprint NGRAM-1."""

from __future__ import annotations

import pytest

from whoosh_modern.analysis.autocomplete_analyzer import AutoCompleteAnalyzer
from whoosh_modern.analysis.edge_ngram_analyzer import EdgeNgramAnalyzer
from whoosh_modern.analysis.presets import AnalyzerPresets
from whoosh_modern.fields.search_as_you_type import SEARCH_AS_YOU_TYPE
from whoosh_modern.profiling.ngram_profiler import NgramProfiler, NgramProfilerReport


class TestAutoCompleteAnalyzer:
    def test_generates_ngrams(self):
        analyzer = AutoCompleteAnalyzer(minsize=2, maxsize=4)
        tokens = [t.text for t in analyzer("ab")]
        assert tokens

    def test_preset_autocomplete(self):
        analyzer = AnalyzerPresets.autocomplete()
        assert callable(analyzer)

    def test_preset_partial_match(self):
        analyzer = AnalyzerPresets.partial_match()
        assert callable(analyzer)

    def test_preset_fuzzy(self):
        analyzer = AnalyzerPresets.fuzzy()
        assert analyzer is not None

    def test_preset_code_search(self):
        analyzer = AnalyzerPresets.code_search()
        assert analyzer is not None

    def test_preset_get_valid(self):
        analyzer = AnalyzerPresets.get("autocomplete")
        assert callable(analyzer)

    def test_preset_get_invalid(self):
        with pytest.raises(ValueError, match="Unknown analyzer preset"):
            AnalyzerPresets.get("unknown")


class TestEdgeNgramAnalyzer:
    def test_generates_edge_ngrams(self):
        analyzer = EdgeNgramAnalyzer(minsize=2, maxsize=3)
        tokens = [t.text for t in analyzer("abc")]
        assert "ab" in tokens
        assert "abc" in tokens


class TestSearchAsYouTypeField:
    def test_field_creation(self):
        field = SEARCH_AS_YOU_TYPE(stored=True)
        assert field is not None


class TestNgramProfiler:
    def test_profile_empty(self):
        profiler = NgramProfiler()
        report = profiler.profile([])
        assert isinstance(report, NgramProfilerReport)
        assert report.ngrams_generated == 0

    def test_profile_documents(self):
        profiler = NgramProfiler()
        report = profiler.profile(["hello world", "foo bar"])
        assert report.ngrams_generated > 0
        assert report.avg_per_term > 0
