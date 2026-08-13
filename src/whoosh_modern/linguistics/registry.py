"""Language registry for multilingual indexing.

Provides ``LanguageRegistry``, ``StemmerRegistry``, and ``LanguageProfile``
to centralize analyzer, stemmer, synonym provider, and language detection
resolution.

Author: dorel14
Version: 3.1.0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from whoosh_modern.linguistics.detection.protocol import LanguageDetector
from whoosh_modern.linguistics.stemmers import (
    EnglishAnalyzer,
    FrenchAnalyzer,
    GermanAnalyzer,
    ItalianAnalyzer,
    SpanishAnalyzer,
)
from whoosh_modern.linguistics.synonyms.provider import SynonymProvider


@dataclass
class LanguageProfile:
    """Profile for a supported language.

    Attributes:
        language: ISO 639-1 language code (e.g. ``"fr"``).
        analyzer: Language-specific analyzer instance.
        stemmer: Language-specific stemmer function.
        synonym_provider: Optional synonym provider for the language.
        detector: Optional language detector instance.
    """

    language: str
    analyzer: Any
    stemmer: Any
    synonym_provider: SynonymProvider | None = None
    detector: LanguageDetector | None = None


class LanguageRegistry:
    """Registry of supported languages.

    Provides ``register()`` and ``resolve()`` to map language codes to
    ``LanguageProfile`` instances.

    Args:
        profiles: Optional initial list of ``LanguageProfile`` instances.
    """

    def __init__(self, profiles: list[LanguageProfile] | None = None) -> None:
        """Initialize the registry.

        Args:
            profiles: Optional initial list of language profiles.
        """
        self._profiles: dict[str, LanguageProfile] = {}
        self._default_language: str = "en"
        if profiles:
            for profile in profiles:
                self.register(profile)

    def register(self, profile: LanguageProfile) -> None:
        """Register a language profile.

        Args:
            profile: The ``LanguageProfile`` to register.
        """
        self._profiles[profile.language] = profile

    def resolve(self, language: str | None = None) -> LanguageProfile | None:
        """Resolve a language to its profile.

        Args:
            language: ISO 639-1 language code, or ``None`` for the default.

        Returns:
            The matching ``LanguageProfile``, or ``None`` if not found.
        """
        lang = language or self._default_language
        return self._profiles.get(lang)

    @property
    def supported_languages(self) -> list[str]:
        """Return the list of registered language codes."""
        return list(self._profiles.keys())

    def set_default(self, language: str) -> None:
        """Set the default language.

        Args:
            language: ISO 639-1 language code to use as default.

        Raises:
            KeyError: If the language is not registered.
        """
        if language not in self._profiles:
            raise KeyError(f"Language {language!r} is not registered")
        self._default_language = language


class StemmerRegistry(LanguageRegistry):
    """Registry of stemmers indexed by language code.

    Extends :class:`LanguageRegistry` with stemmer-specific helpers.
    """

    def list_stemmers(self) -> list[str]:
        """Return the list of registered stemmer codes.

        Returns:
            A list of language codes that have a registered stemmer.
        """
        return list(self._profiles.keys())

    def get_stemmer(self, language: str) -> Any:
        """Return the stemmer function for a language.

        Args:
            language: ISO 639-1 language code.

        Returns:
            The stemmer function/analyzer for the language.

        Raises:
            KeyError: If the language is not registered.
        """
        profile = self._profiles.get(language)
        if profile is None:
            raise KeyError(f"No stemmer registered for {language!r}")
        return profile.stemmer


def get_default_registry() -> LanguageRegistry:
    """Return a pre-populated registry for FR/EN/DE/ES/IT.

    Returns:
        A ``LanguageRegistry`` instance with profiles for French, English,
        German, Spanish, and Italian.
    """

    def _make_stemmer(analyzer: Any) -> Any:
        def _stem(text: str) -> list[str]:
            return [t.text for t in analyzer(text)]

        return _stem

    profiles = [
        LanguageProfile(
            language="fr",
            analyzer=FrenchAnalyzer,
            stemmer=_make_stemmer(FrenchAnalyzer),
        ),
        LanguageProfile(
            language="en",
            analyzer=EnglishAnalyzer,
            stemmer=_make_stemmer(EnglishAnalyzer),
        ),
        LanguageProfile(
            language="de",
            analyzer=GermanAnalyzer,
            stemmer=_make_stemmer(GermanAnalyzer),
        ),
        LanguageProfile(
            language="es",
            analyzer=SpanishAnalyzer,
            stemmer=_make_stemmer(SpanishAnalyzer),
        ),
        LanguageProfile(
            language="it",
            analyzer=ItalianAnalyzer,
            stemmer=_make_stemmer(ItalianAnalyzer),
        ),
    ]
    registry = LanguageRegistry(profiles)
    registry.set_default("en")
    return registry


__all__ = [
    "LanguageProfile",
    "LanguageRegistry",
    "StemmerRegistry",
    "get_default_registry",
]
