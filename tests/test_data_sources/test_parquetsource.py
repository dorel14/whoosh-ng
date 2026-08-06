"""Tests for ParquetSource (optional backend)."""

import os
import tempfile
from typing import Any

import pytest

pandas = pytest.importorskip("pandas")

from whoosh_modern.data_sources.parquet_ds import ParquetSource
from whoosh_modern.exceptions import DataSourceError


def _create_parquet_file(data: dict[str, list[Any]]) -> str:
    """Create a temporary Parquet file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".parquet")
    os.close(fd)
    df = pandas.DataFrame(data)
    df.to_parquet(path, index=False)
    return path


class TestParquetSource:
    def test_health_check_valid_file(self):
        path = _create_parquet_file({"id": [1, 2], "title": ["Hello", "World"]})
        try:
            source = ParquetSource(path=path)
            assert source.health_check() is True
        finally:
            os.remove(path)

    def test_health_check_missing_file(self):
        source = ParquetSource(path="/nonexistent/file.parquet")
        assert source.health_check() is False

    def test_discover_schema(self):
        path = _create_parquet_file({"id": [1, 2], "title": ["Hello", "World"]})
        try:
            source = ParquetSource(path=path)
            schema = source.discover_schema()
            assert "id" in schema
            assert "title" in schema
        finally:
            os.remove(path)

    def test_iter_documents(self):
        path = _create_parquet_file({"id": [1, 2], "title": ["Hello", "World"]})
        try:
            source = ParquetSource(path=path)
            docs = list(source.iter_documents())
            assert len(docs) == 2
            assert docs[0]["id"] == 1
        finally:
            os.remove(path)

    def test_document_count(self):
        path = _create_parquet_file({"id": [1, 2], "title": ["Hello", "World"]})
        try:
            source = ParquetSource(path=path)
            assert source.document_count() == 2
        finally:
            os.remove(path)

    def test_metadata(self):
        path = _create_parquet_file({"id": [1], "title": ["Hello"]})
        try:
            source = ParquetSource(
                path=path,
                incremental_field="id",
                id_field="id",
            )
            meta = source.metadata()
            assert meta["type"] == "parquet"
            assert meta["incremental_field"] == "id"
        finally:
            os.remove(path)

    def test_missing_file_raises(self):
        source = ParquetSource(path="/nonexistent/file.parquet")
        with pytest.raises(DataSourceError):
            list(source.iter_documents())

    def test_name_property(self):
        path = _create_parquet_file({"id": [1]})
        try:
            source = ParquetSource(path=path)
            assert source.name == f"parquet:{path}"
        finally:
            os.remove(path)
