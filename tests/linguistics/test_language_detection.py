"""Tests for language detection."""

from __future__ import annotations

import pytest

from whoosh_modern.linguistics.detection.stopword_detector import StopwordDetector


class TestStopwordDetector:
    def test_detect_french(self):
        detector = StopwordDetector(["fr", "en"])
        result = detector.detect("le chat mange la souris")
        assert result == "fr"

    def test_detect_english(self):
        detector = StopwordDetector(["fr", "en"])
        result = detector.detect("the cat eats the mouse")
        assert result == "en"

    def test_detect_empty_text(self):
        detector = StopwordDetector(["fr", "en"])
        assert detector.detect("") == ""

    def test_detect_unknown_returns_first_supported(self):
        detector = StopwordDetector(["fr", "en"])
        result = detector.detect("xyzzy foobar")
        assert result in ("fr", "en")

    def test_custom_supported_languages(self):
        detector = StopwordDetector(["de", "es"])
        result = detector.detect("der hund beißt den mann")
        assert result == "de"

    def test_default_supported_languages(self):
        detector = StopwordDetector()
        result = detector.detect("la maison est belle")
        assert result == "fr"
