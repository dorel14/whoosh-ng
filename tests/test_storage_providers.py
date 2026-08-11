"""Tests for EPIC 4.5 Storage Providers (S3, Hybrid)."""

from __future__ import annotations

import os
from typing import Any

import pytest

from whoosh.filedb.filestore import FileStorage
from whoosh.plugins.storage_base import SyncStorageProvider
from whoosh_modern.storage import (
    AsyncHybridStorage,
    FileStorage,
    HybridStorage,
    S3Storage,
)
from whoosh_modern.storage.s3 import SnapshotStorage

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class FakeS3Client:
    """Minimal in-memory S3 client for tests."""

    def __init__(self) -> None:
        self._store: dict[str, bytes] = {}

    def put_object(self, Bucket: str, Key: str, Body: bytes) -> None:
        self._store[Key] = Body

    def get_object(self, Bucket: str, Key: str) -> dict[str, Any]:
        if Key not in self._store:
            raise Exception(f"Key '{Key}' not found")
        return {"Body": _FakeBody(self._store[Key])}

    def delete_object(self, Bucket: str, Key: str) -> None:
        self._store.pop(Key, None)

    def head_object(self, Bucket: str, Key: str) -> None:
        if Key not in self._store:
            raise Exception(f"Key '{Key}' not found")

    def get_paginator(self, operation: str) -> "_FakePaginator":
        return _FakePaginator(self._store)


class _FakeBody:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self) -> bytes:
        return self._data


class _FakePaginator:
    def __init__(self, store: dict[str, bytes]) -> None:
        self._store = store

    def paginate(self, Bucket: str, Prefix: str = "") -> list[dict[str, Any]]:
        prefix = Prefix.strip("/")
        keys: list[str] = []
        for k in self._store:
            if prefix and not k.startswith(f"{prefix}/"):
                continue
            keys.append(k)
        return [{"Contents": [{"Key": k} for k in sorted(keys)]}]


@pytest.fixture
def fake_s3_client():
    return FakeS3Client()


@pytest.fixture
def s3_storage(fake_s3_client):
    return S3Storage(bucket="test-bucket", prefix="segments", client=fake_s3_client)


@pytest.fixture
def remote_storage(tmp_path):
    return FileStorage(str(tmp_path / "remote"))


# ---------------------------------------------------------------------------
# FileStorage
# ---------------------------------------------------------------------------


def test_file_storage_round_trip(tmp_path) -> None:
    storage = FileStorage(str(tmp_path))
    storage.write("a.txt", b"hello")
    assert storage.read("a.txt") == b"hello"


def test_file_storage_exists(tmp_path) -> None:
    storage = FileStorage(str(tmp_path))
    storage.write("exists.txt", b"data")
    assert storage.exists("exists.txt") is True
    assert storage.exists("missing.txt") is False


def test_file_storage_delete(tmp_path) -> None:
    storage = FileStorage(str(tmp_path))
    storage.write("delete_me.txt", b"temp")
    assert storage.exists("delete_me.txt") is True
    storage.delete("delete_me.txt")
    assert storage.exists("delete_me.txt") is False


def test_file_storage_list_keys(tmp_path) -> None:
    storage = FileStorage(str(tmp_path))
    storage.write("a.txt", b"1")
    storage.write("b.txt", b"2")
    storage.write("sub/c.txt", b"3")
    keys = storage.list_keys()
    assert "a.txt" in keys
    assert "b.txt" in keys
    assert "sub/c.txt" in keys


# ---------------------------------------------------------------------------
# CoreStorageAdapter
# ---------------------------------------------------------------------------


def test_core_adapter_round_trip(tmp_path) -> None:
    from whoosh.filedb.filestore import FileStorage as CoreFileStorage

    core = CoreFileStorage(str(tmp_path))
    adapter = CoreStorageAdapter(core)
    adapter.write("segment.dat", b"segdata")
    assert adapter.read("segment.dat") == b"segdata"


def test_core_adapter_exists(tmp_path) -> None:
    from whoosh.filedb.filestore import FileStorage as CoreFileStorage

    core = CoreFileStorage(str(tmp_path))
    adapter = CoreStorageAdapter(core)
    adapter.write("exists.dat", b"x")
    assert adapter.exists("exists.dat") is True
    assert adapter.exists("missing.dat") is False


def test_core_adapter_delete(tmp_path) -> None:
    from whoosh.filedb.filestore import FileStorage as CoreFileStorage

    core = CoreFileStorage(str(tmp_path))
    adapter = CoreStorageAdapter(core)
    adapter.write("del.dat", b"tmp")
    assert adapter.exists("del.dat") is True
    adapter.delete("del.dat")
    assert adapter.exists("del.dat") is False


def test_core_adapter_delete_missing_is_noop(tmp_path) -> None:
    from whoosh.filedb.filestore import FileStorage as CoreFileStorage

    core = CoreFileStorage(str(tmp_path))
    adapter = CoreStorageAdapter(core)
    adapter.delete("missing.dat")  # should not raise


