"""Language registry for multilingual indexing.

Provides ``LanguageRegistry`` and ``LanguageProfile`` to centralize
analyzer, stemmer, synonym provider, and language detection resolution.

Author: dorel14
Version: 1.0.0
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


def get_default_registry() -> LanguageRegistry:
    """Return a pre-populated registry for FR/EN/DE/ES/IT.

    Returns:
        A ``LanguageRegistry`` instance with profiles for French, English,
        German, Spanish, and Italian.
    """
    profiles = [
        LanguageProfile(
            language="fr",
            analyzer=FrenchAnalyzer,
            stemmer=lambda text: [t.text for t in FrenchAnalyzer(text)],
            synonym_provider=None,
        ),
        LanguageProfile(
            language="en",
            analyzer=EnglishAnalyzer,
            stemmer=lambda text: [t.text for t in EnglishAnalyzer(text)],
            synonym_provider=None,
        ),
        LanguageProfile(
            language="de",
            analyzer=GermanAnalyzer,
            stemmer=lambda text: [t.text for t in GermanAnalyzer(text)],
            synonym_provider=None,
        ),
        LanguageProfile(
            language="es",
            analyzer=SpanishAnalyzer,
            stemmer=lambda text: [t.text for t in SpanishAnalyzer(text)],
            synonym_provider=None,
        ),
        LanguageProfile(
            language="it",
            analyzer=ItalianAnalyzer,
            stemmer=lambda text: [t.text for t in ItalianAnalyzer(text)],
            synonym_provider=None,
        ),
    ]
    registry = LanguageRegistry(profiles)
    registry.set_default("en")
    return registry
