"""JSON-based synonym provider."""

from __future__ import annotations

import json

from whoosh_modern.linguistics.synonyms.provider import StaticSynonymProvider


class JSONSynonymProvider(StaticSynonymProvider):
    """Synonym provider that loads from a JSON file.

    Expected JSON format::

        {
            "car": ["automobile", "vehicle"],
            "bike": ["bicycle", "motorcycle"]
        }
    """

    def __init__(self, path: str) -> None:
        self._path = path
        super().__init__()
        self._load()

    def _load(self) -> None:
        with open(self._path, encoding="utf-8") as f:
            data = json.load(f)
        for word, syns in data.items():
            self.add_synonym(str(word), [str(s) for s in syns])
