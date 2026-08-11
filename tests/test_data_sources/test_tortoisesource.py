"""Tests for TortoiseSource (optional backend)."""

import pytest

tortoise = pytest.importorskip("tortoise")
from tortoise import fields  # noqa: E402
from tortoise.models import Model  # noqa: E402

from whoosh_modern.data_sources.tortoise_ds import TortoiseSource  # noqa: E402


class Article(Model):
    id = fields.IntField(primary_key=True)
    title = fields.CharField(max_length=255)
    body = fields.TextField()

    class Meta:
        table = "articles"


class TestTortoiseSource:
    @pytest.mark.asyncio
    async def test_discover_schema(self):
        source = TortoiseSource(model=Article)
        schema = source.discover_schema()
        assert "id" in schema
        assert "title" in schema
        assert "body" in schema

    @pytest.mark.asyncio
    async def test_metadata(self):
        source = TortoiseSource(model=Article)
        meta = source.metadata()
        assert meta["type"] == "tortoise"
        assert meta["table"] == "articles"

    @pytest.mark.asyncio
    async def test_name_property(self):
        source = TortoiseSource(model=Article)
        assert source.name == "tortoise:articles"
