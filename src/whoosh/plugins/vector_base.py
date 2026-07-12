from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Sequence

from whoosh.vector.base import VectorHit


class AsyncVectorProvider(ABC):
    """Asynchronous vector provider contract for plugins.

    Mirrors :class:`whoosh.vector.base.VectorProvider` but exposes coroutine
    methods so that vector backends using async I/O (e.g. Qdrant, Milvus over a
    network) can be integrated without blocking the event loop.
    """

    @abstractmethod
    async def aadd(self, vectors: Iterable[tuple[str, Sequence[float]]]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def asearch(
        self, query_vector: Sequence[float], k: int = 10, filter_ids: Sequence[str] = ()
    ) -> list[VectorHit]:
        raise NotImplementedError

    @abstractmethod
    async def aremove(self, doc_ids: Iterable[str]) -> None:
        raise NotImplementedError


__all__ = ["AsyncVectorProvider"]
