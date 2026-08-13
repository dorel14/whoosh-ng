"""Synonym manager for CRUD operations and import/export.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

import json
import logging
from typing import Any

from whoosh_modern.linguistics.synonyms.provider import StaticSynonymProvider
from whoosh_modern.linguistics.synonyms.yaml_provider import YAMLSynonymProvider

logger = logging.getLogger(__name__)


class SynonymManager:
    """Manage synonyms with CRUD operations and import/export.

    Args:
        mapping: optional initial synonym mapping
    """

    def __init__(self, mapping: dict[str, list[str]] | None = None) -> None:
        """Initialize the manager with an optional synonym mapping.

        Args:
            mapping: A dict mapping words to lists of synonym terms.
                Defaults to an empty mapping.
        """
        self._provider = StaticSynonymProvider(mapping)

    def get_synonyms(self, word: str) -> list[str]:
        """Return synonyms for a word.

        Args:
            word: The term whose synonyms should be retrieved.

        Returns:
            A list of synonymous terms for ``word``.
        """
        return self._provider.get_synonyms(word)

    def add_synonyms(self, word: str, synonyms: list[str]) -> None:
        """Add synonyms for a word.

        Args:
            word: The term to associate synonyms with.
            synonyms: The list of synonym terms to add.
        """
        self._provider.add_synonym(word, synonyms)

    def remove_synonym(self, word: str, synonym: str) -> None:
        """Remove a synonym for a word.

        Args:
            word: The term whose synonym should be removed.
            synonym: The synonym term to remove.
        """
        self._provider.remove_synonym(word, synonym)

    def import_yaml(self, path: str) -> None:
        """Import synonyms from a YAML file.

        Args:
            path: Filesystem path to the YAML synonym file.
        """
        provider = YAMLSynonymProvider(path)
        self._merge(provider)

    def import_json(self, path: str) -> None:
        """Import synonyms from a JSON file.

        Args:
            path: Filesystem path to the JSON synonym file.
        """
        from whoosh_modern.linguistics.synonyms.json_provider import JSONSynonymProvider

        provider = JSONSynonymProvider(path)
        self._merge(provider)

    def import_wiktionary(self, path: str) -> None:
        """Import synonyms from a Wiktionary JSON Lines dictionary.

        Args:
            path: Filesystem path to the kaikki.org JSON Lines dictionary
                file for a given language (e.g.
                ``dictionaries/wiktionary/fr.json``).
        """
        from whoosh_modern.linguistics.synonyms.wiktionary_provider import (
            WiktionarySynonymProvider,
        )

        provider = WiktionarySynonymProvider(path)
        self._merge(provider)

    def import_wiktionary_index(
        self,
        index_path: str,
        language: str | None = None,
    ) -> None:
        """Import synonyms from a built Wiktionary index.

        Opens the Whoosh index at ``index_path`` and merges the stored
        ``synonyms`` field into this manager, optionally filtered by
        ``language``.

        Args:
            index_path: Filesystem path to the Whoosh index directory
                built by ``WiktionaryIndexer.build_index()``.
            language: Optional two-letter language code filter
                (e.g. ``"fr"``). If ``None``, all languages are imported.
        """
        from whoosh_modern.linguistics.wiktionary_indexer import WiktionaryIndexer

        indexer = WiktionaryIndexer(index_path)
        for doc in indexer.iter_documents(language=language):
            word = doc.get("word")
            synonyms = doc.get("synonyms") or []
            if not word:
                continue
            clean_synonyms = [str(s) for s in synonyms if str(s)]
            if clean_synonyms:
                self._provider.add_synonym(word, clean_synonyms)

    def export_json(self, path: str) -> None:
        """Export synonyms to a JSON file.

        Args:
            path: Filesystem path where the JSON file will be written.
        """
        data = self._provider.to_dict()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _merge(self, provider: Any) -> None:
        """Merge another provider's synonyms into this manager's provider.

        Args:
            provider: A synonym provider instance that either has a
                ``to_dict`` method or a ``_mapping`` attribute.
        """
        if hasattr(provider, "to_dict"):
            self._provider.update_from_dict(provider.to_dict())
        elif hasattr(provider, "_mapping"):
            for word, syns in provider._mapping.items():
                self._provider.add_synonym(word, list(syns))
