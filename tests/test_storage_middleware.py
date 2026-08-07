"""Tests for storage middleware and pluggable storage providers."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from whoosh.middleware.context import MiddlewareContext
from whoosh_modern.middleware import (
    FileStorageProvider,
    S3StorageProvider,
    SQLiteStorageProvider,
    StorageMiddleware,
)


class TestFileStorageProvider:
    def test_round_trip(self, tmp_path) -> None:
        provider = FileStorageProvider(str(tmp_path))
        provider.write("a/b.bin", b"hello")
        assert provider.read("a/b.bin") == b"hello"
        assert provider.exists("a/b.bin") is True
        assert provider.list_keys() == ["a/b.bin"]
        provider.delete("a/b.bin")
        assert provider.exists("a/b.bin") is False
        assert provider.list_keys() == []

    def test_missing_key_raises(self, tmp_path) -> None:
        provider = FileStorageProvider(str(tmp_path))
        with pytest.raises(FileNotFoundError):
            provider.read("missing")


class TestSQLiteStorageProvider:
    def test_round_trip(self, tmp_path) -> None:
        db = str(tmp_path / "blobs.db")
        provider = SQLiteStorageProvider(db)
        provider.write("key1", b"v1")
        provider.write("nested/key2", b"v2")
        assert provider.read("key1") == b"v1"
        assert provider.read("nested/key2") == b"v2"
        assert provider.exists("key1") is True
        assert sorted(provider.list_keys()) == ["key1", "nested/key2"]
        provider.delete("key1")
        assert provider.exists("key1") is False
        provider.close()

    def test_missing_key_raises(self, tmp_path) -> None:
        db = str(tmp_path / "blobs.db")
        provider = SQLiteStorageProvider(db)
        with pytest.raises(KeyError):
            provider.read("nope")
        provider.close()


class TestS3StorageProvider:
    def _fake_client(self) -> tuple[MagicMock, dict[str, bytes]]:
        store: dict[str, bytes] = {}
        client = MagicMock()

        def put_object(**kwargs):
            store[kwargs["Key"]] = kwargs["Body"]
            return {}

        def get_object(**kwargs):
            key = kwargs["Key"]
            if key not in store:
                raise KeyError(key)
            return {"Body": MagicMock(read=lambda: store[key])}

        def delete_object(**kwargs):
            store.pop(kwargs["Key"], None)
            return {}

        def head_object(**kwargs):
            if kwargs["Key"] not in store:
                raise KeyError(kwargs["Key"])
            return {}

        client.put_object.side_effect = put_object
        client.get_object.side_effect = get_object
        client.delete_object.side_effect = delete_object
        client.head_object.side_effect = head_object
        client.get_paginator.return_value.paginate.side_effect = lambda **kw: [
            {"Contents": [{"Key": k} for k in store]}
        ]
        return client, store

    def test_round_trip_with_injected_client(self) -> None:
        client, _ = self._fake_client()
        provider = S3StorageProvider(bucket="b", prefix="idx", client=client)
        provider.write("seg1", b"data")
        assert provider.read("seg1") == b"data"
        assert provider.exists("seg1") is True
        assert provider.list_keys() == ["seg1"]
        provider.delete("seg1")
        assert provider.exists("seg1") is False

    def test_missing_boto3_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "boto3" or name.startswith("boto3."):
                raise ImportError("no boto3")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        with pytest.raises(ImportError, match="boto3"):
            S3StorageProvider(bucket="b")


class TestStorageMiddleware:
    def test_delegates_to_provider(self, tmp_path) -> None:
        provider = FileStorageProvider(str(tmp_path))
        mw = StorageMiddleware(provider, name="fs")
        assert mw.provider is provider
        mw.write("doc/1", b"x")
        assert mw.read("doc/1") == b"x"
        assert mw.exists("doc/1") is True

    def test_before_index_tags_context(self, tmp_path) -> None:
        provider = FileStorageProvider(str(tmp_path))
        mw = StorageMiddleware(provider)
        ctx = MiddlewareContext("index")
        result = mw.before_index(ctx)
        assert result.labels["storage_backend"] == "FileStorageProvider"
        assert result.metadata["storage_provider"] is mw

    def test_on_commit_writes_marker(self, tmp_path) -> None:
        provider = FileStorageProvider(str(tmp_path))
        mw = StorageMiddleware(provider, name="fs")
        ctx = MiddlewareContext("index")
        mw.on_commit(ctx)
        keys = provider.list_keys()
        assert any(k.startswith("commits/fs/") for k in keys)
        assert ctx.metadata["storage_commit_marker"].startswith("commits/fs/")
