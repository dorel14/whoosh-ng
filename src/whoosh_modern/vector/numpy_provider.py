from __future__ import annotations

import math
from typing import Iterable, Sequence

import numpy as np

from whoosh_modern.vector.base import VectorField, VectorHit, VectorProvider


class NumpyProvider(VectorProvider):
    def __init__(self) -> None:
        self._vectors: dict[str, np.ndarray] = {}

    def add(self, vectors: Iterable[tuple[str, Sequence[float]]]) -> None:
        for doc_id, values in vectors:
            self._vectors[doc_id] = np.asarray(values, dtype=np.float64)

    def search(
        self,
        query_vector: Sequence[float],
        k: int = 10,
        filter_ids: Sequence[str] = (),
    ) -> list[VectorHit]:
        if not self._vectors:
            return []

        query = np.asarray(query_vector, dtype=np.float64)
        query_norm = np.linalg.norm(query)
        if query_norm == 0:
            return []

        results: list[VectorHit] = []
        allowed = set(filter_ids) if filter_ids else set()
        for doc_id, vector in self._vectors.items():
            if allowed and doc_id not in allowed:
                continue
            doc_norm = np.linalg.norm(vector)
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
        for doc_id in doc_ids:
            self._vectors.pop(doc_id, None)
