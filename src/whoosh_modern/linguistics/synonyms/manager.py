"""Synonym manager for CRUD operations and import/export."""

from __future__ import annotations

import json
import logging
from typing import Any

from whoosh_modern.linguistics.synonyms.provider import StaticSynonymProvider
from whoosh_modern.linguistics.synonyms.yaml_provider import YAMLSynonymProvider

logger = logging.getLogger(__name__)


class SynonymManager:
    """Manage synonyms with CRUD operations and import/export.

    :param mapping: optional initial synonym mapping
    """

    def __init__(self, mapping: dict[str, list[str]] | None = None) -> None:
        self._provider = StaticSynonymProvider(mapping)

    def get_synonyms(self, word: str) -> list[str]:
        """Return synonyms for a word."""
        return self._provider.get_synonyms(word)

    def add_synonyms(self, word: str, synonyms: list[str]) -> None:
        """Add synonyms for a word."""
        self._provider.add_synonym(word, synonyms)

    def remove_synonym(self, word: str, synonym: str) -> None:
        """Remove a synonym for a word."""
        self._provider.remove_synonym(word, synonym)

    def import_yaml(self, path: str) -> None:
        """Import synonyms from a YAML file."""
        provider = YAMLSynonymProvider(path)
        self._merge(provider)

    def import_json(self, path: str) -> None:
        """Import synonyms from a JSON file."""
        from whoosh_modern.linguistics.synonyms.json_provider import JSONSynonymProvider

        provider = JSONSynonymProvider(path)
        self._merge(provider)

    def export_json(self, path: str) -> None:
        """Export synonyms to a JSON file."""
        data = self._provider.to_dict()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _merge(self, provider: Any) -> None:
        if hasattr(provider, "to_dict"):
            self._provider.update_from_dict(provider.to_dict())
        elif hasattr(provider, "_mapping"):
            for word, syns in provider._mapping.items():
                self._provider.add_synonym(word, list(syns))
