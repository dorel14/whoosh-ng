"""Engine for building a ``PluginManager`` from plugin configuration.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any

from whoosh.plugins.manager import PluginManager
from whoosh_modern.config.models import WhooshNGConfig


class PluginEngine:
    """Build a ``PluginManager`` from configured plugins.

    Attributes:
        _config: The merged application configuration.
    """

    def __init__(self, config: WhooshNGConfig) -> None:
        """Initialize the engine with a merged configuration.

        Args:
            config: Merged Whoosh-NG configuration.
        """
        self._config = config

    def build(self) -> Any:
        """Build a PluginManager from the configured plugins.

        Returns:
            A PluginManager instance, or ``None`` if the plugin system is not available.
        """
        try:
            return PluginManager()
        except ImportError:
            return None
