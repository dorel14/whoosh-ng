"""Language detection protocol.

Author: dorel14
Version: 1.0.0
"""

from __future__ import annotations

from typing import Protocol


class LanguageDetector(Protocol):
    """Protocol for language detection implementations.

    Detectors take a text string and return an ISO 639-1 language code
    (e.g. ``"fr"``, ``"en"``).
    """

    def detect(self, text: str) -> str:
        """Detect the language of the given text.

        Args:
            text: The text to analyze.

        Returns:
            An ISO 639-1 language code (e.g. ``"fr"``).
        """
        ...
