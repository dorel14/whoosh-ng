"""YAML-based synonym provider.

Author: dorel14
Version: 3.0.0
"""

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

    Args:
        path: Filesystem path to the YAML synonym file.
    """

    def __init__(self, path: str) -> None:
        """Initialize the provider and load synonyms from a YAML file.

        Args:
            path: Filesystem path to the YAML synonym file.

        Raises:
            ImportError: If PyYAML is not installed.
        """
        self._path = path
        super().__init__()
        self._load()

    def _load(self) -> None:
        """Load and parse the YAML file, populating internal synonyms.

        Raises:
            ImportError: If PyYAML is not installed.
        """
        try:
            import yaml
        except ImportError as exc:
            raise ImportError(
                "PyYAML is required for YAMLSynonymProvider. "
                "Install it with: pip install whoosh-ng[yaml]"
            ) from exc
        with open(self._path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        for word, syns in data.items():
            self.add_synonym(str(word), [str(s) for s in syns])
