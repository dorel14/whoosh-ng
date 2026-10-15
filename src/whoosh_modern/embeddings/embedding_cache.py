"""Persistent on-disk cache for text embeddings (NumPy ``.npz`` format).

This lets an indexing run reuse embeddings computed in a previous run:
texts that are already present in the cache skip model inference entirely,
which can turn a re-index of an unchanged dataset into a pure write pass.

Auteur: SoniqueBay Team
Version: 1.0.0
"""

from __future__ import annotations

import os
from typing import Any

import numpy as np


class EmbeddingCache:
    """Load/save a ``{text: vector}`` mapping as a compressed NumPy archive.

    The archive stores two parallel arrays (``texts`` and ``vectors``) so that
    variable-length text keys are kept out of the numeric array. Vectors are
    stored as ``float32`` to match :class:`~whoosh_modern.fields.vector.VECTOR`
    storage.
    """

    @staticmethod
    def load(path: str) -> dict[str, np.ndarray]:
        """Load a cached mapping from disk.

        Args:
            path: Path to an ``.npz`` file previously written by :meth:`save`.

        Returns:
            A mapping from text to its ``float32`` embedding vector. Returns an
            empty dict when the file is missing or unreadable.
        """
        if not path or not os.path.exists(path):
            return {}
        try:
            data = np.load(path, allow_pickle=True)
        except (OSError, ValueError) as exc:
            import logging

            logging.getLogger(__name__).warning("EmbeddingCache.load failed for %s: %s", path, exc)
            return {}

        texts = data["texts"]
        vectors = data["vectors"]
        if texts.size == 0:
            return {}
        return {str(t): vectors[i] for i, t in enumerate(texts.tolist())}

    @staticmethod
    def save(path: str, cache: dict[str, Any]) -> None:
        """Persist a ``{text: vector}`` mapping to disk.

        Args:
            path: Destination ``.npz`` path. Parent directories are created.
            cache: Mapping from text to a vector (``ndarray`` or ``bytes`` blob).
        """
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        if not cache:
            empty_texts = np.empty((0,), dtype=object)
            empty_vecs = np.empty((0, 0), dtype=np.float32)
            np.savez(path, texts=empty_texts, vectors=empty_vecs)
            return

        texts = np.array(list(cache.keys()), dtype=object)
        vectors = np.stack(
            [
                np.asarray(v, dtype=np.float32)
                if isinstance(v, np.ndarray)
                else np.frombuffer(v, dtype=np.float32)
                for v in cache.values()
            ]
        ).astype(np.float32)
        np.savez(path, texts=texts, vectors=vectors)
