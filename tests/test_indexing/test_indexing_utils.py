"""Tests for the shared indexing helpers in ``whoosh_modern.indexing._utils``.

Verifies that ``_rmtree_retry`` and ``_build_segment_worker`` are defined once
and reused by both ``modern_builder`` and ``parallel_builder``.
"""

import os
import tempfile
from unittest import mock

from whoosh import fields
from whoosh.index import open_dir
from whoosh_modern.indexing import modern_builder, parallel_builder
from whoosh_modern.indexing._utils import _build_segment_worker, _rmtree_retry


def _schema():
    return fields.Schema(id=fields.ID(stored=True), title=fields.TEXT(stored=True))


class TestSingleDefinition:
    def test_modern_builder_reuses_shared_helpers(self):
        assert modern_builder._rmtree_retry is _rmtree_retry
        assert modern_builder._build_segment_worker is _build_segment_worker

    def test_parallel_builder_does_not_redefine_helpers(self):
        assert not hasattr(parallel_builder, "_build_segment_worker")
        assert not hasattr(parallel_builder, "_rmtree_retry")


class TestRmtreeRetry:
    def test_removes_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = os.path.join(tmpdir, "sub")
            os.makedirs(target)
            _rmtree_retry(target)
            assert not os.path.exists(target)

    def test_retries_on_permission_error(self):
        calls = {"n": 0}

        def _fake_rmtree(path):
            calls["n"] += 1
            if calls["n"] < 3:
                raise PermissionError("locked")

        with mock.patch("whoosh_modern.indexing._utils.shutil.rmtree", _fake_rmtree):
            _rmtree_retry("whatever", retries=5, delay=0)

        assert calls["n"] == 3

    def test_gives_up_after_retries(self):
        def _always_locked(path):
            raise PermissionError("locked")

        with mock.patch("whoosh_modern.indexing._utils.shutil.rmtree", _always_locked):
            # Should not raise once the retry budget is exhausted.
            _rmtree_retry("whatever", retries=2, delay=0)


class TestBuildSegmentWorker:
    def test_builds_segment_index(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            seg_dir = os.path.join(tmpdir, "_segment_0")
            docs = [{"id": "1", "title": "hello"}, {"id": "2", "title": "world"}]

            result = _build_segment_worker((seg_dir, _schema(), docs, 0))

            assert result == seg_dir
            ix = open_dir(seg_dir)
            try:
                assert ix.doc_count() == 2
            finally:
                ix.close()
