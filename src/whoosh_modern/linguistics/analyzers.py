"""Multi-language analyzer.

Author: dorel14
Version: 3.1.0
"""

from __future__ import annotations

from typing import Any

from whoosh_modern.linguistics.stemmers import (
    EnglishAnalyzer,
    FrenchAnalyzer,
    GermanAnalyzer,
    ItalianAnalyzer,
    SpanishAnalyzer,
)

_LANG_ALIASES: dict[str, Any] = {
    "fr": FrenchAnalyzer,
    "en": EnglishAnalyzer,
    "de": GermanAnalyzer,
    "es": SpanishAnalyzer,
    "it": ItalianAnalyzer,
}


class MultiLanguageAnalyzer:
    """Analyzer that applies multiple language analyzers.

    Args:
        languages: List of language codes to support.
    """

    def __init__(self, languages: list[str] | None = None) -> None:
        self._languages = languages or ["fr", "en", "de", "es", "it"]
        unsupported = [lang for lang in self._languages if lang not in _LANG_ALIASES]
        if unsupported:
            supported = ", ".join(sorted(_LANG_ALIASES))
            msg = f"Unsupported language(s): {unsupported}. Supported languages are: {supported}."
            raise ValueError(msg)
        self._analyzers = [_LANG_ALIASES[lang] for lang in self._languages]

    def __call__(self, text: str) -> Any:
        """Analyze text with all configured language analyzers.

        Args:
            text: Input text.

        Returns:
            Combined token stream from all analyzers.
        """
        tokens: list[Any] = []
        for analyzer in self._analyzers:
            tokens.extend(analyzer(text))
        return tokens


__all__ = ["MultiLanguageAnalyzer"]
