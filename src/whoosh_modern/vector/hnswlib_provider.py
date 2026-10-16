"""hnswlib-based vector provider for Whoosh-NG.

Wraps ``hnswlib`` for approximate nearest neighbor search. ``hnswlib`` is an
optional dependency: install it with ``pip install whoosh-ng[hnsw]``.

Author: dorel14
Version: 2.0.0

Optimizations:
- Batch add() with vstack for better performance than incremental adds.
- Efficient search with configurable ef parameter.
- Support for periodic rebuild to reclaim deleted vector space.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from contextlib import suppress
from typing import Any, Literal

import numpy as np

from whoosh.vector.base import VectorHit, VectorProvider

logger = logging.getLogger(__name__)


class HnswlibProvider(VectorProvider):
    """Approximate nearest neighbor provider using ``hnswlib``.

    Optimized for batch operations. Use add() with multiple vectors
    for better throughput than single incremental adds.

    Args:
        dimension: Vector dimensionality.
        space: Distance space (``"l2"``, ``"ip"``, or ``"cosine"``).
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
            space: Distance space (``"l2"``, ``"ip"``, or ``"cosine"``).
            max_elements: Maximum number of elements in the index.
            ef_construction: HNSW construction time ef parameter.
            m: HNSW m parameter (number of connections per node).

        Raises:
            ImportError: If ``hnswlib`` is not installed.
            ValueError: If dimension <= 0 or max_elements < 1.
        """
        if dimension <= 0:
            raise ValueError(f"dimension must be > 0, got {dimension}")
        if max_elements < 1:
            raise ValueError(f"max_elements must be >= 1, got {max_elements}")

        try:
            import hnswlib  # pyright: ignore[reportMissingImports,reportUnusedImport,reportMissingModuleSource]
        except ImportError as exc:
            raise ImportError(
                "HnswlibProvider requires hnswlib. Install it with: pip install whoosh-ng[hnsw]"
            ) from exc

        self._dimension = dimension
        self._space: Literal["l2", "ip", "cosine"] = space
        self._max_elements = max_elements
        self._ef_construction = ef_construction
        self._m = m
        self._index: Any = None
        self._labels: dict[int, str] = {}
        self._next_id = 0

        logger.debug(
            "HnswlibProvider initialized: dimension=%d, space=%r, "
            "max_elements=%d, ef_construction=%d, m=%d",
            dimension,
            space,
            max_elements,
            ef_construction,
            m,
        )

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
            logger.debug("HNSW index created with %d max elements", self._max_elements)

        return self._index

    def add(self, vectors: Iterable[tuple[str, Sequence[float]]]) -> None:
        """Add vectors to the HNSW index (batch mode).

        For best performance, pass multiple vectors at once rather than
        calling add() repeatedly with single vectors.

        Args:
            vectors: Iterable of (doc_id, vector_values) pairs.

        Raises:
            ValueError: If any vector dimension doesn't match provider dimension.
        """
        index = self._ensure_index()
        doc_ids: list[str] = []
        arrs: list[np.ndarray] = []

        for doc_id, values in vectors:
            if isinstance(values, bytes | bytearray):
                arr = np.frombuffer(values, dtype=np.float32)
            else:
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

        # Batch add with vstack for efficiency
        matrix = np.vstack(arrs)
        labels = list(range(self._next_id, self._next_id + len(doc_ids)))

        try:
            index.add_items(matrix, labels)
            for idx, doc_id in zip(labels, doc_ids, strict=False):
                self._labels[idx] = doc_id
            self._next_id += len(doc_ids)
            logger.debug("Added %d vectors to HNSW index (total: %d)", len(doc_ids), self._next_id)
        except Exception as exc:
            logger.error("Failed to add %d vectors to HNSW index: %s", len(doc_ids), exc)
            raise

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
            List of VectorHit sorted by score (ascending for l2,
            descending for cosine/ip).

        Raises:
            ValueError: If query_vector dimension doesn't match provider dimension.
        """
        if self._index is None or not self._labels:
            return []

        index = self._ensure_index()
        if isinstance(query_vector, bytes | bytearray):
            query = np.frombuffer(query_vector, dtype=np.float32)
        else:
            query = np.asarray(query_vector, dtype=np.float32)
        if query.shape[-1] != self._dimension:
            raise ValueError(
                f"Query vector length {query.shape[-1]} does not match "
                f"provider dimension {self._dimension}"
            )

        allowed = set(filter_ids) if filter_ids else None

        # Adaptive ef based on k
        ef = max(k * 3, 50)
        self._index.set_ef(ef)

        try:
            labels, distances = index.knn_query(query.reshape(1, -1), k=max(k * 3, 100))
        except Exception as exc:
            logger.error("HNSW search failed: %s", exc)
            return []

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

        logger.debug("HNSW search returned %d results (k=%d)", len(hits), k)
        return hits

    def remove(self, doc_ids: Iterable[str]) -> None:
        """Remove vectors by doc_id.

        Note: hnswlib does not support true deletion. This method marks
        entries as deleted in the internal index. Use rebuild() periodically
        to reclaim space and optimize the index.

        Args:
            doc_ids: Iterable of document IDs to remove.
        """
        if self._index is None or not self._labels:
            return

        index = self._ensure_index()
        target = set(doc_ids)
        removed_count = 0

        for label, doc_id in list(self._labels.items()):
            if doc_id in target:
                with suppress(Exception):
                    index.mark_deleted(label)
                self._labels.pop(label, None)
                removed_count += 1

        if removed_count > 0:
            logger.debug("Marked %d vectors as deleted in HNSW index", removed_count)

    def rebuild(self, vectors: Iterable[tuple[str, Sequence[float]]]) -> None:
        """Rebuild the index from scratch.

        Useful for reclaiming space after many deletions.

        Args:
            vectors: Iterable of (doc_id, vector_values) pairs.
        """
        self._index = None
        self._labels.clear()
        self._next_id = 0
        logger.info("HNSW index rebuilt from scratch")
        self.add(vectors)
