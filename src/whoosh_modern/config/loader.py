"""Configuration file loaders for YAML and JSON.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from whoosh_modern.config.models import WhooshNGConfig

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML configuration file.

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed configuration as a dictionary.

    Raises:
        ImportError: If ``PyYAML`` is not installed.
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not valid YAML.
    """
    if not HAS_YAML:
        raise ImportError("PyYAML is required to load YAML configuration files")
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        try:
            data = yaml.safe_load(fh)
        except Exception as exc:
            raise ValueError(f"Invalid YAML in {path}: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"Configuration file must contain a mapping at the top level: {path}")
    return data


def load_json(path: str | Path) -> dict[str, Any]:
    """Load a JSON configuration file.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed configuration as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not valid JSON.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except Exception as exc:
            raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Configuration file must contain a mapping at the top level: {path}")
    return data


def load_config(path: str | Path) -> WhooshNGConfig:
    """Load a Whoosh-NG configuration file and return a validated model.

    Supports YAML (``.yml`` / ``.yaml``) and JSON (``.json``) files.

    Args:
        path: Path to the configuration file.

    Returns:
        A validated :class:`WhooshNGConfig` instance.

    Raises:
        ValueError: If the file format is unsupported or the content is invalid.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in (".yml", ".yaml"):
        raw = load_yaml(path)
    elif suffix == ".json":
        raw = load_json(path)
    else:
        raise ValueError(
            f"Unsupported configuration file format: {suffix!r}. "
            "Use .yml, .yaml, or .json."
        )
    return WhooshNGConfig(**raw)


__all__ = ["load_config", "load_json", "load_yaml"]
