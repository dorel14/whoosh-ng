from __future__ import annotations

import collections.abc
import os
import tempfile

import pytest

from whoosh.backends.abc import Backend
from whoosh.backends.file import FileBackend
from whoosh.backends.sqlite import SQLiteBackend
from whoosh.registry import BackendRegistry
from whoosh.fields import Schema, TEXT, ID, KEYWORD, STORED
from whoosh.index import EmptyIndexError


@pytest.fixture
def tmp_sqlite_path(tmp_path):
    return tmp_path / "test.db"


# ---------------------------------------------------------------------------
# ABC compliance
# ---------------------------------------------------------------------------


class ConcreteBackend(Backend):
    name = "concrete"

    def create(self, schema): ...
    def open(self, schema=None): ...
    def exists(self):
        return False


def test_backend_is_abstract() -> None:
    with pytest.raises(TypeError):
        Backend()


def test_concrete_backend_instantiable() -> None:
    b = ConcreteBackend()
    assert b.name == "concrete"


def test_backend_default_methods() -> None:
    b = ConcreteBackend()
    # destroy should raise NotImplementedError by default
    with pytest.raises(NotImplementedError):
        b.destroy()


# ---------------------------------------------------------------------------
# SQLiteBackend CRUD
# ---------------------------------------------------------------------------


def test_sqlite_create_and_exists(tmp_sqlite_path) -> None:
    backend = SQLiteBackend(tmp_sqlite_path)
    schema = Schema(title=TEXT, body=TEXT)
    ix = backend.create(schema)
    assert ix is not None
    assert backend.exists()
    # Fresh index is empty until documents are committed
    assert ix.is_empty()


def test_sqlite_round_trip(tmp_sqlite_path) -> None:
    backend = SQLiteBackend(tmp_sqlite_path)
    schema = Schema(title=TEXT(stored=True), body=TEXT, path=ID(stored=True))
    backend.create(schema)
    w = backend.writer()
    w.add_document(title="First", body="one two three", path="/a")
    w.add_document(title="Second", body="four five six", path="/b")
    w.commit()
    assert backend.doc_count() == 2

    r = backend.reader()
    fields = r.all_stored_fields()
    assert len(fields) == 2
    titles = {f["title"] for f in fields}
    assert titles == {"First", "Second"}
    assert r.stored_fields(1)["path"] == "/a"
    assert r.stored_fields(2)["path"] == "/b"
    r.close()


def test_sqlite_open_missing(tmp_sqlite_path) -> None:
    backend = SQLiteBackend(tmp_sqlite_path)
    with pytest.raises(EmptyIndexError):
        backend.open()


def test_sqlite_destroy(tmp_sqlite_path) -> None:
    backend = SQLiteBackend(tmp_sqlite_path)
    backend.create(Schema(title=TEXT))
    assert backend.exists()
    # Close connection before destroy to release file lock
    backend._conn.close() if backend._conn else None
    backend._conn = None
    backend.destroy()
    assert not backend.exists()


def test_sqlite_context_manager(tmp_sqlite_path) -> None:
    backend = SQLiteBackend(tmp_sqlite_path)
    with backend:
        ix = backend.create(Schema(title=TEXT(stored=True)))
        w = backend.writer()
        w.add_document(title="ctx")
        w.commit()
    backend = SQLiteBackend(tmp_sqlite_path)
    assert backend.doc_count() == 1


def test_sqlite_fts_columns_in_schema() -> None:
    backend = SQLiteBackend(":memory:")
    schema = Schema(content=TEXT, tags=KEYWORD, title=ID(stored=True))
    backend.create(schema)
    ix = backend.open(schema)
    assert "content" in ix.schema
    assert "tags" in ix.schema
    assert "title" in ix.schema


def test_sqlite_optimize(tmp_sqlite_path) -> None:
    backend = SQLiteBackend(tmp_sqlite_path)
    backend.create(Schema(body=TEXT))
    w = backend.writer()
    for i in range(100):
        w.add_document(body=f"doc{i}")
        if i % 20 == 0:
            w.commit()
    w.commit()
    backend.optimize()
    assert backend.doc_count() == 100
