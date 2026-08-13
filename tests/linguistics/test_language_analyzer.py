"""Tests for EPIC 6.7 Sprint LNG-3: MultiLanguageAnalyzer."""

from __future__ import annotations

import pytest

from whoosh_modern.linguistics.analyzers import MultiLanguageAnalyzer
from whoosh_modern.linguistics.stemmers import FrenchAnalyzer


class TestMultiLanguageAnalyzer:
    """Tests for MultiLanguageAnalyzer."""

    def test_default_languages(self) -> None:
        analyzer = MultiLanguageAnalyzer()
        assert analyzer is not None

    def test_custom_languages(self) -> None:
        analyzer = MultiLanguageAnalyzer(languages=["fr", "en"])
        assert analyzer is not None

    def test_callable(self) -> None:
        analyzer = MultiLanguageAnalyzer(languages=["fr"])
        tokens = analyzer("bonjour")
        assert isinstance(tokens, list)
