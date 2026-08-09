"""Fast analyzer pipeline utilities for Whoosh-NG.

Provides reusable token and filter pipelines that reduce allocations
during batch indexing:

* reusable Token instances
* fast path ASCII
* fast path CRM

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from whoosh.analysis.acore import Token


class FastAnalyzerPipeline:
    """Reusable analyzer pipeline that minimizes allocations.

    Wraps an existing analyzer/tokenizer and reuses ``Token`` instances
    across calls when the caller-visible configuration is unchanged.

    Example::

        pipeline = FastAnalyzerPipeline(RegexTokenizer())
        for value in values:
            for token in pipeline(value):
                ...

    Attributes:
        _tokenizer: The underlying tokenizer callable.
        _last_token: The last ``Token`` instance, reused for the next call.
    """

    def __init__(self, tokenizer: Any) -> None:
        """Initialize the FastAnalyzerPipeline.

        Args:
            tokenizer: A Whoosh tokenizer or analyzer callable.
        """
        self._tokenizer = tokenizer
        self._last_token: Token | None = None

    def __call__(self, value: str, **kwargs: Any) -> Iterable[Token]:
        """Tokenize a value, reusing Token instances to reduce allocations.

        Args:
            value: The string to tokenize.
            **kwargs: Additional keyword arguments forwarded to the tokenizer.

        Yields:
            ``Token`` instances with text, boost, and position attributes
            copied from the source tokens.
        """
        last_token = self._last_token
        if last_token is None:
            last_token = Token()
            self._last_token = last_token
        for token in self._tokenizer(value, **kwargs):
            reuse: Token = last_token
            reuse.text = token.text
            reuse.boost = token.boost
            reuse.original = getattr(token, "original", token.text)
            reuse.stopped = getattr(token, "stopped", False)
            for attr in ("pos", "startchar", "endchar"):
                if hasattr(token, attr):
                    setattr(reuse, attr, getattr(token, attr))
            self._last_token = token
            yield reuse
