"""Tests for DataSource protocol and capability protocols."""

import pytest

from whoosh.fields import Schema
from whoosh_modern.data_sources import (
    AsyncDataSource,
    CountableDataSource,
    DataSource,
    IncrementalDataSource,
    MetadataDataSource,
    RefreshableDataSource,
)


class FakeDataSource:
    """A duck-typed implementation of DataSource for testing."""

    @property
    def name(self) -> str:
        return "fake"

    def discover_schema(self) -> Schema:
        return Schema()

    def iter_documents(self):
        yield {}


class TestDataSourceProtocol:
    def test_duck_typing_with_hasattr(self):
        """DataSource protocol uses duck typing - check attributes."""
        source = FakeDataSource()
        assert hasattr(source, "name")
        assert hasattr(source, "discover_schema")
        assert hasattr(source, "iter_documents")

    def test_protocol_has_name_property(self):
        source = FakeDataSource()
        assert source.name == "fake"

    def test_protocol_has_discover_schema(self):
        source = FakeDataSource()
        schema = source.discover_schema()
        assert isinstance(schema, Schema)

    def test_protocol_has_iter_documents(self):
        source = FakeDataSource()
        docs = list(source.iter_documents())
        assert isinstance(docs, list)


class TestIncrementalDataSource:
    def test_duck_types_with_iter_changes(self):
        class IncrementalSource:
            def iter_changes(self, since):
                yield {}

        source = IncrementalSource()
        assert isinstance(source, IncrementalDataSource)


class TestAsyncDataSource:
    def test_duck_types_with_aiter_documents(self):
        class AsyncSource:
            async def aiter_documents(self):
                yield {}

        source = AsyncSource()
        assert isinstance(source, AsyncDataSource)


class TestRefreshableDataSource:
    def test_duck_types_with_refresh(self):
        class RefreshableSource:
            def refresh(self):
                pass

        source = RefreshableSource()
        assert isinstance(source, RefreshableDataSource)


class TestCountableDataSource:
    def test_duck_types_with_document_count(self):
        class CountableSource:
            def document_count(self):
                return 0

        source = CountableSource()
        assert isinstance(source, CountableDataSource)
        assert source.document_count() == 0


class TestMetadataDataSource:
    def test_duck_types_with_metadata(self):
        class MetaSource:
            def metadata(self):
                return {}

        source = MetaSource()
        assert isinstance(source, MetadataDataSource)
        assert source.metadata() == {}
