"""Stopword-based language detector.

Detects language by counting stopwords from known language lists. The
language with the highest stopword hit count is returned.

Author: dorel14
Version: 1.0.0
"""

from __future__ import annotations

import logging

from whoosh_modern.linguistics.detection.protocol import LanguageDetector

logger = logging.getLogger(__name__)

_STOPWORD_MAP: dict[str, frozenset[str]] = {}


def _get_stopwords(lang: str) -> frozenset[str]:
    """Return the stopword set for a language code.

    Args:
        lang: Two-letter ISO 639-1 language code.

    Returns:
        A frozenset of stopwords for the language, or an empty frozenset
        if the language is not available.
    """
    if lang in _STOPWORD_MAP:
        return _STOPWORD_MAP[lang]
    try:
        from whoosh.lang import stopwords_for_language

        words = stopwords_for_language(lang)
        stopset = frozenset(words) if words else frozenset()
    except Exception:
        stopset = frozenset()
    _STOPWORD_MAP[lang] = stopset
    return stopset


class StopwordDetector(LanguageDetector):
    """Detect language by counting stopword matches.

    The detector tokenizes the input text on whitespace and counts how
    many tokens appear in each language's stopword list. The language
    with the highest hit count is returned. Ties are broken by the
    first language in ``supported_languages`` order.

    Args:
        supported_languages: Ordered list of language codes to consider.
    """

    def __init__(self, supported_languages: list[str] | None = None) -> None:
        """Initialize the detector.

        Args:
            supported_languages: Ordered list of language codes to consider.
                Defaults to ``["fr", "en", "de", "es", "it"]``.
        """
        self._supported_languages = supported_languages or ["fr", "en", "de", "es", "it"]
        self._stopword_sets: dict[str, frozenset[str]] = {}

    def detect(self, text: str) -> str:
        """Detect the language of the given text.

        Args:
            text: The text to analyze.

        Returns:
            The detected ISO 639-1 language code, or an empty string if
            detection fails.
        """
        tokens = [t.lower() for t in text.split() if t]
        if not tokens:
            return ""

        best_lang = ""
        best_count = -1
        for lang in self._supported_languages:
            stopset = _get_stopwords(lang)
            count = sum(1 for t in tokens if t in stopset)
            if count > best_count:
                best_count = count
                best_lang = lang

        return best_lang
