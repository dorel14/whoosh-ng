"""Engine for building a ``LanguageDetector`` from ``WhooshNGConfig.language_detection``.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any

from whoosh_modern.config.models import WhooshNGConfig


class LanguageEngine:
    """Build a ``LanguageDetector`` from ``WhooshNGConfig.language_detection``.

    Attributes:
        _config: The merged application configuration.
    """

    def __init__(self, config: WhooshNGConfig) -> None:
        """Initialize the engine with a merged configuration.

        Args:
            config: Merged Whoosh-NG configuration.
        """
        self._config = config

    def build(self) -> Any:
        """Build a LanguageDetector from the configured language detection settings.

        Returns:
            A LanguageDetector instance, or ``None`` if no language detection
            configuration is provided.
        """
        detection_config = self._config.language_detection
        if not detection_config:
            return None
        detector_type = detection_config.get("provider", "stopword").lower()
        if detector_type == "stopword":
            supported = detection_config.get("supported_languages", ["fr", "en", "de", "es", "it"])
            from whoosh_modern.linguistics.detection.stopword_detector import StopwordDetector

            return StopwordDetector(supported_languages=list(supported))
        if detector_type == "langdetect":
            try:
                from whoosh_modern.linguistics.detection.langdetect_provider import (
                    LangDetectProvider,
                )

                return LangDetectProvider()
            except ImportError as exc:
                raise ImportError(
                    "LangDetectProvider requires langdetect. "
                    "Install with: pip install whoosh-ng[language-detection]"
                ) from exc
        raise ValueError(f"Unsupported language detector: {detector_type}")
