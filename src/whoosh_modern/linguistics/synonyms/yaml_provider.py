"""YAML-based synonym provider."""

from __future__ import annotations

import logging

from whoosh_modern.linguistics.synonyms.provider import StaticSynonymProvider

logger = logging.getLogger(__name__)


class YAMLSynonymProvider(StaticSynonymProvider):
    """Synonym provider that loads from a YAML file.

    Expected YAML format::

        car:
          - automobile
          - vehicle
        bike:
          - bicycle
          - motorcycle
    """

    def __init__(self, path: str) -> None:
        self._path = path
        super().__init__()
        self._load()

    def _load(self) -> None:
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "PyYAML is required for YAMLSynonymProvider. "
                "Install it with: pip install whoosh-ng[yaml]"
            ) from exc
        with open(self._path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        for word, syns in data.items():
            self.add_synonym(str(word), [str(s) for s in syns])
