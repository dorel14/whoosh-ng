"""Tests for multilingual indexing with auto language detection."""

from __future__ import annotations

from whoosh_modern.application import SearchApplication
from whoosh_modern.config.models import FieldConfig
from whoosh_modern.data_sources.json import JSONSource
from whoosh_modern.linguistics.detection.stopword_detector import StopwordDetector


class TestFieldConfigEffectiveLanguage:
    def test_auto_with_detector(self):
        detector = StopwordDetector(["fr", "en"])
        field = FieldConfig(type="le chat mange la souris", language="auto")
        result = field.effective_language(detector)
        assert result == "fr"

    def test_auto_without_detector(self):
        field = FieldConfig(type="hello world", language="auto")
        assert field.effective_language(None) is None

    def test_explicit_language_passthrough(self):
        field = FieldConfig(type="hello world", language="en")
        assert field.effective_language(StopwordDetector()) == "en"


class TestSearchApplicationMultilingual:
    def test_detect_language_french(self, tmp_path):
        source = JSONSource("src/whoosh_modern/linguistics/dictionaries/wiktionary/fr.json")
        detector = StopwordDetector(["fr", "en", "de", "es", "it"])
        app = SearchApplication(source=source, language_detector=detector)
        doc = {"word": "voiture", "definition": "un véhicule automobile"}
        assert app._detect_language(doc) == "fr"

    def test_detect_language_english(self, tmp_path):
        source = JSONSource("src/whoosh_modern/linguistics/dictionaries/wiktionary/en.json")
        detector = StopwordDetector(["fr", "en", "de", "es", "it"])
        app = SearchApplication(source=source, language_detector=detector)
        doc = {"word": "car", "definition": "a road vehicle"}
        assert app._detect_language(doc) == "en"

    def test_detect_language_empty_document(self, tmp_path):
        source = JSONSource("src/whoosh_modern/linguistics/dictionaries/wiktionary/fr.json")
        detector = StopwordDetector(["fr", "en"])
        app = SearchApplication(source=source, language_detector=detector)
        assert app._detect_language({}) is None

    def test_detect_language_no_detector(self, tmp_path):
        source = JSONSource("src/whoosh_modern/linguistics/dictionaries/wiktionary/fr.json")
        app = SearchApplication(source=source)
        assert app._detect_language({"word": "voiture"}) is None
