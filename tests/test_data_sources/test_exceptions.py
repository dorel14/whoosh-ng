"""Tests for typed exceptions with source and field context."""

import pytest

from whoosh import WhooshError
from whoosh_modern.exceptions import (
    DataSourceError,
    DataSourceNotFoundError,
    DocumentIterationError,
    SchemaDiscoveryError,
    ValidationError,
)


class TestDataSourceError:
    def test_base_exception_message(self):
        exc = DataSourceError("something went wrong")
        assert str(exc) == "something went wrong"

    def test_exception_with_source(self):
        exc = DataSourceError("failed", source="sql")
        assert exc.source == "sql"

    def test_exception_with_field(self):
        exc = DataSourceError("bad field", field="title")
        assert exc.field == "title"

    def test_exception_with_source_and_field(self):
        exc = DataSourceError("bad source and field", source="sql", field="id")
        assert exc.source == "sql"
        assert exc.field == "id"

    def test_exception_context(self):
        """All exceptions carry source/field context."""
        exc = DataSourceError("test", source="rest", field="url")
        assert exc.source == "rest"
        assert exc.field == "url"

    def test_is_whoosh_error(self):
        assert issubclass(DataSourceError, WhooshError)


class TestSchemaDiscoveryError:
    def test_is_subclass(self):
        assert issubclass(SchemaDiscoveryError, DataSourceError)

    def test_duplicate_column(self):
        exc = SchemaDiscoveryError("Duplicate column name: id", field="id")
        assert exc.field == "id"


class TestDocumentIterationError:
    def test_is_subclass(self):
        assert issubclass(DocumentIterationError, DataSourceError)


class TestValidationError:
    def test_is_subclass(self):
        assert issubclass(ValidationError, DataSourceError)


class TestDataSourceNotFoundError:
    def test_is_subclass(self):
        assert issubclass(DataSourceNotFoundError, DataSourceError)

    def test_not_found_message(self):
        exc = DataSourceNotFoundError("Source not found", source="sql")
        assert exc.source == "sql"
        assert "not found" in str(exc).lower()
