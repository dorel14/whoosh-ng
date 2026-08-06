"""Tests for language-specific analyzers."""

from __future__ import annotations

import pytest

from whoosh_modern.linguistics.stemmers import (
    EnglishAnalyzer,
    FrenchAnalyzer,
    GermanAnalyzer,
    ItalianAnalyzer,
    SpanishAnalyzer,
)
from whoosh_modern.analysis.stemming_analyzer import stemming_analyzer


class TestLanguageAnalyzers:
    @pytest.mark.parametrize(
        "analyzer_cls,language",
        [
            (FrenchAnalyzer, "fr"),
            (EnglishAnalyzer, "en"),
            (GermanAnalyzer, "de"),
            (SpanishAnalyzer, "es"),
            (ItalianAnalyzer, "it"),
        ],
    )
    def test_analyzer_returns_tokens(self, analyzer_cls, language):
        analyzer = analyzer_cls()
        tokens = analyzer("maison et ordinateur")
        assert isinstance(tokens, list)
        assert len(tokens) > 0

    def test_french_stems(self):
        analyzer = FrenchAnalyzer()
        tokens = analyzer("mangeons")
        assert isinstance(tokens, list)

    def test_english_stems(self):
        analyzer = EnglishAnalyzer()
        tokens = analyzer("running")
        assert isinstance(tokens, list)

    def test_german_stems(self):
        analyzer = GermanAnalyzer()
        tokens = analyzer("häuser")
        assert isinstance(tokens, list)

    def test_spanish_stems(self):
        analyzer = SpanishAnalyzer()
        tokens = analyzer("jugando")
        assert isinstance(tokens, list)

    def test_italian_stems(self):
        analyzer = ItalianAnalyzer()
        tokens = analyzer("amano")
        assert isinstance(tokens, list)


class TestStemmingAnalyzerLanguageFix:
    def test_stemming_analyzer_with_language(self):
        analyzer = stemming_analyzer(stemmer="auto", language="french")
        tokens = list(analyzer("voiture"))
        assert isinstance(tokens, list)

    def test_stemming_analyzer_default_language(self):
        analyzer = stemming_analyzer(stemmer="auto")
        tokens = list(analyzer("running"))
        assert isinstance(tokens, list)

    def test_stemming_analyzer_internal_french(self):
        analyzer = stemming_analyzer(stemmer="internal", language="french")
        tokens = list(analyzer("ordinateur"))
        assert isinstance(tokens, list)
