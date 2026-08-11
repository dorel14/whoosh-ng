"""JSON-based synonym provider.

Author: dorel14
Version: 3.0.0
"""

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

    Args:
        path: Filesystem path to the JSON synonym file.
    """

    def __init__(self, path: str) -> None:
        """Initialize the provider and load synonyms from a JSON file.

        Args:
            path: Filesystem path to the JSON synonym file.
        """
        self._path = path
        super().__init__()
        self._load()

    def _load(self) -> None:
        """Load and parse the JSON file, populating internal synonyms."""
        with open(self._path, encoding="utf-8") as f:
            data = json.load(f)
        for word, syns in data.items():
            self.add_synonym(str(word), [str(s) for s in syns])