def test_core_adapter_list_keys(tmp_path) -> None:
    from whoosh.filedb.filestore import FileStorage as CoreFileStorage

    core = CoreFileStorage(str(tmp_path))
    adapter = CoreStorageAdapter(core)
    adapter.write("a.dat", b"1")
    adapter.write("b.dat", b"2")
    keys = adapter.list_keys()
    assert "a.dat" in keys
    assert "b.dat" in keys


def test_core_adapter_is_sync_provider() -> None:
    from whoosh.filedb.filestore import RamStorage

    core = RamStorage()
    adapter = CoreStorageAdapter(core)
    assert isinstance(adapter, SyncStorageProvider)


# ---------------------------------------------------------------------------
# S3Storage
# ---------------------------------------------------------------------------


def test_s3_round_trip(s3_storage: S3Storage) -> None:
    s3_storage.write("segment_1.dat", b"segdata")
    assert s3_storage.read("segment_1.dat") == b"segdata"


def test_s3_exists(s3_storage: S3Storage) -> None:
    s3_storage.write("exists.dat", b"x")
    assert s3_storage.exists("exists.dat") is True
    assert s3_storage.exists("missing.dat") is False


def test_s3_delete(s3_storage: S3Storage) -> None:
    s3_storage.write("del.dat", b"tmp")
    assert s3_storage.exists("del.dat") is True
    s3_storage.delete("del.dat")
    assert s3_storage.exists("del.dat") is False


def test_s3_list_keys(s3_storage: S3Storage) -> None:
    s3_storage.write("a.dat", b"1")
    s3_storage.write("b.dat", b"2")
    keys = s3_storage.list_keys()
    assert "a.dat" in keys
    assert "b.dat" in keys


def test_s3_prefix(fake_s3_client) -> None:
    storage = S3Storage(bucket="b", prefix="pre", client=fake_s3_client)
    storage.write("k.dat", b"v")
    assert fake_s3_client._store["pre/k.dat"] == b"v"


# ---------------------------------------------------------------------------
# SnapshotStorage
# ---------------------------------------------------------------------------


@pytest.fixture
def snapshot_storage(tmp_path, fake_s3_client):
    return SnapshotStorage(
        local_path=str(tmp_path / "scratch"),
        bucket="test-bucket",
        prefix="segments",
        client=fake_s3_client,
    )


def test_snapshot_storage_read_caches_locally(snapshot_storage: SnapshotStorage, tmp_path) -> None:
    snapshot_storage.write("segment_1.dat", b"segdata")
    data = snapshot_storage.read("segment_1.dat")
    assert data == b"segdata"
    cached_path = tmp_path / "scratch" / "segment_1.dat"
    assert cached_path.read_bytes() == b"segdata"


def test_snapshot_storage_read_rejects_parent_traversal(
    snapshot_storage: SnapshotStorage, fake_s3_client
) -> None:
    fake_s3_client._store["segments/../../etc/passwd"] = b"malicious"
    with pytest.raises(ValueError, match=r"path traversal.*not allowed"):
        snapshot_storage.read("../../etc/passwd")


def test_snapshot_storage_read_rejects_embedded_traversal(
    snapshot_storage: SnapshotStorage, fake_s3_client
) -> None:
    fake_s3_client._store["segments/foo/../../../etc/passwd"] = b"malicious"
    with pytest.raises(ValueError, match=r"path traversal.*not allowed"):
        snapshot_storage.read("foo/../../../etc/passwd")


def test_snapshot_storage_read_rejects_absolute_path(
    snapshot_storage: SnapshotStorage, fake_s3_client
) -> None:
    fake_s3_client._store["segments/etc/passwd"] = b"malicious"
    with pytest.raises(ValueError, match=r"absolute paths are not allowed"):
        snapshot_storage.read("/etc/passwd")


def test_snapshot_storage_read_does_not_escape_local_path(
    snapshot_storage: SnapshotStorage, tmp_path
) -> None:
    snapshot_storage.write("safe/segment.dat", b"ok")
    snapshot_storage.read("safe/segment.dat")
    cached_path = tmp_path / "scratch" / "safe" / "segment.dat"
    assert cached_path.read_bytes() == b"ok"
    assert not (tmp_path / "etc").exists()


# ---------------------------------------------------------------------------
# HybridStorage
# ---------------------------------------------------------------------------


def test_hybrid_read_cache_miss_then_hit(tmp_path, remote_storage: FileStorage) -> None:
    remote_storage.write("hot.dat", b"remote-data")
    cache = str(tmp_path / "cache")
    storage = HybridStorage(local_cache=cache, remote=remote_storage)
    assert storage.read("hot.dat") == b"remote-data"
    assert os.path.exists(os.path.join(cache, "hot.dat"))
    assert storage.read("hot.dat") == b"remote-data"


