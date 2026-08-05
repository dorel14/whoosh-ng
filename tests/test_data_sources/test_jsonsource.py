"""Tests for JSONSource."""

import json
import os
import tempfile
from typing import Any

import pytest

from whoosh_modern.data_sources.json import JSONSource
from whoosh_modern.exceptions import DataSourceError


def _create_json_file(data: Any) -> str:
    """Create a temporary JSON file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


class TestJSONSource:
    def test_health_check_valid_file(self):
        path = _create_json_file([{"id": 1, "title": "Test"}])
        try:
            source = JSONSource(path=path)
            assert source.health_check() is True
        finally:
            os.remove(path)

    def test_health_check_missing_file(self):
        source = JSONSource(path="/nonexistent/path/file.json")
        assert source.health_check() is False

    def test_discover_schema_array(self):
        path = _create_json_file(
            [
                {"id": 1, "title": "Hello", "body": "World"},
                {"id": 2, "title": "Python", "body": "Tips"},
            ]
        )
        try:
            source = JSONSource(path=path)
            schema = source.discover_schema()
            assert "id" in schema
            assert "title" in schema
            assert "body" in schema
        finally:
            os.remove(path)

    def test_discover_schema_with_document_path(self):
        path = _create_json_file(
            {
                "results": [
                    {"id": 1, "title": "Hello"},
                    {"id": 2, "title": "World"},
                ]
            }
        )
        try:
            source = JSONSource(path=path, document_path="results")
            schema = source.discover_schema()
            assert "id" in schema
            assert "title" in schema
        finally:
            os.remove(path)

    def test_iter_documents_array(self):
        path = _create_json_file(
            [
                {"id": 1, "title": "Hello"},
                {"id": 2, "title": "World"},
            ]
        )
        try:
            source = JSONSource(path=path)
            docs = list(source.iter_documents())
            assert len(docs) == 2
            assert docs[0]["id"] == 1
            assert docs[0]["title"] == "Hello"
        finally:
            os.remove(path)

    def test_document_count(self):
        path = _create_json_file(
            [
                {"id": 1, "title": "Hello"},
                {"id": 2, "title": "World"},
            ]
        )
        try:
            source = JSONSource(path=path)
            assert source.document_count() == 2
        finally:
            os.remove(path)

    def test_metadata(self):
        path = _create_json_file([{"id": 1}])
        try:
            source = JSONSource(
                path=path,
                document_path="data",
                encoding="utf-8",
                incremental_field="id",
                id_field="id",
            )
            meta = source.metadata()
            assert meta["type"] == "json"
            assert meta["document_path"] == "data"
            assert meta["incremental_field"] == "id"
        finally:
            os.remove(path)

    def test_missing_file_raises(self):
        source = JSONSource(path="/nonexistent/file.json")
        with pytest.raises(DataSourceError):
            list(source.iter_documents())

    def test_invalid_json_raises(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        with open(path, "w", encoding="utf-8") as f:
            f.write("not valid json")
        try:
            source = JSONSource(path=path)
            with pytest.raises(DataSourceError):
                list(source.iter_documents())
        finally:
            os.remove(path)

    def test_name_property(self):
        path = _create_json_file([{"id": 1}])
        try:
            source = JSONSource(path=path)
            assert source.name == f"json:{path}"
        finally:
            os.remove(path)

    def test_empty_array_returns_empty_schema(self):
        path = _create_json_file([])
        try:
            source = JSONSource(path=path)
            schema = source.discover_schema()
            assert len(schema) == 0
        finally:
            os.remove(path)
