"""Tests for ObservableDataSource protocol."""

import pytest

from whoosh_modern.data_sources import ObservableDataSource


class ObservableSource:
    """A duck-typed implementation of ObservableDataSource for testing."""

    def __init__(self) -> None:
        self._observers: list[object] = []

    def add_observer(self, callback: object) -> None:
        self._observers.append(callback)

    def remove_observer(self, callback: object) -> None:
        self._observers.remove(callback)


class TestObservableDataSource:
    def test_duck_types_with_observers(self):
        source = ObservableSource()
        assert isinstance(source, ObservableDataSource)

    def test_add_observer(self):
        source = ObservableSource()

        def callback(event, doc):
            pass

        source.add_observer(callback)
        assert callback in source._observers

    def test_remove_observer(self):
        source = ObservableSource()

        def callback(event, doc):
            pass

        source.add_observer(callback)
        source.remove_observer(callback)
        assert callback not in source._observers

    def test_remove_observer_raises_if_not_found(self):
        source = ObservableSource()

        def callback(event, doc):
            pass

        with pytest.raises(ValueError, match="list"):
            source.remove_observer(callback)
