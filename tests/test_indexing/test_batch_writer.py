"""Tests for BatchIndexWriter."""

import os
import tempfile

import pytest

from whoosh import fields
from whoosh.index import create_in
from whoosh_modern.indexing import BatchIndexWriter


def _create_index(dir_path: str):
    """Create a temporary index and return it."""
    schema = fields.Schema(
        id=fields.ID(stored=True),
        title=fields.TEXT(stored=True),
        body=fields.TEXT(),
    )
    ix = create_in(dir_path, schema)
    return ix


class TestBatchIndexWriter:
    def test_add_batch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ix = _create_index(tmpdir)
            writer = BatchIndexWriter(ix, batch_size=100)
            docs = [
                {"id": "1", "title": "Hello", "body": "World"},
                {"id": "2", "title": "Python", "body": "Tips"},
            ]
            count = writer.add_batch(docs)
            assert count == 2
            writer.close()
            assert ix.doc_count() == 2

    def test_add_empty_batch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ix = _create_index(tmpdir)
            writer = BatchIndexWriter(ix, batch_size=100)
            count = writer.add_batch([])
            assert count == 0
            writer.close()
            assert ix.doc_count() == 0

    def test_add_batches(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ix = _create_index(tmpdir)
            writer = BatchIndexWriter(ix, batch_size=100)
            batches = [
                [{"id": "1", "title": "A", "body": "B"}],
                [{"id": "2", "title": "C", "body": "D"}],
            ]
            count = writer.add_batches(iter(batches))
            assert count == 2
            writer.close()
            assert ix.doc_count() == 2

    def test_context_manager(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ix = _create_index(tmpdir)
            with BatchIndexWriter(ix, batch_size=100) as writer:
                writer.add_batch(
                    [
                        {"id": "1", "title": "Hello", "body": "World"},
                    ]
                )
            assert ix.doc_count() == 1

    def test_doc_count_property(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ix = _create_index(tmpdir)
            writer = BatchIndexWriter(ix, batch_size=100)
            writer.add_batch([{"id": "1", "title": "A", "body": "B"}])
            assert writer.doc_count == 1
            writer.close()

    def test_batch_count_property(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ix = _create_index(tmpdir)
            writer = BatchIndexWriter(ix, batch_size=100)
            writer.add_batch([{"id": "1", "title": "A", "body": "B"}])
            writer.add_batch([{"id": "2", "title": "C", "body": "D"}])
            assert writer.batch_count == 2
            writer.close()

    def test_filters_unknown_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ix = _create_index(tmpdir)
            writer = BatchIndexWriter(ix, batch_size=100)
            docs = [
                {"id": "1", "title": "Hello", "body": "World", "unknown_field": "ignored"},
            ]
            writer.add_batch(docs)
            writer.close()
            assert ix.doc_count() == 1

    def test_commit_every(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ix = _create_index(tmpdir)
            writer = BatchIndexWriter(ix, batch_size=100, commit_every=2)
            writer.add_batch([{"id": "1", "title": "A", "body": "B"}])
            writer.add_batch([{"id": "2", "title": "C", "body": "D"}])
            assert writer.batch_count == 2
            writer.close()
            assert ix.doc_count() == 2

    def test_close_returns_total(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ix = _create_index(tmpdir)
            writer = BatchIndexWriter(ix, batch_size=100)
            writer.add_batch([{"id": "1", "title": "A", "body": "B"}])
            writer.add_batch([{"id": "2", "title": "C", "body": "D"}])
            total = writer.close()
            assert total == 2

    def test_close_idempotent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ix = _create_index(tmpdir)
            writer = BatchIndexWriter(ix, batch_size=100)
            writer.add_batch([{"id": "1", "title": "A", "body": "B"}])
            writer.close()
            writer.close()
            assert ix.doc_count() == 1
