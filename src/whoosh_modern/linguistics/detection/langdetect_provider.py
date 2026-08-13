"""Optional langdetect-based language detector.

Requires the optional ``langdetect`` package::

    pip install whoosh-ng[language-detection]

Author: dorel14
Version: 1.0.0
"""

from __future__ import annotations

import logging
from typing import Any

from whoosh_modern.linguistics.detection.protocol import LanguageDetector

logger = logging.getLogger(__name__)


class LangDetectProvider(LanguageDetector):
    """Language detector wrapping the optional ``langdetect`` library.

    Args:
        **kwargs: Optional keyword arguments forwarded to
            ``langdetect.detect_langs`` (e.g. ``seed``).
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the detector.

        Args:
            **kwargs: Optional keyword arguments forwarded to
                ``langdetect.detect_langs``.

        Raises:
            ImportError: If ``langdetect`` is not installed.
        """
        try:
            import langdetect  # type: ignore[import-not-found]
        except ImportError as exc:
            raise ImportError(
                "langdetect is required for LangDetectProvider. "
                "Install it with: pip install whoosh-ng[language-detection]"
            ) from exc
        self._kwargs = kwargs

    def detect(self, text: str) -> str:
        """Detect the language of the given text.

        Args:
            text: The text to analyze.

        Returns:
            An ISO 639-1 language code (e.g. ``"fr"``).
        """
        import langdetect  # pyright: ignore[reportMissingImports]

        langs = langdetect.detect_langs(text)
        if not langs:
            return ""
        return str(langs[0].lang)
