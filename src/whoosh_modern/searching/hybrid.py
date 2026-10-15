"""Hybrid search combining BM25 and vector similarity.

Fuses full-text search results with vector search results using
Reciprocal Rank Fusion (RRF) or weighted score merging. Supports both
external :class:`VectorProvider` backends and native Whoosh VECTOR
columns via :class:`VectorSearcher`.

Author: dorel14
Version: 2.0.0
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any

from whoosh.qparser import QueryParser
from whoosh.searching import Searcher
from whoosh.vector.base import VectorHit, VectorProvider
from whoosh_modern.searching.vector_searcher import VectorSearcher


@dataclass
class HybridResult:
    """A single result from a hybrid search.

    Attributes:
        doc_id: Unique document identifier.
        score: Final fused score.
        bm25_score: Raw BM25 score from the text search.
        vector_score: Raw vector similarity score.
        rank: Rank in the fused results (0-based).
        fields: Stored fields of the matching document.
    """

    doc_id: str
    score: float
    bm25_score: float
    vector_score: float
    rank: int
    fields: dict[str, object] = field(default_factory=dict)


class HybridSearcher:
    """Fuse BM25 text search with vector similarity search.

    Wraps a Whoosh :class:`Searcher` and either a :class:`VectorProvider`
    or a native VECTOR column to produce a unified ranking. Two fusion
    strategies are supported:

    * **weighted** — linear interpolation of normalized BM25 and vector
      scores: ``score = alpha * bm25_norm + (1 - alpha) * vector_norm``.
    * **rrf** — Reciprocal Rank Fusion: ``score = sum(1 / (k + rank_i))``
      over the two result lists.

    When ``vector_column`` is provided, vector search operates directly
    on the Whoosh index columns and fuses at the docnum level, avoiding
    expensive doc_id round-trips.

    Attributes:
        _searcher: The Whoosh searcher used for BM25 search.
        _vector_provider: The vector provider used for similarity search.
        _vector_column: Optional native VECTOR field name for column search.
        _vector_searcher: Native VectorSearcher when using column mode.
        _id_field: Stored field name that holds the unique document ID
            used to match Whoosh results with vector hits.
        _docnum_to_id: Cache mapping docnum -> doc_id for the current
            searcher.
        _id_to_docnum: Cache mapping doc_id -> docnum for fast field
            lookup.
    """

    def __init__(
        self,
        searcher: Searcher,
        vector_provider: VectorProvider | None = None,
        id_field: str = "id",
        *,
        vector_column: str | None = None,
    ) -> None:
        """Initialize the hybrid searcher.

        Args:
            searcher: An open Whoosh :class:`Searcher`.
            vector_provider: A :class:`VectorProvider` populated with the
                same documents (using the same ``id_field`` values as
                doc_ids). Required unless ``vector_column`` is provided.
            id_field: Name of the stored field that uniquely identifies
                a document. Defaults to ``"id"``.
            vector_column: Optional name of a native VECTOR field in the
                index schema. When set, uses :class:`VectorSearcher` for
                direct column-based vector search.
        """
        self._searcher = searcher
        self._vector_provider = vector_provider
        self._id_field = id_field
        self._vector_column = vector_column
        self._vector_searcher: VectorSearcher | None = None
        self._docnum_to_id: dict[int, str] = {}
        self._id_to_docnum: dict[str, int] = {}
        self._build_id_mapping()

        if vector_column is not None:
            if vector_column not in searcher.schema:
                raise ValueError(f"Vector column {vector_column!r} not found in schema")
            self._vector_searcher = VectorSearcher(searcher.reader(), vector_column)

    def _build_id_mapping(self) -> None:
        """Build docnum <-> doc_id mapping from the searcher's stored fields."""
        reader = self._searcher.reader()
        for docnum in reader.all_doc_ids():
            fields = reader.stored_fields(docnum)
            if fields and self._id_field in fields:
                doc_id = str(fields[self._id_field])
                self._docnum_to_id[docnum] = doc_id
                self._id_to_docnum[doc_id] = docnum

    def _doc_id_for(self, docnum: int) -> str | None:
        """Return the doc_id for a given docnum, if known."""
        return self._docnum_to_id.get(docnum)

    def search(
        self,
        query: str | Any,
        query_vector: Sequence[float] | None = None,
        limit: int = 10,
        alpha: float = 0.5,
        method: str = "weighted",
        rrf_k: int = 60,
        vector_k: int = 10,
        **kwargs: Any,
    ) -> list[HybridResult]:
        """Run a hybrid search and return fused results.

        Args:
            query: Text query for BM25 search, or a pre-parsed Query object.
            query_vector: Optional query vector for vector search. If
                ``None``, only BM25 results are used.
            limit: Maximum number of fused results to return.
            alpha: Weight for BM25 scores in ``"weighted"`` mode.
                ``vector_weight = 1 - alpha``. Must be in ``[0, 1]``.
            method: Fusion strategy. Either ``"weighted"`` or ``"rrf"``.
            rrf_k: Constant ``k`` used in RRF scoring. Defaults to 60.
            vector_k: Number of vector search results to retrieve before
                fusion.
            **kwargs: Additional keyword arguments forwarded to
                ``Searcher.search()``.

        Returns:
            List of :class:`HybridResult` sorted by descending fused score.

        Raises:
            ValueError: If ``method`` is not ``"weighted"`` or ``"rrf"``.
            ValueError: If ``alpha`` is not in ``[0, 1]``.
        """
        if method not in ("weighted", "rrf"):
            raise ValueError(f"Unknown fusion method: {method!r}")
        if not (0.0 <= alpha <= 1.0):
            raise ValueError(f"alpha must be in [0, 1], got {alpha}")

        schema = self._searcher.schema
        parser = QueryParser(schema.names()[0] if schema else "content", schema)
        parsed_query = parser.parse(query) if isinstance(query, str) else query

        bm25_results = self._searcher.search(parsed_query, limit=limit, **kwargs)

        if self._vector_column and self._vector_searcher is not None:
            return self._search_native(
                bm25_results, query_vector, limit, alpha, method, rrf_k, vector_k
            )

        return self._search_provider(
            bm25_results, query_vector, limit, alpha, method, rrf_k, vector_k
        )

    def _search_provider(
        self,
        bm25_results: Any,
        query_vector: Sequence[float] | None,
        limit: int,
        alpha: float,
        method: str,
        rrf_k: int,
        vector_k: int,
    ) -> list[HybridResult]:
        """Provider-based vector search: fuse by doc_id."""
        vector_hits: list[VectorHit] = []
        if query_vector is not None and self._vector_provider is not None:
            vector_hits = self._vector_provider.search(query_vector, k=vector_k)

        if not bm25_results and not vector_hits:
            return []

        bm25_map: dict[str, tuple[float, int]] = {}
        for rank, hit in enumerate(bm25_results):
            doc_id = self._doc_id_for(hit.docnum)
            if doc_id is not None:
                score = float(hit.score) if hit.score is not None else 0.0
                bm25_map[doc_id] = (score, rank)

        vector_map: dict[str, tuple[float, int]] = {}
        for rank, hit in enumerate(vector_hits):
            vector_map[hit.doc_id] = (hit.score, rank)

        return self._fuse_by_doc_id(bm25_map, vector_map, limit, alpha, method, rrf_k)

    def _search_native(
        self,
        bm25_results: Any,
        query_vector: Sequence[float] | None,
        limit: int,
        alpha: float,
        method: str,
        rrf_k: int,
        vector_k: int,
    ) -> list[HybridResult]:
        """Native column-based vector search: fuse by docnum."""
        if self._vector_searcher is None:
            return []

        vector_hits: list[tuple[int, float]] = []
        if query_vector is not None:
            vector_hits = self._vector_searcher.search(query_vector, k=vector_k)

        if not bm25_results and not vector_hits:
            return []

        bm25_scores: dict[int, tuple[float, int]] = {}
        for rank, hit in enumerate(bm25_results):
            score = float(hit.score) if hit.score is not None else 0.0
            bm25_scores[hit.docnum] = (score, rank)

        vector_scores: dict[int, tuple[float, int]] = {}
        for rank, (docnum, score) in enumerate(vector_hits):
            vector_scores[docnum] = (score, rank)

        return self._fuse_by_docnum(bm25_scores, vector_scores, limit, alpha, method, rrf_k)

    def _fuse_by_doc_id(
        self,
        bm25_map: dict[str, tuple[float, int]],
        vector_map: dict[str, tuple[float, int]],
        limit: int,
        alpha: float,
        method: str,
        rrf_k: int,
    ) -> list[HybridResult]:
        """Fuse score maps keyed by doc_id."""
        all_doc_ids = set(bm25_map) | set(vector_map)

        norm_bm25 = norm_vector = (0.0, 1.0)
        if method == "weighted":
            norm_bm25 = self._normalize(bm25_map.values())
            norm_vector = self._normalize(vector_map.values())
        bm25_min, bm25_max = norm_bm25
        vec_min, vec_max = norm_vector

        fused: list[HybridResult] = []
        for doc_id in all_doc_ids:
            bm25_score, bm25_rank = bm25_map.get(doc_id, (0.0, -1))
            vector_score, vector_rank = vector_map.get(doc_id, (0.0, -1))

            if method == "rrf":
                score = 0.0
                if bm25_rank >= 0:
                    score += 1.0 / (rrf_k + bm25_rank)
                if vector_rank >= 0:
                    score += 1.0 / (rrf_k + vector_rank)
            else:
                bm25_norm = self._min_max_scale(bm25_score, bm25_min, bm25_max)
                vector_norm = self._min_max_scale(vector_score, vec_min, vec_max)
                score = alpha * bm25_norm + (1.0 - alpha) * vector_norm

            fields = self._fields_for(doc_id)
            fused.append(
                HybridResult(
                    doc_id=doc_id,
                    score=score,
                    bm25_score=bm25_score,
                    vector_score=vector_score,
                    rank=0,
                    fields=fields,
                )
            )

        fused.sort(key=lambda r: r.score, reverse=True)
        for i, result in enumerate(fused[:limit]):
            result.rank = i
        return fused[:limit]

    def _fuse_by_docnum(
        self,
        bm25_scores: dict[int, tuple[float, int]],
        vector_scores: dict[int, tuple[float, int]],
        limit: int,
        alpha: float,
        method: str,
        rrf_k: int,
    ) -> list[HybridResult]:
        """Fuse score maps keyed by docnum (native column path)."""
        all_docnums = set(bm25_scores) | set(vector_scores)

        norm_bm25 = norm_vector = (0.0, 1.0)
        if method == "weighted":
            norm_bm25 = self._normalize(bm25_scores.values())
            norm_vector = self._normalize(vector_scores.values())
        bm25_min, bm25_max = norm_bm25
        vec_min, vec_max = norm_vector

        fused: list[HybridResult] = []
        searcher = self._searcher
        for docnum in all_docnums:
            bm25_score, bm25_rank = bm25_scores.get(docnum, (0.0, -1))
            vector_score, vector_rank = vector_scores.get(docnum, (0.0, -1))

            if method == "rrf":
                score = 0.0
                if bm25_rank >= 0:
                    score += 1.0 / (rrf_k + bm25_rank)
                if vector_rank >= 0:
                    score += 1.0 / (rrf_k + vector_rank)
            else:
                bm25_norm = self._min_max_scale(bm25_score, bm25_min, bm25_max)
                vector_norm = self._min_max_scale(vector_score, vec_min, vec_max)
                score = alpha * bm25_norm + (1.0 - alpha) * vector_norm

            fields = dict(searcher.stored_fields(docnum)) if searcher.stored_fields(docnum) else {}
            doc_id = self._doc_id_for(docnum) or str(docnum)
            fused.append(
                HybridResult(
                    doc_id=doc_id,
                    score=score,
                    bm25_score=bm25_score,
                    vector_score=vector_score,
                    rank=0,
                    fields=fields,
                )
            )

        fused.sort(key=lambda r: r.score, reverse=True)
        for i, result in enumerate(fused[:limit]):
            result.rank = i
        return fused[:limit]

    def _normalize(self, scores: Iterable[tuple[float, int]]) -> tuple[float, float]:
        """Return (min, max) of the score values."""
        values = [s for s, _ in scores]
        if not values:
            return (0.0, 1.0)
        return (min(values), max(values))

    @staticmethod
    def _min_max_scale(value: float, min_val: float, max_val: float) -> float:
        """Scale ``value`` to ``[0, 1]`` using min-max normalization."""
        if max_val == min_val:
            return 0.5 if value == max_val else 0.0
        return (value - min_val) / (max_val - min_val)

    def _fields_for(self, doc_id: str) -> dict[str, object]:
        """Return stored fields for a given doc_id."""
        docnum = self._id_to_docnum.get(doc_id)
        if docnum is not None:
            fields = self._searcher.stored_fields(docnum)
            return dict(fields) if fields else {}
        return {}


__all__ = ["HybridSearcher", "HybridResult"]
