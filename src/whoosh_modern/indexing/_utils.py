"""Shared internal helpers for the ``whoosh_modern.indexing`` package.

This module holds helpers that were previously duplicated verbatim between
``modern_builder.py`` and ``parallel_builder.py``:

- :func:`_rmtree_retry`: Windows-safe recursive directory removal.
- :func:`_build_segment_worker`: process-pool worker building one isolated
  index segment from a batch of documents.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

import gc
import os
import shutil
import time
from typing import TYPE_CHECKING, Any

from whoosh.index import create_in

if TYPE_CHECKING:
    from whoosh.fields import Schema

__all__ = ["_build_segment_worker", "_rmtree_retry"]


def _rmtree_retry(path: str, retries: int = 20, delay: float = 0.5) -> None:
    """Remove a directory tree, retrying on Windows permission errors.

    On Windows, files created by worker processes can remain briefly
    locked after the process pool shuts down. Retrying with small
    delays avoids spurious failures in tests and cleanup paths.

    Args:
        path: Path to the directory tree to remove.
        retries: Maximum number of retry attempts. Defaults to 20.
        delay: Delay in seconds between retries. Defaults to 0.5.

    Example:
        >>> _rmtree_retry("/tmp/does-not-exist", retries=1)
    """
    for attempt in range(retries):
        try:
            shutil.rmtree(path)
            return
        except PermissionError:
            if attempt < retries - 1:
                time.sleep(delay)


def _build_segment_worker(args: tuple[str, Schema, list[dict[str, Any]], int]) -> str:
    """Build a single index segment in a separate process.

    Args:
        args: A tuple of ``(temp_dir, schema, docs, docbase)`` where
            ``temp_dir`` is the output directory, ``schema`` is the Whoosh
            schema, ``docs`` is the list of document dicts, and ``docbase``
            is the starting document ID (unused in this implementation).

    Returns:
        The path to the written segment directory.

    Raises:
        Exception: Any error raised while adding documents or committing;
            the writer is cancelled before the error propagates.
    """
    temp_dir, schema, docs, _docbase = args
    # ``create_in`` does not create the target directory itself, so it must
    # exist before the segment's on-disk index is created.
    os.makedirs(temp_dir, exist_ok=True)
    ix = create_in(temp_dir, schema)
    writer = ix.writer(limitmb=128, multisegment=True)
    try:
        for _doc in docs:
            writer.add_document(**_doc)
        writer.commit(merge=False)
    except Exception:
        writer.cancel()
        raise
    finally:
        # Break reference cycles before dropping references so the cyclic
        # GC can reclaim the writer and its open file handles on Windows.
        del writer
        del ix
        gc.collect()
    return temp_dir
