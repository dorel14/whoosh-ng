"""Storage middleware and pluggable storage providers (FS / SQLite / S3).

:class:`StorageMiddleware` routes index persistence through a
:class:`~whoosh.plugins.storage_base.SyncStorageProvider` so the writer does not
need to know the concrete backend. The actual segment routing is owned by
EPIC 4.5 (Storage Providers); here the middleware offers a functional,
backend-agnostic blob surface plus commit checkpoints so it can be wired into
the indexing pipeline without touching core code.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

import os
import sqlite3
import time
from typing import Any

from whoosh.middleware.base import Middleware
from whoosh.middleware.context import MiddlewareContext
from whoosh.plugins.storage_base import SyncStorageProvider


class FileStorageProvider(SyncStorageProvider):
    """Local filesystem storage provider.

    Keys are interpreted as relative paths under ``root`` (``/`` or ``\\`` are
    normalised to ``os.sep``). Intermediate directories are created on write.

    Args:
        root: Absolute or relative path to the root directory used as
            the storage root.
    """

    def __init__(self, root: str) -> None:
        self._root = os.path.abspath(root)

    @property
    def root(self) -> str:
        """Absolute root directory used by this provider.

        Returns:
            The absolute filesystem path of the storage root.
        """
        return self._root

    def _path(self, key: str) -> str:
        """Normalize *key* to an absolute filesystem path.

        Args:
            key: A blob key, possibly using ``/`` or ``\\`` separators.

        Returns:
            The absolute filesystem path corresponding to *key*.
        """
        safe = key.replace("\\", os.sep).replace("/", os.sep)
        return os.path.join(self._root, safe)

    def write(self, key: str, data: bytes) -> None:
        """Write *data* to the blob identified by *key*.

        Args:
            key: The blob key (relative path).
            data: Raw bytes to persist.

        Raises:
            OSError: If the underlying filesystem write fails.
        """
        path = self._path(key)
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(data)

    def read(self, key: str) -> bytes:
        """Read and return the blob identified by *key*.

        Args:
            key: The blob key (relative path).

        Returns:
            The raw bytes stored under *key*.

        Raises:
            FileNotFoundError: If no blob exists at *key*.
        """
        with open(self._path(key), "rb") as fh:
            return fh.read()

    def delete(self, key: str) -> None:
        """Delete the blob identified by *key*.

        Args:
            key: The blob key (relative path).

        Raises:
            FileNotFoundError: If no blob exists at *key*.
        """
        path = self._path(key)
        if os.path.exists(path):
            os.remove(path)

    def exists(self, key: str) -> bool:
        """Check whether a blob exists for *key*.

        Args:
            key: The blob key (relative path).

        Returns:
            ``True`` if the blob exists, ``False`` otherwise.
        """
        return os.path.exists(self._path(key))

    def list_keys(self) -> list[str]:
        """List all blob keys currently stored.

        Returns:
            A sorted list of relative blob keys.
        """
        keys: list[str] = []
        if not os.path.isdir(self._root):
            return keys
        for current, _dirs, files in os.walk(self._root):
            for name in files:
                full = os.path.join(current, name)
                rel = os.path.relpath(full, self._root)
                keys.append(rel.replace(os.sep, "/"))
        return sorted(keys)


class SQLiteStorageProvider(SyncStorageProvider):
    """SQLite-backed blob storage provider (stdlib ``sqlite3`` only).

    Args:
        path: Filesystem path to the SQLite database file.
        table: Name of the table used to store blobs.  The table is created
            automatically if it does not exist.
    """

    def __init__(self, path: str, table: str = "whoosh_blobs") -> None:
        self._path = path
        self._table = table
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute(f"CREATE TABLE IF NOT EXISTS {table} (key TEXT PRIMARY KEY, data BLOB)")
        self._conn.commit()

    def _execute(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        """Execute *sql* with *params* and commit immediately.

        Args:
            sql: The SQL statement to execute.
            params: Parameter tuple for placeholder substitution.

        Returns:
            The cursor resulting from the execution.
        """
        cur = self._conn.execute(sql, params)
        self._conn.commit()
        return cur

    def write(self, key: str, data: bytes) -> None:
        """Write *data* to the blob identified by *key*.

        Args:
            key: The blob key.
            data: Raw bytes to persist.
        """
        self._execute(
            f"INSERT OR REPLACE INTO {self._table} (key, data) VALUES (?, ?)",
            (key, data),
        )

    def read(self, key: str) -> bytes:
        """Read and return the blob identified by *key*.

        Args:
            key: The blob key.

        Returns:
            The raw bytes stored under *key*.

        Raises:
            KeyError: If no blob exists for *key*.
        """
        cur = self._conn.execute(f"SELECT data FROM {self._table} WHERE key = ?", (key,))
        row = cur.fetchone()
        if row is None:
            raise KeyError(f"Key '{key}' not found")
        return bytes(row[0])

    def delete(self, key: str) -> None:
        """Delete the blob identified by *key*.

        Args:
            key: The blob key.
        """
        self._execute(f"DELETE FROM {self._table} WHERE key = ?", (key,))

    def exists(self, key: str) -> bool:
        """Check whether a blob exists for *key*.

        Args:
            key: The blob key.

        Returns:
            ``True`` if the blob exists, ``False`` otherwise.
        """
        cur = self._conn.execute(f"SELECT 1 FROM {self._table} WHERE key = ? LIMIT 1", (key,))
        return cur.fetchone() is not None

    def list_keys(self) -> list[str]:
        """List all blob keys currently stored.

        Returns:
            A sorted list of blob keys.
        """
        cur = self._conn.execute(f"SELECT key FROM {self._table} ORDER BY key")
        return [row[0] for row in cur.fetchall()]

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        self._conn.close()


class S3StorageProvider(SyncStorageProvider):
    """S3 (or S3-compatible) blob storage provider.

    ``boto3`` is an optional dependency: it is imported lazily so the rest of
    Whoosh-NG does not require it. A ``client`` may be injected for testing.

    Args:
        bucket: Name of the S3 bucket to read from / write to.
        prefix: Optional key prefix applied to every blob key.  A single
            leading/trailing ``/`` is stripped.
        client: A pre-configured ``boto3`` S3 client.  When ``None`` (the
            default) a new client is created via ``boto3.client("s3")``.

    Raises:
        ImportError: If *client* is ``None`` and ``boto3`` is not installed.
    """

    def __init__(
        self,
        bucket: str,
        prefix: str = "",
        client: Any | None = None,
    ) -> None:
        self._bucket = bucket
        self._prefix = prefix.strip("/")
        if client is not None:
            self._client = client
        else:
            try:
                import boto3  # pyright: ignore[reportMissingImports]
            except ImportError as exc:
                raise ImportError(
                    "S3StorageProvider requires boto3. Install with: pip install whoosh-ng[s3]"
                ) from exc
            self._client = boto3.client("s3")

    def _key(self, key: str) -> str:
        """Prefix *key* with the configured prefix.

        Args:
            key: The raw blob key.

        Returns:
            The fully-qualified S3 object key.
        """
        return f"{self._prefix}/{key}" if self._prefix else key

    def write(self, key: str, data: bytes) -> None:
        """Write *data* to the S3 object identified by *key*.

        Args:
            key: The blob key.
            data: Raw bytes to persist.
        """
        self._client.put_object(Bucket=self._bucket, Key=self._key(key), Body=data)

    def read(self, key: str) -> bytes:
        """Read and return the S3 object identified by *key*.

        Args:
            key: The blob key.

        Returns:
            The raw bytes stored in the S3 object.

        Raises:
            botocore.exceptions.ClientError: If the object does not exist
                or is otherwise inaccessible.
        """
        resp = self._client.get_object(Bucket=self._bucket, Key=self._key(key))
        body: bytes = resp["Body"].read()
        return body

    def delete(self, key: str) -> None:
        """Delete the S3 object identified by *key*.

        Args:
            key: The blob key.
        """
        self._client.delete_object(Bucket=self._bucket, Key=self._key(key))

    def exists(self, key: str) -> bool:
        """Check whether an S3 object exists for *key*.

        Args:
            key: The blob key.

        Returns:
            ``True`` if the object exists, ``False`` otherwise.
        """
        try:
            self._client.head_object(Bucket=self._bucket, Key=self._key(key))
            return True
        except Exception:
            return False

    def list_keys(self) -> list[str]:
        """List all blob keys currently stored under the prefix.

        Returns:
            A sorted list of blob keys (with the configured prefix stripped).
        """
        keys: list[str] = []
        paginator = self._client.get_paginator("list_objects_v2")
        prefix = f"{self._prefix}/" if self._prefix else ""
        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                k = obj["Key"]
                keys.append(k[len(prefix) :] if prefix and k.startswith(prefix) else k)
        return sorted(keys)


class StorageMiddleware(Middleware):
    """Route index persistence through a pluggable storage provider.

    The middleware tags the indexing context with the active backend and writes
    a commit checkpoint on ``on_commit``, giving the pipeline a single storage
    integration point without modifying the writer.

    Args:
        provider: The :class:`SyncStorageProvider` that backs this middleware.
        name: Identifier used for commit checkpoint markers.
    """

    def __init__(self, provider: SyncStorageProvider, name: str = "storage") -> None:
        self._provider = provider
        self._name = name

    @property
    def provider(self) -> SyncStorageProvider:
        """The active storage provider.

        Returns:
            The :class:`SyncStorageProvider` instance backing this middleware.
        """
        return self._provider

    @property
    def name(self) -> str:
        """The middleware name.

        Returns:
            The identifier used for commit checkpoint markers.
        """
        return self._name

    def write(self, key: str, data: bytes) -> None:
        """Write *data* to the blob identified by *key* via the provider.

        Args:
            key: The blob key.
            data: Raw bytes to persist.
        """
        self._provider.write(key, data)

    def read(self, key: str) -> bytes:
        """Read and return the blob identified by *key* via the provider.

        Args:
            key: The blob key.

        Returns:
            The raw bytes stored under *key*.
        """
        return self._provider.read(key)

    def delete(self, key: str) -> None:
        """Delete the blob identified by *key* via the provider.

        Args:
            key: The blob key.
        """
        self._provider.delete(key)

    def exists(self, key: str) -> bool:
        """Check whether a blob exists for *key* via the provider.

        Args:
            key: The blob key.

        Returns:
            ``True`` if the blob exists, ``False`` otherwise.
        """
        return self._provider.exists(key)

    def list_keys(self) -> list[str]:
        """List all blob keys via the provider.

        Returns:
            A list of blob keys.
        """
        return self._provider.list_keys()

    def before_index(self, context: MiddlewareContext) -> MiddlewareContext:
        """Tag the indexing context with storage backend metadata.

        Args:
            context: The middleware context for the current indexing pass.

        Returns:
            The mutated context with ``storage_backend`` label and
            ``storage_provider`` metadata set.
        """
        context.labels["storage_backend"] = self._provider.__class__.__name__
        context.metadata["storage_provider"] = self
        return context

    def on_commit(self, context: MiddlewareContext) -> None:
        """Write a commit checkpoint marker to storage.

        Args:
            context: The middleware context for the current commit.
        """
        marker = f"commits/{self._name}/{int(time.time() * 1000)}"
        self._provider.write(marker, b"1")
        context.metadata["storage_commit_marker"] = marker


__all__ = [
    "FileStorageProvider",
    "SQLiteStorageProvider",
    "S3StorageProvider",
    "StorageMiddleware",
]
