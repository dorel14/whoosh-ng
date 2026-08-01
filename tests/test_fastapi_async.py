from __future__ import annotations

import os
import tempfile

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
import httpx  # noqa: E402

from whoosh import fields  # noqa: E402
from whoosh.index import create_in, open_dir  # noqa: E402
from whoosh_fastapi import create_app  # noqa: E402


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
    application = create_app(open_dir(tmp))
    yield application
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)


@pytest.mark.asyncio
async def test_health_endpoint(app) -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_search_endpoint(app) -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/search", json={"q": "world"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert any("world" in str(hit.get("fields", {})) for hit in body["hits"])


@pytest.mark.asyncio
async def test_autocomplete_endpoint_with_provider() -> None:
    from whoosh_modern.autocomplete.factory import create_autocomplete

    tmp = _build_index()
    try:
        provider = create_autocomplete("inverted")
        provider.add(["machine learning", "machine vision", "hello world"])
        autocomplete_app = create_app(open_dir(tmp), autocomplete=provider)
        transport = httpx.ASGITransport(app=autocomplete_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/autocomplete?q=mach")
            assert resp.status_code == 200
            body = resp.json()
            assert len(body["suggestions"]) >= 1
            assert "machine learning" in body["suggestions"]
    finally:
        for f in os.listdir(tmp):
            os.remove(os.path.join(tmp, f))
        os.rmdir(tmp)
