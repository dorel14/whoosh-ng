from __future__ import annotations

import pytest

from whoosh.registry.base import Registry
from whoosh.registry import (
    AnalyzerRegistry,
    RankingRegistry,
    StorageRegistry,
    SuggestRegistry,
    VectorRegistry,
)


class DummyItem:
    name: str = "dummy"


@pytest.fixture
def registry() -> Registry:
    return Registry("test")


def test_register_and_get(registry: Registry) -> None:
    registry.register("item", DummyItem(), owner="tests")
    item = registry.get("item")
    assert item.name == "dummy"


def test_duplicate_registration(registry: Registry) -> None:
    registry.register("item", DummyItem())
    with pytest.raises(KeyError):
        registry.register("item", DummyItem())


def test_unregister(registry: Registry) -> None:
    registry.register("item", DummyItem())
    registry.unregister("item")
    with pytest.raises(KeyError):
        registry.get("item")


def test_list_keys(registry: Registry) -> None:
    registry.register("a", DummyItem())
    registry.register("b", DummyItem())
    assert registry.list_keys() == ["a", "b"]


def test_owner_tracking(registry: Registry) -> None:
    registry.register("item", DummyItem(), owner="my_plugin")
    assert registry.owner("item") == "my_plugin"


def test_default_registries_have_predefined_names() -> None:
    assert StorageRegistry._name == "storage"
    assert AnalyzerRegistry._name == "analyzer"
    assert RankingRegistry._name == "ranking"
    assert SuggestRegistry._name == "suggest"
    assert VectorRegistry._name == "vector"
