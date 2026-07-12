from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING, Any

from whoosh.backends.abc import Backend
from whoosh.fields import Schema, STORED, TEXT, KEYWORD, ID, NUMERIC, BOOLEAN, DATETIME
from whoosh.index import EmptyIndexError

if TYPE_CHECKING:
    pass

_FTS_READY_ERROR = (
    "SQLite FTS5 is not available in this build of Python/sqlite3. "
    "Please upgrade your Python (>=3.8 ships FTS5) or sqlite3 module."
)


def _sql_type_for(ftype_cls: type) -> str:
    if ftype_cls in (NUMERIC, DATETIME, BOOLEAN):
        return "REAL"
    return "TEXT"


def _encode_value(value: Any) -> Any:
    """Convert complex Python objects to SQLite-friendly primitives."""
    if isinstance(value, (dict, list, set, tuple)):
        return json.dumps(value, default=str)
    return value


def _decode_value(value: Any) -> Any:
    """Attempt to decode JSON-encoded values back to native types."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            pass
    return value


class _SQLiteIndex:
    """Minimal Index façade returned by :class:`SQLiteBackend`."""

    def __init__(self, backend: SQLiteBackend, schema: Schema) -> None:
        self.backend = backend
        self._schema = schema

    @property
    def schema(self) -> Schema:
        return self._schema

    def is_empty(self) -> bool:
        return self.backend.doc_count() == 0

    def close(self) -> None:
        pass

    def doc_count_all(self) -> int:
        return self.backend.doc_count()

    def doc_count(self) -> int:
        return self.backend.doc_count()

    def latest_generation(self) -> int:
        return 0

    def refresh(self):  # type: ignore[override]
        return self

    def up_to_date(self) -> bool:
        return True

    def last_modified(self) -> int:
        path = self.backend._path
        if isinstance(path, str) and path == ":memory:":
            return -1
        return path.stat().st_mtime_ns if path else -1

    def add_field(self, fieldname: str, fieldspec) -> None:  # type: ignore[override]
        raise NotImplementedError(
            "Adding fields to a SQLite-backed index requires full "
            "table reconstruction, which is not yet implemented. Recreate "
            "the index instead."
        )

    def remove_field(self, fieldname: str) -> None:  # type: ignore[override]
        raise NotImplementedError(
            "Removing fields from a SQLite-backed index requires full "
            "table reconstruction, which is not yet implemented. Recreate "
            "the index instead."
        )

    def reader(self, reuse=None):  # type: ignore[override]
        return self.backend.reader()

    def writer(self, **kwargs):  # type: ignore[override]
        return self.backend.writer()

    def optimize(self, **kwargs) -> None:  # type: ignore[override]
        self.backend.optimize()


class SQLiteReader:
    """Minimal IndexReader façade."""

    def __init__(self, backend: SQLiteBackend) -> None:
        self.backend = backend

    def doc_count_all(self) -> int:
        return self.backend.doc_count()

    def doc_count(self) -> int:
        return self.backend.doc_count()

    def all_stored_fields(self) -> list[dict[str, Any]]:
        return self.backend._all_stored_fields()

    def stored_fields(self, docnum: int) -> dict[str, Any] | None:
        return self.backend._stored_fields(docnum)

    def close(self) -> None:
        pass


class SQLiteWriter:
    """Accumulates documents in memory and flushes them to SQLite on commit."""

    def __init__(self, backend: SQLiteBackend) -> None:
        self.backend = backend
        self._docs: list[dict[str, Any]] = []

    def add_document(self, **fields: Any) -> None:
        doc: dict[str, Any] = {name: value for name, value in fields.items()}
        self._docs.append(doc)

    def delete_by_term(self, fieldname: str, text: str) -> None:  # type: ignore[override]
        raise NotImplementedError("delete_by_term not yet supported for SQLiteBackend")

    def delete_by_query(self, q) -> None:  # type: ignore[override]
        raise NotImplementedError("delete_by_query not yet supported for SQLiteBackend")

    def commit(self, optimize: bool = False) -> None:  # type: ignore[override]
        self.backend._commit(self._docs, optimize=optimize)
        self._docs = []

    def cancel(self) -> None:
        self._docs = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        if exc[0] is None:
            self.commit()
        else:
            self.cancel()
        return False


class SQLiteBackend(Backend):
    """SQLite + FTS5 full-text search backend.

    Stores the index (schema + documents) in a single SQLite database
    file and relies on the FTS5 extension for full-text search.

    FTS5-capable field types
    ------------------------
    * :class:`~whoosh.fields.TEXT`
    * :class:`~whoosh.fields.KEYWORD`

    All other field types (``ID``, ``NUMERIC``, ``DATETIME``,
    ``BOOLEAN``, ``STORED``) are stored as plain columns and remain
    retrievable but are not searchable through FTS5.

    Usage::

        from whoosh.backends.sqlite import SQLiteBackend
        backend = SQLiteBackend("myindex.db")
        ix = backend.create(schema)
    """

    name = "sqlite"

    def __init__(self, path: str | Path) -> None:
        # Keep ":memory:" as string for special handling; convert other paths
        if isinstance(path, str) and path == ":memory:":
            self._path: str | Path = path
        else:
            self._path = Path(path)
        self._conn: sqlite3.Connection | None = None
        self._schema: Schema | None = None

    def __repr__(self) -> str:
        return f"SQLiteBackend({self._path!r})"

    # -- lifecycle -------------------------------------------------------

    async def startup(self) -> None:
        self._connect()

    async def shutdown(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> SQLiteBackend:
        self._connect()
        return self

    def __exit__(self, *args) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # -- internal helpers ------------------------------------------------

    def _check_fts5(self) -> None:
        try:
            probe = sqlite3.connect(":memory:")
            probe.execute("CREATE VIRTUAL TABLE _fts5_check USING fts5(x)")
            probe.execute("DROP TABLE _fts5_check")
            probe.close()
        except sqlite3.OperationalError as exc:
            raise RuntimeError(_FTS_READY_ERROR) from exc

    def _connect(self) -> None:
        self._check_fts5()
        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA busy_timeout=5000")

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._connect()
        return self._conn  # type: ignore[return-value]

    def _ensure_schema_table(self) -> None:
        con = self._get_conn()
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS _whoosh_schema (
                fieldname  TEXT PRIMARY KEY,
                fieldtype  TEXT NOT NULL,
                stored     INTEGER NOT NULL DEFAULT 1
            )
            """
        )

    def _fts_columns(self, schema: Schema | None = None) -> list[str]:
        schema = schema or self._schema
        if schema is None:
            return []
        return [name for name, ftype in schema.items() if isinstance(ftype, (TEXT, KEYWORD))]

    def _ensure_doc_table(self, schema: Schema) -> None:
        con = self._get_conn()
        fts_cols = self._fts_columns(schema)
        all_names = list(schema.names())

        col_defs = ", ".join(f'"{n}" {_sql_type_for(type(schema[n]))}' for n in all_names)
        col_defs += ", _rowid INTEGER PRIMARY KEY AUTOINCREMENT"
        con.execute(f"CREATE TABLE IF NOT EXISTS documents ({col_defs})")
        con.commit()

        if fts_cols:
            fts_content = ", ".join(fts_cols)
            con.execute(
                f"CREATE VIRTUAL TABLE IF NOT EXISTS _fts USING fts5({fts_content}, content='documents', content_rowid='_rowid')"
            )
            fts_quoted = ", ".join(f'"{n}"' for n in fts_cols)
            new_expr = ", ".join(f"new.{n}" for n in fts_cols)
            old_expr = ", ".join(f"old.{n}" for n in fts_cols)
            con.execute(
                f"""
                CREATE TRIGGER IF NOT EXISTS _ai
                AFTER INSERT ON documents BEGIN
                    INSERT INTO _fts(rowid, {fts_quoted})
                    VALUES (new._rowid, {new_expr});
                END
                """
            )
            con.execute(
                f"""
                CREATE TRIGGER IF NOT EXISTS _ad
                AFTER DELETE ON documents BEGIN
                    INSERT INTO _fts(_fts, rowid, {fts_quoted})
                    VALUES ('delete', old._rowid, {old_expr});
                END
                """
            )
            con.commit()

    def _save_schema(self, schema: Schema) -> None:
        con = self._get_conn()
        con.execute("DELETE FROM _whoosh_schema")
        rows = [
            (
                name,
                type(ftype).__name__,
                1 if (ftype is STORED or getattr(ftype, "stored", False)) else 0,
            )
            for name, ftype in schema.items()
        ]
        con.executemany(
            "INSERT INTO _whoosh_schema(fieldname, fieldtype, stored) VALUES (?,?,?)", rows
        )
        con.commit()

    def _load_schema(self) -> Schema | None:
        con = self._get_conn()
        cur = con.execute("SELECT fieldname, fieldtype FROM _whoosh_schema")
        rows = cur.fetchall()
        if not rows:
            return None
        field_map = {
            "TEXT": TEXT,
            "KEYWORD": KEYWORD,
            "ID": ID,
            "NUMERIC": NUMERIC,
            "DATETIME": DATETIME,
            "BOOLEAN": BOOLEAN,
            "STORED": STORED,
        }
        schema = Schema()
        for name, ftype_name in rows:
            ftype_cls = field_map.get(ftype_name)
            if ftype_cls is None or ftype_cls is STORED:
                schema.add(name, STORED)
            else:
                schema.add(name, ftype_cls(stored=True))
        return schema

    # -- index CRUD -------------------------------------------------------

    def create(self, schema: Schema) -> _SQLiteIndex:
        # Close existing connection before unlinking to release file lock
        if self._conn is not None:
            self._conn.close()
            self._conn = None
        path_exists = self._path.exists() if not isinstance(self._path, str) else False
        if path_exists:
            try:
                self._path.unlink()
            except (PermissionError, OSError):
                pass  # File may be locked on Windows
        self._ensure_schema_table()
        self._ensure_doc_table(schema)
        self._save_schema(schema)
        self._schema = schema
        return _SQLiteIndex(self, schema)

    def open(self, schema: Schema | None = None) -> _SQLiteIndex:
        # For in-memory databases, skip file existence check
        if (
            not (isinstance(self._path, str) and self._path == ":memory:")
            and not self._path.exists()
        ):
            raise EmptyIndexError(f"No Whoosh (SQLite) index found at {self._path!r}")
        self._connect()
        # For :memory: databases, use the schema already in memory if available
        if isinstance(self._path, str) and self._path == ":memory:" and self._schema is not None:
            schema = schema or self._schema
        else:
            loaded = self._load_schema()
            if loaded is None:
                raise EmptyIndexError(f"Index at {self._path!r} has no schema")
            schema = schema or loaded
        self._ensure_doc_table(schema)
        self._schema = schema
        return _SQLiteIndex(self, schema)

    def exists(self) -> bool:
        if isinstance(self._path, str) and self._path == ":memory:":
            return self._conn is not None
        if not self._path.exists():
            return False
        try:
            con = sqlite3.connect(str(self._path))
            cur = con.execute("SELECT COUNT(*) FROM _whoosh_schema")
            count = cur.fetchone()[0]
            con.close()
            return count > 0
        except Exception:
            return False

    def destroy(self) -> None:
        # Close connection first to release file lock
        if self._conn is not None:
            self._conn.close()
            self._conn = None
        # :memory: databases have no file to destroy
        if isinstance(self._path, str) and self._path == ":memory:":
            return
        if self._path.exists():
            try:
                self._path.unlink()
            except (PermissionError, OSError):
                pass  # File may be locked on Windows

    # -- reader / writer factories ----------------------------------------

    def reader(self) -> SQLiteReader:
        return SQLiteReader(self)

    def writer(self) -> SQLiteWriter:
        return SQLiteWriter(self)

    # -- misc helpers -----------------------------------------------------

    def doc_count(self) -> int:
        con = self._get_conn()
        try:
            cur = con.execute("SELECT COUNT(*) FROM documents")
            return cur.fetchone()[0]
        except sqlite3.OperationalError:
            return 0

    def _all_stored_fields(self) -> list[dict[str, Any]]:
        con = self._get_conn()
        cur = con.execute("SELECT * FROM documents")
        return [dict(row) for row in cur.fetchall()]

    def _stored_fields(self, docnum: int) -> dict[str, Any] | None:
        con = self._get_conn()
        cur = con.execute("SELECT * FROM documents WHERE _rowid = ?", (docnum,))
        row = cur.fetchone()
        return dict(row) if row else None

    def optimize(self) -> None:
        con = self._get_conn()
        con.execute("VACUUM")
        con.commit()

    # -- commits ----------------------------------------------------------

    def _commit(
        self,
        docs: list[dict[str, Any]],
        optimize: bool = False,
    ) -> None:
        if not docs or self._schema is None:
            return
        con = self._get_conn()
        all_fields = list(self._schema.names())
        placeholders = ", ".join(["?"] * len(all_fields))
        insert_sql = f"INSERT INTO documents ({', '.join(all_fields)}) VALUES ({placeholders})"
        for doc in docs:
            values = [_encode_value(doc.get(f)) for f in all_fields]
            con.execute(insert_sql, values)
        con.commit()
        if optimize:
            con.execute("VACUUM")
            con.commit()


from whoosh.registry import BackendRegistry  # noqa: E402

BackendRegistry.register("sqlite", SQLiteBackend, "whoosh")
