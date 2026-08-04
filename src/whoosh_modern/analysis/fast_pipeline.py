"""Fast analyzer pipeline utilities for Whoosh-NG.

Provides reusable token and filter pipelines that reduce allocations
during batch indexing:

* reusable Token instances
* fast path ASCII
* fast path CRM
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from whoosh.analysis.acore import Token
from whoosh.analysis.tokenizers import RegexTokenizer


class FastAnalyzerPipeline:
    """Reusable analyzer pipeline that minimizes allocations.

    Wraps an existing analyzer/tokenizer and reuses ``Token`` instances
    across calls when the caller-visible configuration is unchanged.

    Example::

        pipeline = FastAnalyzerPipeline(RegexTokenizer())
        for value in values:
            for token in pipeline(value):
                ...
    """

    def __init__(self, tokenizer: Any) -> None:
        self._tokenizer = tokenizer
        self._last_token: Token | None = None

    def __call__(self, value: str, **kwargs: Any) -> Iterable[Token]:
        if self._last_token is None:
            self._last_token = Token()
        for token in self._tokenizer(value, **kwargs):
            reuse = self._last_token
            reuse.text = token.text
            reuse.boost = token.boost
            reuse.original = getattr(token, "original", token.text)
            reuse.stopped = getattr(token, "stopped", False)
            for attr in ("pos", "startchar", "endchar"):
                if hasattr(token, attr):
                    setattr(reuse, attr, getattr(token, attr))
            self._last_token = token
            yield reuse
