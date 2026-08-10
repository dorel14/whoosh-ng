"""Tests for language-specific analyzers."""

from __future__ import annotations

import pytest

from whoosh.analysis.analyzers import CompositeAnalyzer
from whoosh_modern.analysis.stemming_analyzer import stemming_analyzer
from whoosh_modern.linguistics.stemmers import (
    EnglishAnalyzer,
    FrenchAnalyzer,
    GermanAnalyzer,
    ItalianAnalyzer,
    SpanishAnalyzer,
)


class TestLanguageAnalyzers:
    @pytest.mark.parametrize(
        ("analyzer", "language"),
        [
            (FrenchAnalyzer, "fr"),
            (EnglishAnalyzer, "en"),
            (GermanAnalyzer, "de"),
            (SpanishAnalyzer, "es"),
            (ItalianAnalyzer, "it"),
        ],
    )
    def test_analyzer_returns_tokens(self, analyzer, language):
        assert isinstance(analyzer, CompositeAnalyzer)
        tokens = [t.text for t in analyzer("maison et ordinateur")]
        assert len(tokens) > 0

    def test_french_stems_in_french(self):
        # "maisons" -> "maison" requires the French stemmer, not English Porter.
        assert [t.text for t in FrenchAnalyzer("maisons")] == ["maison"]

    def test_english_stems(self):
        assert [t.text for t in EnglishAnalyzer("running")] == ["run"]

    def test_german_stems(self):
        tokens = [t.text for t in GermanAnalyzer("häuser")]
        assert tokens == ["haus"]

    def test_spanish_stems(self):
        assert [t.text for t in SpanishAnalyzer("jugando")] == ["jug"]

    def test_italian_stems(self):
        tokens = [t.text for t in ItalianAnalyzer("amano")]
        assert len(tokens) == 1

    def test_languages_differ(self):
        # Same input must not be stemmed identically across languages.
        word = "continuando"
        assert [t.text for t in SpanishAnalyzer(word)] != [t.text for t in EnglishAnalyzer(word)]


class TestStemmingAnalyzerLanguageFix:
    def test_stemming_analyzer_with_language(self):
        analyzer = stemming_analyzer(stemmer="internal", language="french")
        assert [t.text for t in analyzer("maisons")] == ["maison"]

    def test_stemming_analyzer_default_language(self):
        analyzer = stemming_analyzer(stemmer="auto")
        tokens = list(analyzer("running"))
        assert isinstance(tokens, list)

    def test_stemming_analyzer_internal_french(self):
        analyzer = stemming_analyzer(stemmer="internal", language="french")
        tokens = list(analyzer("ordinateur"))
        assert isinstance(tokens, list)
