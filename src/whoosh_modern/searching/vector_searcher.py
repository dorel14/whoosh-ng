"""Native Whoosh vector searcher using VECTOR columns.

Reads dense vectors directly from Whoosh segment columns and performs
exact cosine similarity search using a single NumPy matrix product.

Author: dorel14
Version: 1.0.0
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

import numpy as np

from whoosh.reading import IndexReader

logger = logging.getLogger(__name__)


class VectorSearcher:
    """Search dense vectors stored in a Whoosh VECTOR column.

    Reads vectors from a segment column and builds an in-memory NumPy
    matrix for exact cosine similarity. The matrix is rebuilt on each
    :meth:`__init__` call to reflect the current index state.

    Top-k selection uses ``np.argpartition`` for O(N) complexity
    instead of a full sort.

    Attributes:
        _reader: The Whoosh index reader.
        _fieldname: Name of the VECTOR field.
        _column: The VectorColumn configuration.
        _matrix: Cached contiguous float32 matrix of all non-default vectors.
        _row_to_docnum: Maps matrix row index -> docnum for result mapping.
    """

    def __init__(self, reader: IndexReader, fieldname: str) -> None:
        """Initialize the vector searcher from an index reader.

        Args:
            reader: An open Whoosh :class:`~whoosh.reading.IndexReader`.
            fieldname: Name of the VECTOR field to search.
        """
        self._reader = reader
        self._fieldname = fieldname
        self._fieldobj = reader.schema[fieldname]  # type: ignore[reportAttributeAccessIssue]
        self._column = self._fieldobj.column_type
        self._matrix: np.ndarray | None = None
        self._row_to_docnum: list[int] = []
        self._build_matrix()

    def _build_matrix(self) -> None:
        """Build the in-memory matrix from the column reader."""
        try:
            creader = self._reader.column_reader(self._fieldname, self._column, translate=False)
        except NotImplementedError:
            self._matrix = np.array([], dtype=np.float32).reshape(0, self._column.dimension)
            self._row_to_docnum = []
            return
        n_docs = self._reader.doc_count_all()
        default_bytes = self._column._default
        np_dtype = np.float32 if self._column.dtype == "float32" else np.float16

        vectors: list[np.ndarray] = []
        row_to_docnum: list[int] = []

        for docnum in range(n_docs):
            if self._reader.is_deleted(docnum):
                continue
            raw = creader[docnum]
            if raw and raw != default_bytes:
                vec = np.frombuffer(raw, dtype=np_dtype)
                row_to_docnum.append(docnum)
                vectors.append(vec)

        if vectors:
            self._matrix = np.array(vectors, dtype=np.float32)
            self._row_to_docnum = row_to_docnum
        else:
            self._matrix = np.array([], dtype=np.float32).reshape(0, self._column.dimension)
            self._row_to_docnum = []

    def search(
        self,
        query_vector: Sequence[float],
        k: int = 10,
    ) -> list[tuple[int, float]]:
        """Search for the k most similar vectors to the query vector.

        Computes exact cosine similarity using a single matrix--vector
        product. Assumes vectors were L2-normalized at index time
        (``normalized=True`` on the VECTOR field).

        Args:
            query_vector: Query vector (sequence or packed float32 bytes).
            k: Maximum number of results to return.

        Returns:
            List of ``(docnum, score)`` tuples sorted by descending score.
        """
        if self._matrix is None or len(self._matrix) == 0:
            return []

        if isinstance(query_vector, bytes | bytearray):
            query = np.frombuffer(query_vector, dtype=np.float32)
        else:
            query = np.asarray(query_vector, dtype=np.float32)
        query_norm = float(np.linalg.norm(query))
        if query_norm == 0:
            logger.warning("Query vector has zero norm, returning empty results")
            return []
        query = query / query_norm

        scores = self._matrix @ query

        if k >= len(scores):
            top_indices = np.argsort(scores)[::-1]
        else:
            top_indices = np.argpartition(scores, -k)[-k:]
            top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]

        results: list[tuple[int, float]] = []
        for idx in top_indices:
            score = float(scores[idx])
            if score <= -np.inf or np.isnan(score):
                continue
            results.append((self._row_to_docnum[idx], score))
        return results


__all__ = ["VectorSearcher"]
