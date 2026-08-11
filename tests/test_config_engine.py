"""Tests for the Whoosh-NG configuration engine.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path
from typing import Any

import pytest

from whoosh_modern.config.engine import ConfigEngine
from whoosh_modern.config.loader import load_config, load_json, load_yaml
from whoosh_modern.config.models import WhooshNGConfig


@pytest.fixture
def yaml_config(tmp_path: Path) -> Path:
    config = textwrap.dedent(
        """\
        index: products
        languages:
          default: fr
        fields:
          title:
            type: text
            language: fr
            stemming: true
          price:
            type: numeric
            sortable: true
        search:
          fuzzy:
            enabled: true
            distance: 2
        """
    )
    path = tmp_path / "whoosh-ng.yml"
    path.write_text(config, encoding="utf-8")
    return path


@pytest.fixture
def json_config(tmp_path: Path) -> Path:
    config = {
        "index": "products",
        "languages": {"default": "en"},
        "fields": {
            "title": {"type": "text", "language": "en", "stemming": True},
            "price": {"type": "numeric", "sortable": True},
        },
        "search": {"fuzzy": {"enabled": True, "distance": 2}},
    }
    path = tmp_path / "whoosh-ng.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


class TestLoadYaml:
    def test_load_yaml_returns_dict(self, yaml_config: Path) -> None:
        data = load_yaml(yaml_config)
        assert isinstance(data, dict)
        assert data["index"] == "products"

    def test_load_yaml_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_yaml(tmp_path / "missing.yml")

    def test_load_yaml_empty_file(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.yml"
        path.write_text("", encoding="utf-8")
        assert load_yaml(path) == {}

    def test_load_yaml_without_pyyaml(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import builtins
        import sys

        original_import = builtins.__import__

        def failing_import(name: str, *args: Any, **kwargs: Any) -> Any:
            if name == "yaml":
                raise ImportError("No module named 'yaml'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", failing_import)
        monkeypatch.delitem(sys.modules, "yaml", raising=False)
        with pytest.raises(ImportError, match="PyYAML is required"):
            load_yaml(yaml_config)


class TestLoadJson:
    def test_load_json_returns_dict(self, json_config: Path) -> None:
        data = load_json(json_config)
        assert isinstance(data, dict)
        assert data["index"] == "products"

    def test_load_json_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_json(tmp_path / "missing.json")


class TestLoadConfig:
    def test_load_yaml_config(self, yaml_config: Path) -> None:
        config = load_config(yaml_config)
        assert isinstance(config, WhooshNGConfig)
        assert config.index == "products"
        assert config.fields["title"].stemming is True

    def test_load_json_config(self, json_config: Path) -> None:
        config = load_config(json_config)
        assert isinstance(config, WhooshNGConfig)
        assert config.index == "products"

    def test_load_unsupported_format(self, tmp_path: Path) -> None:
        path = tmp_path / "config.toml"
        path.write_text("", encoding="utf-8")
        with pytest.raises(ValueError, match="Unsupported configuration file format"):
            load_config(path)


class TestConfigEngine:
    def test_default_config(self) -> None:
        engine = ConfigEngine()
        config = engine.get_config()
        assert isinstance(config, WhooshNGConfig)
        assert config.index == "default"

    def test_load_yaml(self, yaml_config: Path) -> None:
        engine = ConfigEngine()
        engine.load(yaml_config)
        config = engine.get_config()
        assert config.index == "products"
        assert config.fields["title"].language == "fr"
        assert config.fields["title"].stemming is True
        assert config.search.fuzzy.enabled is True
        assert config.search.fuzzy.distance == 2

    def test_merge_overrides(self, yaml_config: Path) -> None:
        engine = ConfigEngine()
        engine.load(yaml_config)
        engine.merge({"index": "overridden", "search": {"fuzzy": {"distance": 5}}})
        config = engine.get_config()
        assert config.index == "overridden"
        assert config.search.fuzzy.distance == 5

    def test_hierarchical_merge(self, tmp_path: Path) -> None:
        base = tmp_path / "base.yml"
        base.write_text(
            textwrap.dedent(
                """\
                index: base
                fields:
                  title:
                    type: text
                    stemming: true
                search:
                  fuzzy:
                    enabled: false
                """
            ),
            encoding="utf-8",
        )
        override = tmp_path / "override.yml"
        override.write_text(
            textwrap.dedent(
                """\
                fields:
                  title:
                    stemming: false
                search:
                  fuzzy:
                    enabled: true
                """
            ),
            encoding="utf-8",
        )
        engine = ConfigEngine()
        engine.load(base, priority="application")
        engine.load(override, priority="instance")
        config = engine.get_config()
        assert config.index == "base"
        assert config.fields["title"].stemming is False
        assert config.search.fuzzy.enabled is True

    def test_reset(self, yaml_config: Path) -> None:
        engine = ConfigEngine()
        engine.load(yaml_config)
        assert engine.get_config().index == "products"
        engine.reset()
        assert engine.get_config().index == "default"

    def test_runtime_overrides_highest(self, tmp_path: Path) -> None:
        base = tmp_path / "base.yml"
        base.write_text(
            textwrap.dedent(
                """\
                index: base
                search:
                  fuzzy:
                    distance: 1
                """
            ),
            encoding="utf-8",
        )
        engine = ConfigEngine()
        engine.load(base, priority="application")
        engine.merge({"search": {"fuzzy": {"distance": 10}}}, priority="runtime")
        config = engine.get_config()
        assert config.search.fuzzy.distance == 10

    def test_load_invalid_priority(self, yaml_config: Path) -> None:
        engine = ConfigEngine()
        with pytest.raises(ValueError, match="Invalid priority"):
            engine.load(yaml_config, priority="invalid")

    def test_merge_invalid_priority(self) -> None:
        engine = ConfigEngine()
        with pytest.raises(ValueError, match="Invalid priority"):
            engine.merge({}, priority="invalid")
