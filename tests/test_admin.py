"""Tests for whoosh_admin plugin."""

import os
import tempfile

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
import httpx  # noqa: E402

from whoosh import fields  # noqa: E402
from whoosh.index import create_in, open_dir  # noqa: E402
from whoosh_admin import create_admin_app  # noqa: E402


def _build_index() -> str:
    schema = fields.Schema(title=fields.TEXT(stored=True), content=fields.TEXT(stored=True))
    tmp = tempfile.mkdtemp()
    ix = create_in(tmp, schema)
    with ix.writer() as w:
        w.add_document(title="Hello", content="world one")
        w.add_document(title="Foo", content="bar two")
    return tmp


@pytest.fixture
def app():
    tmp = _build_index()
    application = create_admin_app(open_dir(tmp))
    yield application
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)


@pytest.mark.asyncio
async def test_admin_index_page(app) -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/admin/")
        assert resp.status_code == 200
        assert "Whoosh-NG Admin" in resp.text


@pytest.mark.asyncio
async def test_admin_stats_endpoint(app) -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/admin/stats")
        assert resp.status_code == 200
        body = resp.json()
        assert "index_stats" in body


@pytest.mark.asyncio
async def test_admin_explore_endpoint(app) -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/admin/explore")
        assert resp.status_code == 200
        body = resp.json()
        assert "documents" in body
