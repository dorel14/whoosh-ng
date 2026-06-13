from __future__ import annotations

import math
from typing import Iterable, Sequence


class AutocompleteHit:
    def __init__(self, text: str, score: float) -> None:
        self.text = text
        self.score = score


class AutocompleteProvider:
    def add(self, phrases: Iterable[str]) -> None:
        raise NotImplementedError

    def search(self, prefix: str, limit: int = 10) -> list[AutocompleteHit]:
        raise NotImplementedError
