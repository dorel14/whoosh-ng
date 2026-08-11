"""NumPy-based vector provider for cosine similarity search.

Uses numpy for computation of cosine similarity between high-dimensional
vectors. numpy is an optional dependency.

Author: dorel14
Version: 2.0.0
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

import numpy as np  # pyright: ignore[reportMissingImports]

from whoosh.vector.base import VectorHit, VectorProvider


class NumpyProvider(VectorProvider):
    """Vector provider using NumPy for cosine similarity.

    Stores vectors in memory and computes cosine similarity for
    search. Uses numpy for vectorized computation.

    Attributes:
        _vectors: Dictionary mapping document IDs to their vectors
            and norms.
    """

    def __init__(self) -> None:
        self._vectors: dict[str, tuple[np.ndarray, float]] = {}

    def add(self, vectors: Iterable[tuple[str, Sequence[float]]]) -> None:
        """Add vectors to the provider.

        Args:
            vectors: Iterable of (doc_id, vector_values) pairs.
        """
        for doc_id, values in vectors:
            arr = np.asarray(values, dtype=np.float64)
            self._vectors[doc_id] = (arr, float(np.linalg.norm(arr)))

    def search(
        self,
        query_vector: Sequence[float],
        k: int = 10,
        filter_ids: Sequence[str] = (),
    ) -> list[VectorHit]:
        """Search for the k most similar vectors to the query vector.

        Args:
            query_vector: Query vector.
            k: Maximum number of results to return.
            filter_ids: If provided, restricts search to these IDs.

        Returns:
            List of VectorHit sorted by descending score.
        """
        if not self._vectors:
            return []

        query = np.asarray(query_vector, dtype=np.float64)
        query_norm = np.linalg.norm(query)
        if query_norm == 0:
            return []

        results: list[VectorHit] = []
        allowed = set(filter_ids) if filter_ids else set()
        for doc_id, (vector, doc_norm) in self._vectors.items():
            if allowed and doc_id not in allowed:
                continue
            if doc_norm == 0:
                continue
            score = float(np.dot(vector, query) / (doc_norm * query_norm))
            if not math.isfinite(score):
                continue
            results.append(
                VectorHit(
                    doc_id=doc_id,
                    score=score,
                    vector=tuple(vector.tolist()),
                )
            )

        results.sort(key=lambda hit: hit.score, reverse=True)
        return results[:k]

    def remove(self, doc_ids: Iterable[str]) -> None:
        """Remove vectors from the provider.

        Args:
            doc_ids: Iterable of document IDs to remove.
        """
        for doc_id in doc_ids:
            self._vectors.pop(doc_id, None)
