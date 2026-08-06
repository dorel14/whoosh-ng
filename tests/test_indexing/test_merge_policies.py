"""Tests for merge policies."""

from __future__ import annotations

import pytest

from whoosh import fields
from whoosh.index import create_in
from whoosh_modern.indexing.merge_policies import (
    LogMergePolicy,
    MergePolicy,
    NoMergePolicy,
    TieredMergePolicy,
)


@pytest.fixture
def tmpdir_index(tmp_path):
    schema = fields.Schema(title=fields.TEXT(stored=True), content=fields.TEXT)
    return create_in(str(tmp_path), schema)


class TestMergePolicies:
    def test_no_merge_policy(self, tmpdir_index):
        policy = NoMergePolicy()
        assert policy.should_merge(tmpdir_index) is False
        assert policy.merge_kwargs(tmpdir_index) == {"merge": False}

    def test_log_merge_policy_below_threshold(self, tmpdir_index):
        writer = tmpdir_index.writer()
        writer.add_document(title="hello", content="world")
        writer.commit(merge=False)
        policy = LogMergePolicy(max_segments=10)
        assert policy.should_merge(tmpdir_index) is False

    def test_log_merge_policy_above_threshold(self, tmpdir_index):
        for i in range(3):
            w = tmpdir_index.writer(multisegment=True)
            w.add_document(title=f"doc {i}", content="x")
            w.commit(merge=False)
        policy = LogMergePolicy(max_segments=2)
        assert policy.should_merge(tmpdir_index) is True
        assert policy.merge_kwargs(tmpdir_index) == {"merge": True}

    def test_tiered_merge_policy_below_threshold(self, tmpdir_index):
        writer = tmpdir_index.writer()
        writer.add_document(title="hello", content="world")
        writer.commit(merge=False)
        policy = TieredMergePolicy(max_segments=10)
        assert policy.should_merge(tmpdir_index) is False

    def test_tiered_merge_policy_above_threshold(self, tmpdir_index):
        for i in range(3):
            w = tmpdir_index.writer(multisegment=True)
            w.add_document(title=f"doc {i}", content="x")
            w.commit(merge=False)
        policy = TieredMergePolicy(max_segments=2, target_segment_size=1000)
        assert policy.should_merge(tmpdir_index) is True
        assert policy.merge_kwargs(tmpdir_index) == {"merge": True}
