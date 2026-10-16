"""NumPy-based vector provider for exact cosine similarity search.

Stores vectors in memory and computes exact cosine similarity via a single
matrix--vector product at query time. This is the **reference exact
baseline** for vector search: correct and useful for benchmarking
approximate methods (HNSW, FAISS), but not intended to scale to 10M+
vectors.

Author: dorel14
Version: 4.0.2

Notes:
- Cosine similarity is computed with one ``matrix @ query`` product.
- Top-k selection uses ``np.argpartition`` (O(N) vs full sort).
- Vectors are appended to ordered lists; the contiguous matrix is rebuilt
  lazily on first search after additions (full rebuild, not incremental).
- ``filter_ids`` uses a doc_id->row index map (O(matched) not O(N)).
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence

import numpy as np  # pyright: ignore[reportMissingImports]

from whoosh.vector.base import VectorHit, VectorProvider

logger = logging.getLogger(__name__)


class NumpyProvider(VectorProvider):
    """Exact vector provider using NumPy for cosine similarity.

    Stores all vectors in memory and computes exact cosine similarity at
    query time. The contiguous matrix is rebuilt (from all stored vectors)
    lazily on the first search after vectors are added.

    This is a reference implementation for benchmarking, not a scalable ANN
    index. For large corpora, prefer HNSW or FAISS.

    Attributes:
        _doc_ids: Ordered document IDs (matrix row order).
        _vectors: List of float32 arrays, one per document.
        _norms: List of precomputed L2 norms.
        _doc_index: doc_id -> row index for fast filtering.
        _matrix: Cached contiguous float32 matrix built at search time.
        _norms_arr: Cached float32 array of norms.
        _consolidation_needed: Whether the matrix must be rebuilt.
    """

    def __init__(self) -> None:
        self._doc_ids: list[str] = []
        self._vectors: list[np.ndarray] = []
        self._norms: list[float] = []
        self._doc_index: dict[str, int] = {}
        self._matrix: np.ndarray | None = None
        self._norms_arr: np.ndarray | None = None
        self._consolidation_needed = False

    def _consolidate_matrix(self) -> None:
        """Rebuild the contiguous matrix from all stored vectors.

        Deferred until search time to amortize the cost of matrix building.
        This is a full rebuild of all vectors, not an incremental append.
        """
        if not self._consolidation_needed:
            return

        if not self._vectors:
            self._matrix = None
            self._norms_arr = None
            self._doc_ids = []
            self._consolidation_needed = False
            return

        # Full rebuild: stack every stored vector into a contiguous matrix.
        self._matrix = np.asarray(self._vectors, dtype=np.float32)
        self._norms_arr = np.asarray(self._norms, dtype=np.float32)
        self._doc_index = {doc_id: i for i, doc_id in enumerate(self._doc_ids)}
        self._consolidation_needed = False
        logger.debug("Matrix consolidated: %d vectors", len(self._doc_ids))

    def _ensure_matrix(self) -> None:
        """Ensure matrix is built and up-to-date."""
        if self._consolidation_needed:
            self._consolidate_matrix()

    def add(self, vectors: Iterable[tuple[str, Sequence[float]]]) -> None:
        """Add vectors to the provider.

        Accepts ``Sequence[float]`` or packed ``bytes`` (float32). Vectors
        are stored with precomputed L2 norm for fast cosine scoring. The
        matrix is NOT rebuilt immediately; it is consolidated at the next
        ``search()`` call.

        Args:
            vectors: Iterable of (doc_id, vector_values) pairs.
        """
        for doc_id, values in vectors:
            if isinstance(values, bytes | bytearray):
                arr = np.frombuffer(values, dtype=np.float32)
            else:
                arr = np.asarray(values, dtype=np.float32)
            norm = float(np.linalg.norm(arr))
            self._doc_ids.append(doc_id)
            self._vectors.append(arr)
            self._norms.append(norm)
        self._doc_index = {d: i for i, d in enumerate(self._doc_ids)}
        self._consolidation_needed = True

    def search(
        self,
        query_vector: Sequence[float],
        k: int = 10,
        filter_ids: Sequence[str] = (),
    ) -> list[VectorHit]:
        """Search for the k most similar vectors to the query vector.

        Args:
            query_vector: Query vector (sequence or packed float32 bytes).
            k: Maximum number of results to return.
            filter_ids: If provided, restricts search to these IDs.

        Returns:
            List of VectorHit sorted by descending score.
        """
        if not self._vectors:
            return []

        self._ensure_matrix()
        matrix = self._matrix
        norms = self._norms_arr
        if matrix is None or norms is None or len(self._doc_ids) == 0:
            return []

        if isinstance(query_vector, bytes | bytearray):
            query = np.frombuffer(query_vector, dtype=np.float32)
        else:
            query = np.asarray(query_vector, dtype=np.float32)
        query_norm = np.linalg.norm(query)
        if query_norm == 0:
            logger.warning("Query vector has zero norm, returning empty results")
            return []

        # Exact cosine similarity: (A . B) / (||A|| * ||B||)
        scores = (matrix @ query) / (norms * query_norm)

        allowed = set(filter_ids) if filter_ids else None
        if allowed is not None:
            allowed_idx = [self._doc_index[d] for d in allowed if d in self._doc_index]
            if not allowed_idx:
                return []
            sub_scores = scores[allowed_idx]
            sub_doc_ids = [self._doc_ids[i] for i in allowed_idx]
            if k >= len(sub_scores):
                order = np.argsort(sub_scores)[::-1]
            else:
                order = np.argpartition(sub_scores, -k)[-k:]
                order = order[np.argsort(sub_scores[order])[::-1]]
            return [
                VectorHit(doc_id=sub_doc_ids[i], score=float(sub_scores[i]))
                for i in order
                if sub_scores[i] > -np.inf
            ]

        # Handle NaN and inf
        scores[np.isnan(scores)] = -np.inf
        scores[np.isinf(scores)] = -np.inf

        # Top-k selection (O(N) via argpartition, not full sort)
        if k >= len(scores):
            top_indices = np.argsort(scores)[::-1]
        else:
            top_indices = np.argpartition(scores, -k)[-k:]
            top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]

        results: list[VectorHit] = []
        for idx in top_indices:
            score = float(scores[idx])
            if score <= -np.inf:
                continue
            results.append(VectorHit(doc_id=self._doc_ids[idx], score=score))
        return results

    def remove(self, doc_ids: Iterable[str]) -> None:
        """Remove vectors from the provider.

        Args:
            doc_ids: Iterable of document IDs to remove.
        """
        removed = 0
        for doc_id in doc_ids:
            if doc_id in self._doc_index:
                removed += 1
        if removed == 0:
            return
        keep = [d for d in self._doc_ids if d not in set(doc_ids)]
        keep_set = set(keep)
        self._doc_ids = keep
        self._vectors = [
            v for d, v in zip(self._doc_ids, self._vectors, strict=True) if d in keep_set
        ]
        self._norms = [n for d, n in zip(self._doc_ids, self._norms, strict=True) if d in keep_set]
        self._doc_index = {d: i for i, d in enumerate(self._doc_ids)}
        self._matrix = None
        self._norms_arr = None
        self._consolidation_needed = True
        logger.debug("Removed %d vectors from provider", removed)
