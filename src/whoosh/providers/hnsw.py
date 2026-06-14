"""HNSW provider for vector search.

Requires hnswlib to be installed.
"""

from __future__ import annotations

import pickle
from typing import Any

try:
    import hnswlib
    import numpy as np
except ImportError as exc:
    raise ImportError(
        "HNSWProvider requires hnswlib and numpy. Install with: pip install whoosh-reloaded[hnsw]"
    ) from exc

from whoosh.vector.base import VectorHit, VectorProvider


class HNSWProvider(VectorProvider[tuple[np.ndarray, Any]]):
    """HNSW-based vector similarity provider.

    Uses hnswlib for approximate nearest neighbor search.
    """

    def __init__(self, dimension: int, space: str = "l2", max_elements: int = 10000):
        self.dimension = dimension
        self.space = space
        self.max_elements = max_elements
        self._index: hnswlib.Index | None = None
        self._labels: dict[int, str] = {}

    def _get_or_create_index(self) -> hnswlib.Index:
        if self._index is None:
            self._index = hnswlib.Index(space=self.space, dim=self.dimension)
            self._index.init_index(max_elements=self.max_elements, ef_construction=200, M=16)
        return self._index

    def add(self, vectors: list[tuple[str, Any]]) -> None:
        """Add vectors to the index.

        :param vectors: List of (doc_id, vector) tuples
        """
        index = self._get_or_create_index()
        for i, (doc_id, vec) in enumerate(vectors):
            if isinstance(vec, np.ndarray):
                index.add_items(vec.reshape(1, -1), [i])
            else:
                arr = np.array(vec, dtype=np.float32)
                index.add_items(arr.reshape(1, -1), [i])
            self._labels[i] = doc_id

    def search(
        self,
        query_vector: Any,
        k: int = 10,
        filter_ids: list[str] | None = None,
    ) -> list[VectorHit]:
        """Search for similar vectors.

        :param query_vector: Query vector
        :param k: Number of results to return
        :param filter_ids: Optional list of doc_ids to filter
        :returns: List of VectorHit with scores
        """
        if self._index is None:
            return []

        index = self._get_or_create_index()
        if isinstance(query_vector, np.ndarray):
            query = query_vector.reshape(1, -1)
        else:
            query = np.array(query_vector, dtype=np.float32).reshape(1, -1)

        labels, distances = index.knn_query(query, k=k)

        hits: list[VectorHit] = []
        for label, dist in zip(labels[0], distances[0]):
            doc_id = self._labels.get(int(label), "")
            if filter_ids is None or doc_id in filter_ids:
                hits.append(VectorHit(doc_id=doc_id, score=float(dist)))
        return hits

    def remove(self, doc_ids: list[str]) -> None:
        """Remove vectors by doc_ids.

        Note: hnswlib does not support efficient removal.
        For production, consider rebuilding the index periodically.
        """
        labels_to_remove = [i for i, doc_id in self._labels.items() if doc_id in doc_ids]
        for label in labels_to_remove:
            del self._labels[label]

    def save(self, path: str) -> None:
        """Save index to disk."""
        if self._index is not None:
            self._index.save_index(path)
            with open(f"{path}.labels", "wb") as f:
                pickle.dump(self._labels, f)

    def load(self, path: str) -> None:
        """Load index from disk."""
        self._index = hnswlib.Index(space=self.space, dim=self.dimension)
        self._index.load_index(path, max_elements=self.max_elements)
        with open(f"{path}.labels", "rb") as f:
            self._labels = pickle.load(f)


__all__ = ["HNSWProvider"]
