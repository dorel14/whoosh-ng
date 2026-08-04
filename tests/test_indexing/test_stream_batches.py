"""Tests for batch writer API and stream_batches protocol."""

from __future__ import annotations

from pathlib import Path

import pytest

from whoosh import fields
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser
from whoosh.searching import Searcher
from whoosh_modern.data_sources import DataSource
from whoosh_modern.data_sources.fast_csv import FastCSVSource
from whoosh_modern.data_sources.json import JSONSource
from whoosh_modern.data_sources.pandas_ds import PandasSource
from whoosh_modern.data_sources.parquet_ds import ParquetSource
from whoosh_modern.data_sources.polars_ds import PolarsSource


@pytest.fixture
def tmp_path_str(tmp_path):
    return str(tmp_path)


class FakeSource:
    def __init__(self, docs):
        self._docs = docs
        self._name = "fake"

    @property
    def name(self):
        return self._name

    def discover_schema(self):
        return fields.Schema(title=fields.TEXT(stored=True))

    def iter_documents(self):
        yield from self._docs

    def stream_batches(self, batch_size=1000):
        batch = []
        for doc in self.iter_documents():
            batch.append(doc)
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch

    def health_check(self):
        return True


class TestBatchWriter:
    def test_add_batch_indexes_all_docs(self, tmp_path_str):
        schema = fields.Schema(title=fields.TEXT(stored=True))
        ix = create_in(tmp_path_str, schema)
        writer = ix.writer()
        docs = [{"title": f"doc {i}"} for i in range(100)]
        writer.add_batch(docs)
        writer.commit(merge=False)
        assert ix.doc_count() == 100

    def test_add_batch_with_batch_size_chunks(self, tmp_path_str):
        schema = fields.Schema(title=fields.TEXT(stored=True))
        ix = create_in(tmp_path_str, schema)
        writer = ix.writer()
        docs = [{"title": f"doc {i}"} for i in range(100)]
        writer.add_batch(docs, batch_size=25)
        writer.commit(merge=False)
        assert ix.doc_count() == 100

    def test_add_batch_empty(self, tmp_path_str):
        schema = fields.Schema(title=fields.TEXT(stored=True))
        ix = create_in(tmp_path_str, schema)
        writer = ix.writer()
        writer.add_batch([])
        writer.commit(merge=False)
        assert ix.doc_count() == 0

    def test_add_batch_searchable(self, tmp_path_str):
        schema = fields.Schema(title=fields.TEXT(stored=True))
        ix = create_in(tmp_path_str, schema)
        writer = ix.writer()
        docs = [{"title": "hello world"} for _ in range(10)]
        writer.add_batch(docs)
        writer.commit(merge=False)

        with ix.searcher() as searcher:
            qp = QueryParser("title", schema)
            results = searcher.search(qp.parse("hello"))
            assert len(results) == 10


class TestStreamBatches:
    def test_stream_batches_groups_docs(self):
        docs = [{"title": f"doc {i}"} for i in range(250)]
        source = FakeSource(docs)
        batches = list(source.stream_batches(batch_size=100))
        assert len(batches) == 3
        assert sum(len(b) for b in batches) == 250
        assert len(batches[0]) == 100
        assert len(batches[1]) == 100
        assert len(batches[2]) == 50

    def test_stream_batches_default_size(self):
        docs = [{"title": f"doc {i}"} for i in range(10)]
        source = FakeSource(docs)
        batches = list(source.stream_batches())
        assert len(batches) == 1
        assert len(batches[0]) == 10


class TestDataSourceStreamBatches:
    def test_csv_stream_batches(self):
        csv_path = (
            Path(__file__).parent.parent.parent
            / "benchmark"
            / "Datas"
            / "customers-2000000.csv"
        )
        if not csv_path.exists():
            pytest.skip("CSV benchmark file not available")
        source = FastCSVSource(path=str(csv_path))
        schema = source.discover_schema()
        batches = []
        count = 0
        for batch in source.stream_batches(batch_size=1000):
            batches.append(batch)
            count += len(batch)
            if count >= 5000:
                break
        assert count > 0
        assert all(len(b) <= 1000 for b in batches)

    def test_json_stream_batches(self):
        json_path = (
            Path(__file__).parent.parent.parent
            / "benchmark"
            / "Datas"
            / "all_latest"
            / "2026-07-31_053230-data.gouv_local.json"
        )
        if not json_path.exists():
            pytest.skip("JSON benchmark file not available")
        source = JSONSource(path=str(json_path), document_path="service")
        batches = []
        count = 0
        for batch in source.stream_batches(batch_size=500):
            batches.append(batch)
            count += len(batch)
            if count >= 2000:
                break
        assert count > 0
        assert all(len(b) <= 500 for b in batches)
