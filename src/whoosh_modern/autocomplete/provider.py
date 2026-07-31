from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

from whoosh.hooks import hookimpl
from whoosh.plugins.manager import Plugin


class AutocompleteHit:
    def __init__(self, text: str, score: float) -> None:
        self.text = text
        self.score = score


class AutocompleteProvider(Plugin):
    def add(self, phrases: Iterable[str]) -> None:
        raise NotImplementedError

    def search(self, prefix: str, limit: int = 10) -> list[AutocompleteHit]:
        raise NotImplementedError
