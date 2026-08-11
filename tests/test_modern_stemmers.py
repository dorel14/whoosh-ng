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


class TestLanguageAnalyzersBackwardCompatibility:
    """Ensure the historical class-style usage keeps working.

    Before being refactored into module-level ``LanguageAnalyzer`` instances,
    these names used to be classes, so existing code instantiates them before
    calling: ``FrenchAnalyzer()(text)``. This must keep working alongside the
    newer instance-style usage (``FrenchAnalyzer(text)``).
    """

    @pytest.mark.parametrize(
        "analyzer",
        [FrenchAnalyzer, EnglishAnalyzer, GermanAnalyzer, SpanishAnalyzer, ItalianAnalyzer],
    )
    def test_instantiation_style_call_returns_analyzer_instance(self, analyzer):
        # FrenchAnalyzer() must not raise TypeError and must return something
        # usable as an analyzer.
        instance = analyzer()
        assert isinstance(instance, CompositeAnalyzer)
        assert instance is not analyzer

    @pytest.mark.parametrize(
        "analyzer",
        [FrenchAnalyzer, EnglishAnalyzer, GermanAnalyzer, SpanishAnalyzer, ItalianAnalyzer],
    )
    def test_instantiation_style_call_then_call_with_text(self, analyzer):
        # Historical usage: FrenchAnalyzer()(text)
        tokens_via_instantiation = [t.text for t in analyzer()("maison et ordinateur")]
        # Modern usage: FrenchAnalyzer(text)
        tokens_direct = [t.text for t in analyzer("maison et ordinateur")]
        assert tokens_via_instantiation == tokens_direct
        assert len(tokens_direct) > 0

    def test_french_stems_via_instantiation_style(self):
        assert [t.text for t in FrenchAnalyzer()("maisons")] == ["maison"]


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
