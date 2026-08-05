"""Stemmer compatibility tests.

Validates that different stemmer backends produce compatible results.
"""

from __future__ import annotations

import pytest

from whoosh_modern.analysis import (
    get_stemmer,
    validate_stemmer_compatibility,
    list_available_backends,
)


class TestStemmerCompatibility:
    """Test stemmer compatibility across backends."""

    @pytest.fixture
    def test_corpus(self):
        """Test corpus for stemmer validation."""
        return [
            "running",
            "runs",
            "runner",
            "studies",
            "studying",
            "connected",
            "connections",
            "testing",
            "tested",
            "tests",
            "organization",
            "organize",
            "organizing",
            "international",
            "internationally",
        ]

    def test_internal_stemmer_available(self):
        """Test that internal stemmer is always available."""
        backends = list_available_backends()
        assert "internal" in backends
        assert backends["internal"] == "available"

    def test_pystemmer_detection(self):
        """Test PyStemmer availability detection."""
        backends = list_available_backends()
        pystemmer_status = backends.get("pystemmer", "unknown")
        # Should be either "available" or "not installed"
        assert pystemmer_status in ["available", "not installed"]

    def test_get_stemmer_internal(self):
        """Test getting internal stemmer."""
        stemmer = get_stemmer("internal", "english")
        assert stemmer.name == "internal"
        assert stemmer.language == "english"

    def test_get_stemmer_auto(self):
        """Test auto-detection."""
        stemmer = get_stemmer("auto", "english")
        assert stemmer.name in ["internal", "pystemmer"]
        assert stemmer.language == "english"

    def test_stemmer_stems_words(self, test_corpus):
        """Test that stemmer produces stems."""
        stemmer = get_stemmer("internal", "english")
        for word in test_corpus:
            stemmed = stemmer.stem(word)
            assert isinstance(stemmed, str)
            assert len(stemmed) > 0

    def test_validate_stemmer_compatibility(self, test_corpus):
        """Test stemmer compatibility validation."""
        stemmer = get_stemmer("internal", "english")
        report = validate_stemmer_compatibility(stemmer, test_corpus)
        
        assert report["provider"] == "internal"
        assert report["language"] == "english"
        assert report["total_words"] == len(test_corpus)
        assert report["successful"] == len(test_corpus)
        assert report["failed"] == 0

    def test_compatibility_report_structure(self, test_corpus):
        """Test that compatibility report has expected structure."""
        stemmer = get_stemmer("internal", "english")
        report = validate_stemmer_compatibility(stemmer, test_corpus)
        
        assert "provider" in report
        assert "language" in report
        assert "total_words" in report
        assert "successful" in report
        assert "failed" in report
        assert "results" in report
        assert isinstance(report["results"], list)
        assert len(report["results"]) == len(test_corpus)
