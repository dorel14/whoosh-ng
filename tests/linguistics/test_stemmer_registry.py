"""Tests for EPIC 6.7 Sprint LNG-4: StemmerRegistry."""

from __future__ import annotations

import pytest

from whoosh_modern.linguistics.registry import (
    LanguageProfile,
    LanguageRegistry,
    StemmerRegistry,
    get_default_registry,
)


class TestLanguageRegistry:
    """Tests for LanguageRegistry."""

    def test_default_registry_has_languages(self) -> None:
        registry = get_default_registry()
        assert "en" in registry.supported_languages
        assert "fr" in registry.supported_languages

    def test_resolve_returns_profile(self) -> None:
        registry = get_default_registry()
        profile = registry.resolve("fr")
        assert profile is not None
        assert profile.language == "fr"

    def test_resolve_none_returns_default(self) -> None:
        registry = get_default_registry()
        profile = registry.resolve(None)
        assert profile is not None
        assert profile.language == "en"

    def test_register_new_profile(self) -> None:
        registry = LanguageRegistry()
        profile = LanguageProfile(language="de", analyzer=None, stemmer=None)
        registry.register(profile)
        assert "de" in registry.supported_languages

    def test_set_default(self) -> None:
        registry = get_default_registry()
        registry.set_default("fr")
        assert registry.resolve(None).language == "fr"


class TestStemmerRegistry:
    """Tests for StemmerRegistry."""

    def test_list_stemmers(self) -> None:
        registry = get_default_registry()
        stemmers = StemmerRegistry(registry._profiles.values()).list_stemmers()
        assert isinstance(stemmers, list)

    def test_get_stemmer_returns_callable(self) -> None:
        registry = get_default_registry()
        stem_registry = StemmerRegistry(registry._profiles.values())
        stemmer = stem_registry.get_stemmer("fr")
        assert callable(stemmer)

    def test_get_stemmer_unknown_raises(self) -> None:
        registry = StemmerRegistry()
        with pytest.raises(KeyError):
            registry.get_stemmer("xx")
