"""SQLite-backed persistent synonym store.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

import sqlite3


class SQLiteSynonymStore:
    """Persistent synonym store backed by SQLite.

    Uses a simple table with (word, synonym) primary key.
    """

    def __init__(self, path: str) -> None:
        """Initialize the store and connect to a SQLite database.

        Creates the synonyms table if it does not already exist.

        Args:
            path: Filesystem path to the SQLite database file.
        """
        self._path = path
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        """Create the synonyms table if it does not exist."""
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
        """Return all synonyms stored for the given word.

        Args:
            word: The term whose synonyms should be retrieved.

        Returns:
            A list of synonym terms associated with ``word``.
        """
        cur = self._conn.execute("SELECT synonym FROM synonyms WHERE word = ?", (word,))
        return [row["synonym"] for row in cur.fetchall()]

    def add_synonym(self, word: str, synonyms: list[str]) -> None:
        """Add synonyms for the given word.

        Duplicate (word, synonym) pairs are silently ignored.

        Args:
            word: The term to associate synonyms with.
            synonyms: The list of synonym terms to add.
        """
        for syn in synonyms:
            self._conn.execute(
                "INSERT OR IGNORE INTO synonyms (word, synonym) VALUES (?, ?)",
                (word, syn),
            )
        self._conn.commit()

    def remove_synonym(self, word: str, synonym: str) -> None:
        """Remove a specific synonym for the given word.

        Args:
            word: The term whose synonym should be removed.
            synonym: The synonym term to remove.
        """
        self._conn.execute(
            "DELETE FROM synonyms WHERE word = ? AND synonym = ?",
            (word, synonym),
        )
        self._conn.commit()

    def close(self) -> None:
        """Close the underlying SQLite database connection."""
        self._conn.close()
