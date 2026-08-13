"""Language detection protocols and implementations.

Author: dorel14
Version: 1.0.0
"""

from __future__ import annotations

from whoosh_modern.linguistics.detection.langdetect_provider import LangDetectProvider
from whoosh_modern.linguistics.detection.protocol import LanguageDetector
from whoosh_modern.linguistics.detection.stopword_detector import StopwordDetector

__all__ = [
    "LanguageDetector",
    "StopwordDetector",
    "LangDetectProvider",
]
