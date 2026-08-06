"""Tests for async storage providers."""

from __future__ import annotations

import os

import pytest

from whoosh_modern.storage.async_file import AsyncFileStorage


pytestmark = pytest.mark.asyncio


@pytest.fixture
def async_storage(tmp_path):
    return AsyncFileStorage(str(tmp_path))


class TestAsyncFileStorage:
    async def test_write_and_read(self, async_storage) -> None:
        await async_storage.awrite("key.txt", b"hello world")
        data = await async_storage.aread("key.txt")
        assert data == b"hello world"

    async def test_exists(self, async_storage) -> None:
        await async_storage.awrite("exists.txt", b"data")
        assert await async_storage.aexists("exists.txt") is True
        assert await async_storage.aexists("missing.txt") is False

    async def test_delete(self, async_storage) -> None:
        await async_storage.awrite("delete_me.txt", b"temp")
        assert await async_storage.aexists("delete_me.txt") is True
        await async_storage.adelete("delete_me.txt")
        assert await async_storage.aexists("delete_me.txt") is False

    async def test_list_keys(self, async_storage) -> None:
        await async_storage.awrite("a.txt", b"1")
        await async_storage.awrite("b.txt", b"2")
        await async_storage.awrite("sub/c.txt", b"3")
        keys = await async_storage.alist_keys()
        assert "a.txt" in keys
        assert "b.txt" in keys
        assert "sub/c.txt" in keys
