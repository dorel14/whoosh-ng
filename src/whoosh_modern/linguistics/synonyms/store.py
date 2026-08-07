"""SQLite-backed persistent synonym store."""

from __future__ import annotations

import sqlite3


class SQLiteSynonymStore:
    """Persistent synonym store backed by SQLite.

    Uses a simple table with (word, synonym) primary key.
    """

    def __init__(self, path: str) -> None:
        self._path = path
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS synonyms (
                word TEXT NOT NULL,
                synonym TEXT NOT NULL,
                PRIMARY KEY (word, synonym)
            )
            """
        )
        self._conn.commit()

    def get_synonyms(self, word: str) -> list[str]:
        cur = self._conn.execute("SELECT synonym FROM synonyms WHERE word = ?", (word,))
        return [row["synonym"] for row in cur.fetchall()]

    def add_synonym(self, word: str, synonyms: list[str]) -> None:
        for syn in synonyms:
            self._conn.execute(
                "INSERT OR IGNORE INTO synonyms (word, synonym) VALUES (?, ?)",
                (word, syn),
            )
        self._conn.commit()

    def remove_synonym(self, word: str, synonym: str) -> None:
        self._conn.execute(
            "DELETE FROM synonyms WHERE word = ? AND synonym = ?",
            (word, synonym),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