def test_hybrid_write_through(tmp_path, remote_storage: FileStorage) -> None:
    cache = str(tmp_path / "cache")
    storage = HybridStorage(local_cache=cache, remote=remote_storage)
    storage.write("new.dat", b"value")
    assert remote_storage.read("new.dat") == b"value"
    assert os.path.exists(os.path.join(cache, "new.dat"))


def test_hybrid_delete_propagates(tmp_path, remote_storage: FileStorage) -> None:
    remote_storage.write("del.dat", b"x")
    cache = str(tmp_path / "cache")
    storage = HybridStorage(local_cache=cache, remote=remote_storage)
    storage.read("del.dat")
    storage.delete("del.dat")
    assert remote_storage.exists("del.dat") is False
    assert not os.path.exists(os.path.join(cache, "del.dat"))


def test_hybrid_exists_cache_hit(tmp_path, remote_storage: FileStorage) -> None:
    remote_storage.write("exists.dat", b"x")
    cache = str(tmp_path / "cache")
    storage = HybridStorage(local_cache=cache, remote=remote_storage)
    storage.read("exists.dat")
    assert storage.exists("exists.dat") is True


def test_hybrid_exists_miss(tmp_path, remote_storage: FileStorage) -> None:
    cache = str(tmp_path / "cache")
    storage = HybridStorage(local_cache=cache, remote=remote_storage)
    assert storage.exists("nope.dat") is False


def test_hybrid_list_keys_from_remote(tmp_path, remote_storage: FileStorage) -> None:
    remote_storage.write("a.dat", b"1")
    remote_storage.write("b.dat", b"2")
    cache = str(tmp_path / "cache")
    storage = HybridStorage(local_cache=cache, remote=remote_storage)
    keys = storage.list_keys()
    assert "a.dat" in keys
    assert "b.dat" in keys


def test_hybrid_list_keys_include_cache(tmp_path, remote_storage: FileStorage) -> None:
    cache = str(tmp_path / "cache")
    storage = HybridStorage(local_cache=cache, remote=remote_storage)
    with open(os.path.join(cache, "cached.dat"), "wb") as fh:
        fh.write(b"cached")
    remote_storage.write("remote.dat", b"r")
    keys = storage.list_keys(include_cache=True)
    assert "cached.dat" in keys
    assert "remote.dat" in keys


def test_hybrid_invalidate(tmp_path, remote_storage: FileStorage) -> None:
    remote_storage.write("inv.dat", b"v")
    cache = str(tmp_path / "cache")
    storage = HybridStorage(local_cache=cache, remote=remote_storage)
    storage.read("inv.dat")
    storage.invalidate("inv.dat")
    assert not os.path.exists(os.path.join(cache, "inv.dat"))


def test_hybrid_prefetch(tmp_path, remote_storage: FileStorage) -> None:
    remote_storage.write("p1.dat", b"1")
    remote_storage.write("p2.dat", b"2")
    cache = str(tmp_path / "cache")
    storage = HybridStorage(local_cache=cache, remote=remote_storage)
    storage.prefetch(["p1.dat", "p2.dat"])
    assert os.path.exists(os.path.join(cache, "p1.dat"))
    assert os.path.exists(os.path.join(cache, "p2.dat"))


def test_hybrid_write_does_not_pollute_cache_on_remote_failure(tmp_path) -> None:
    class FailingRemote(SyncStorageProvider):
        def write(self, key: str, data: bytes) -> None:
            raise RuntimeError("S3 down")

        def read(self, key: str) -> bytes:
            raise RuntimeError("S3 down")

        def delete(self, key: str) -> None:
            raise RuntimeError("S3 down")

        def exists(self, key: str) -> bool:
            return False

        def list_keys(self) -> list[str]:
            return []

    cache = str(tmp_path / "cache")
    storage = HybridStorage(local_cache=cache, remote=FailingRemote())
    with pytest.raises(RuntimeError):
        storage.write("key.dat", b"data")
    assert not os.path.exists(os.path.join(cache, "key.dat"))


# ---------------------------------------------------------------------------
# AsyncHybridStorage
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_hybrid_round_trip(tmp_path, remote_storage: FileStorage) -> None:
    remote_storage.write("async.dat", b"async-data")
    cache = str(tmp_path / "cache")
    storage = AsyncHybridStorage(local_cache=cache, remote=remote_storage)
    assert await storage.aread("async.dat") == b"async-data"


@pytest.mark.asyncio
async def test_async_hybrid_awrite(tmp_path, remote_storage: FileStorage) -> None:
    cache = str(tmp_path / "cache")
    storage = AsyncHybridStorage(local_cache=cache, remote=remote_storage)
    await storage.awrite("async_write.dat", b"av")
    assert remote_storage.read("async_write.dat") == b"av"
