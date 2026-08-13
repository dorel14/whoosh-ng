"""Explain analyzer for Search Studio.

Exposes the tokenization/stemming pipeline for debugging and visualization.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TokenExplanation:
    """Explanation of a single token transformation.

    Attributes:
        original: Original token text.
        step: Pipeline step name (e.g. ``"lowercase"``, ``"stem"``).
        result: Resulting token text after the step.
    """

    original: str = ""
    step: str = ""
    result: str = ""


@dataclass
class AnalysisExplanation:
    """Full analysis explanation for a text.

    Attributes:
        text: Original text analyzed.
        tokens: Final token list.
        explanations: Step-by-step explanations.
    """

    text: str = ""
    tokens: list[str] = field(default_factory=list)
    explanations: list[TokenExplanation] = field(default_factory=list)


class ExplainAnalyzer:
    """Analyzer that exposes the tokenization/stemming pipeline.

    Wraps an underlying analyzer and records each transformation step
    for Search Studio visualization.

    Args:
        analyzer: The analyzer to wrap.
    """

    def __init__(self, analyzer: Any = None) -> None:
        """Initialize the explain analyzer.

        Args:
            analyzer: The underlying analyzer to wrap. If ``None``, text is
                split on whitespace without tokenization or stemming.
        """
        self._analyzer = analyzer

    def explain(self, text: str) -> AnalysisExplanation:
        """Analyze text and return a full explanation.

        Args:
            text: The text to analyze.

        Returns:
            An :class:`AnalysisExplanation` with token details.
        """
        explanation = AnalysisExplanation(text=text)
        if self._analyzer is None:
            explanation.tokens = text.split()
            return explanation
        tokens = list(self._analyzer(text))
        explanation.tokens = [t.text for t in tokens]
        return explanation


__all__ = ["ExplainAnalyzer", "AnalysisExplanation", "TokenExplanation"]
