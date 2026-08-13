"""hnswlib-based vector provider for Whoosh-NG.

Wraps ``hnswlib`` for approximate nearest neighbor search. ``hnswlib`` is an
optional dependency: install it with ``pip install whoosh-ng[hnsw]``.

Author: dorel14
Version: 1.0.0
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from contextlib import suppress
from typing import Any, Literal

import numpy as np

from whoosh.vector.base import VectorHit, VectorProvider


class HnswlibProvider(VectorProvider):
    """Approximate nearest neighbor provider using ``hnswlib``.

    Args:
        dimension: Vector dimensionality.
        space: Distance space (``"l2"`` or ``"cosine"``).
        max_elements: Maximum number of elements in the index.
        ef_construction: HNSW construction time ef parameter.
        m: HNSW m parameter (number of connections per node).
    """

    def __init__(
        self,
        dimension: int,
        space: Literal["l2", "ip", "cosine"] = "l2",
        max_elements: int = 10000,
        ef_construction: int = 200,
        m: int = 16,
    ) -> None:
        """Initialize the HNSW provider.

        Args:
            dimension: Vector dimensionality.
            space: Distance space (``"l2"`` or ``"cosine"``).
            max_elements: Maximum number of elements in the index.
            ef_construction: HNSW construction time ef parameter.
            m: HNSW m parameter (number of connections per node).

        Raises:
            ImportError: If ``hnswlib`` is not installed.
        """
        try:
            import hnswlib  # pyright: ignore[reportMissingImports,reportUnusedImport,reportMissingModuleSource]
        except ImportError as exc:
            raise ImportError(
                "HnswlibProvider requires hnswlib. "
                "Install it with: pip install whoosh-ng[hnsw]"
            ) from exc
        self._dimension = dimension
        self._space: Literal["l2", "ip", "cosine"] = space
        self._max_elements = max_elements
        self._ef_construction = ef_construction
        self._m = m
        self._index: Any = None
        self._labels: dict[int, str] = {}
        self._next_id = 0

    def _ensure_index(self) -> Any:
        """Lazily create the underlying ``hnswlib`` index.

        Returns:
            The initialized ``hnswlib.Index`` instance.
        """
        if self._index is None:
            import hnswlib  # pyright: ignore[reportMissingImports,reportMissingModuleSource]

            self._index = hnswlib.Index(space=self._space, dim=self._dimension)
            self._index.init_index(
                max_elements=self._max_elements,
                ef_construction=self._ef_construction,
                M=self._m,
            )
        return self._index

    def add(self, vectors: Iterable[tuple[str, Sequence[float]]]) -> None:
        """Add vectors to the HNSW index.

        Args:
            vectors: Iterable of (doc_id, vector_values) pairs.
        """
        index = self._ensure_index()
        doc_ids: list[str] = []
        arrs: list[np.ndarray] = []
        for doc_id, values in vectors:
            arr = np.asarray(values, dtype=np.float32)
            if arr.shape[-1] != self._dimension:
                raise ValueError(
                    f"Vector length {arr.shape[-1]} does not match "
                    f"provider dimension {self._dimension}"
                )
            doc_ids.append(doc_id)
            arrs.append(arr)
        if not arrs:
            return
        matrix = np.vstack(arrs)
        labels = list(range(self._next_id, self._next_id + len(doc_ids)))
        index.add_items(matrix, labels)
        for idx, doc_id in zip(labels, doc_ids, strict=False):
            self._labels[idx] = doc_id
        self._next_id += len(doc_ids)

    def search(
        self,
        query_vector: Sequence[float],
        k: int = 10,
        filter_ids: Sequence[str] = (),
    ) -> list[VectorHit]:
        """Search for the k nearest neighbors of the query vector.

        Args:
            query_vector: Query vector.
            k: Maximum number of results to return.
            filter_ids: If provided, restricts search to these doc_ids.

        Returns:
            List of VectorHit sorted by descending score (distance for l2,
            similarity for cosine).
        """
        if self._index is None:
            return []
        index = self._ensure_index()
        query = np.asarray(query_vector, dtype=np.float32)
        if query.shape[-1] != self._dimension:
            raise ValueError(
                f"Query vector length {query.shape[-1]} does not match "
                f"provider dimension {self._dimension}"
            )
        allowed = set(filter_ids) if filter_ids else None
        self._index.set_ef(max(k, 50))
        labels, distances = index.knn_query(query.reshape(1, -1), k=k * 3)
        hits: list[VectorHit] = []
        for label, distance in zip(labels[0], distances[0], strict=False):
            doc_id = self._labels.get(int(label))
            if doc_id is None:
                continue
            if allowed is not None and doc_id not in allowed:
                continue
            score = float(distance)
            hits.append(VectorHit(doc_id=doc_id, score=score))
            if len(hits) >= k:
                break
        return hits

    def remove(self, doc_ids: Iterable[str]) -> None:
        """Remove vectors by doc_id.

        Note:
            ``hnswlib`` does not support true deletion. This method marks
            entries as deleted in the internal index. Periodic ``rebuild()``
            is recommended to reclaim space.
        """
        if self._index is None:
            return
        index = self._ensure_index()
        target = set(doc_ids)
        for label, doc_id in list(self._labels.items()):
            if doc_id in target:
                with suppress(Exception):
                    index.mark_deleted(label)
                self._labels.pop(label, None)

    def rebuild(self, vectors: Iterable[tuple[str, Sequence[float]]]) -> None:
        """Rebuild the index from scratch.

        Args:
            vectors: Iterable of (doc_id, vector_values) pairs.
        """
        self._index = None
        self._labels.clear()
        self._next_id = 0
        self.add(vectors)
