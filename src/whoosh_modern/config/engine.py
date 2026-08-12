"""Whoosh-NG configuration engine with hierarchical merging.

The :class:`ConfigEngine` loads configuration from YAML/JSON files and merges
them according to a precedence hierarchy:

1. Runtime overrides (highest priority)
2. Instance configuration
3. Application configuration
4. Language defaults
5. Built-in defaults (lowest priority)

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from whoosh_modern.config.engines import (
    AnalyzerEngine,
    DataSourceEngine,
    FacetEngine,
    SchemaEngine,
    StorageEngine,
)
from whoosh_modern.config.loader import load_json, load_yaml
from whoosh_modern.config.models import WhooshNGConfig


class ConfigEngine:
    """Whoosh-NG configuration engine.

    Loads, validates, and merges configuration from multiple sources.
    Configuration files are loaded with :meth:`load_config` and merged with
    :meth:`merge` so that higher-priority sources override lower-priority ones.

    Example:
        >>> engine = ConfigEngine()
        >>> engine.load("whoosh-ng.yml")
        >>> engine.load("whoosh-ng.local.yml", priority="instance")
        >>> app = engine.build()

    Attributes:
        _config: The current merged configuration.
        _layers: Ordered list of (name, config) pairs representing the
            configuration stack, from lowest to highest priority.
    """

    def __init__(self) -> None:
        """Initialize an empty configuration engine."""
        self._config: WhooshNGConfig = WhooshNGConfig()
        self._layers: list[tuple[str, dict[str, Any]]] = []
        self._app_cache: Any = None

    def load(self, path: str | Path, priority: str = "application") -> None:
        """Load a configuration file and merge it into the current config.

        Args:
            path: Path to a YAML or JSON configuration file.
            priority: Merge priority layer. Accepted values:
                ``"language"``, ``"application"``, ``"instance"``,
                ``"runtime"``. Higher priority layers override lower ones.

        Raises:
            ValueError: If ``priority`` is not one of the accepted values, or if
                the file format is unsupported or the content is invalid.
        """
        self._validate_priority(priority)
        path = Path(path)
        suffix = path.suffix.lower()
        if suffix in (".yml", ".yaml"):
            raw = load_yaml(path)
        elif suffix == ".json":
            raw = load_json(path)
        else:
            accepted_formats = [".yml", ".yaml", ".json"]
            raise ValueError(
                f"Unsupported configuration file format: {suffix!r}. "
                f"Accepted formats are: {', '.join(accepted_formats)}."
            )
        self._layers.append((priority, raw))
        self._rebuild()

    def merge(self, overrides: dict[str, Any], priority: str = "runtime") -> None:
        """Merge a dictionary of configuration overrides.

        Args:
            overrides: Configuration overrides as a dictionary.
            priority: Merge priority layer (see :meth:`load`).

        Raises:
            ValueError: If ``priority`` is not one of the accepted values.
        """
        self._validate_priority(priority)
        self._layers.append((priority, overrides))
        self._rebuild()

    def get_config(self) -> WhooshNGConfig:
        """Return the current merged configuration.

        Returns:
            A validated :class:`WhooshNGConfig` representing the merged
            configuration from all loaded sources.
        """
        return self._config

    def build(self) -> Any:
        """Build a complete Whoosh-NG application from the merged configuration.

        Orchestrates the specialized engines to construct a ready-to-use
        :class:`whoosh_modern.application.SearchApplication`.

        Returns:
            A configured :class:`whoosh_modern.application.SearchApplication`
            instance.

        Raises:
            ValueError: If the configuration cannot be resolved into a valid
                application (e.g. unsupported data source or storage type).
        """
        if self._app_cache is not None:
            return self._app_cache
        source = DataSourceEngine(self._config).build()
        storage = StorageEngine(self._config).build()
        from whoosh_modern.application import SearchApplication
        self._app_cache = SearchApplication(source=source, storage=storage)
        return self._app_cache

    def reset(self) -> None:
        """Reset the configuration engine to its default state."""
        self._config = WhooshNGConfig()
        self._layers.clear()
        self._app_cache = None

    @staticmethod
    def _validate_priority(priority: str) -> None:
        """Raise ``ValueError`` if ``priority`` is not an accepted layer name."""
        accepted_priorities = {"language", "application", "instance", "runtime"}
        if priority not in accepted_priorities:
            raise ValueError(
                f"Invalid priority: {priority!r}. Accepted values are: "
                f"{sorted(accepted_priorities)}"
            )

    def _rebuild(self) -> None:
        """Rebuild the merged configuration from all layers."""
        priority_order = {"language": 0, "application": 1, "instance": 2, "runtime": 3}
        sorted_layers = sorted(self._layers, key=lambda item: priority_order.get(item[0], 1))
        merged: dict[str, Any] = {}
        for _, layer in sorted_layers:
            self._deep_merge(merged, layer)
        self._config = WhooshNGConfig(**merged)
        self._app_cache = None

    @staticmethod
    def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> None:
        """Recursively merge ``override`` into ``base``.

        Nested dictionaries are merged recursively. Scalar values and lists are
        replaced entirely by the override values. **Important**: lists are NOT
        appended or combined; a higher-priority list will completely overwrite
        a lower-priority one. For example, merging `{"plugins": ["a"]}` with
        `{"plugins": ["b"]}` results in `{"plugins": ["b"]}`, not
        `{"plugins": ["a", "b"]}`. This design ensures explicit control over
        list contents across layers and avoids unpredictable merged states.
        If additive list merging is required, handle it at the application level
        before calling :meth:`merge` or implement a custom merge strategy.

        Args:
            base: Base dictionary to merge into.
            override: Override dictionary whose values take precedence.
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                ConfigEngine._deep_merge(base[key], value)
            else:
                base[key] = value


__all__ = ["ConfigEngine"]
