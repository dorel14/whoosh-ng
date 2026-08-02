"""Tests for CSVSource."""

import csv
import os
import tempfile

import pytest

from whoosh_modern.data_sources.csv import CSVSource
from whoosh_modern.exceptions import DataSourceError


def _create_csv_file(data: list[dict[str, str]]) -> str:
    """Create a temporary CSV file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    with open(path, "w", newline="", encoding="utf-8") as f:
        if data:
            writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
            writer.writeheader()
            writer.writerows(data)
    return path


class TestCSVSource:
    def test_health_check_valid_file(self):
        path = _create_csv_file([{"id": "1", "title": "Test"}])
        try:
            source = CSVSource(path=path)
            assert source.health_check() is True
        finally:
            os.remove(path)

    def test_health_check_missing_file(self):
        source = CSVSource(path="/nonexistent/path/file.csv")
        assert source.health_check() is False

    def test_discover_schema(self):
        path = _create_csv_file([
            {"id": "1", "title": "Hello", "body": "World"},
            {"id": "2", "title": "Python", "body": "Tips"},
        ])
        try:
            source = CSVSource(path=path)
            schema = source.discover_schema()
            assert "id" in schema
            assert "title" in schema
            assert "body" in schema
        finally:
            os.remove(path)

    def test_iter_documents(self):
        path = _create_csv_file([
            {"id": "1", "title": "Hello"},
            {"id": "2", "title": "World"},
        ])
        try:
            source = CSVSource(path=path)
            docs = list(source.iter_documents())
            assert len(docs) == 2
            assert docs[0]["id"] == "1"
            assert docs[0]["title"] == "Hello"
        finally:
            os.remove(path)

    def test_document_count(self):
        path = _create_csv_file([
            {"id": "1", "title": "Hello"},
            {"id": "2", "title": "World"},
        ])
        try:
            source = CSVSource(path=path)
            assert source.document_count() == 2
        finally:
            os.remove(path)

    def test_metadata(self):
        path = _create_csv_file([{"id": "1", "title": "Test"}])
        try:
            source = CSVSource(
                path=path,
                delimiter=",",
                encoding="utf-8",
                incremental_field="id",
                id_field="id",
            )
            meta = source.metadata()
            assert meta["type"] == "csv"
            assert meta["incremental_field"] == "id"
            assert meta["id_field"] == "id"
        finally:
            os.remove(path)

    def test_missing_file_raises(self):
        source = CSVSource(path="/nonexistent/file.csv")
        with pytest.raises(DataSourceError):
            list(source.iter_documents())

    def test_missing_file_discover_raises(self):
        source = CSVSource(path="/nonexistent/file.csv")
        with pytest.raises(DataSourceError):
            source.discover_schema()

    def test_name_property(self):
        path = _create_csv_file([{"id": "1"}])
        try:
            source = CSVSource(path=path)
            assert source.name == f"csv:{path}"
        finally:
            os.remove(path)

    def test_custom_delimiter(self):
        path = _create_csv_file([{"id": "1", "title": "Hello"}])
        try:
            source = CSVSource(path=path, delimiter=",")
            docs = list(source.iter_documents())
            assert len(docs) == 1
        finally:
            os.remove(path)
