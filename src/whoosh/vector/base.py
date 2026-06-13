from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Generic, Iterable, Sequence, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class VectorHit:
    doc_id: str
    score: float
    vector: tuple[float, ...] = ()
    payload: dict[str, object] = field(default_factory=dict)


class VectorProvider(Generic[T]):
    def add(self, vectors: Iterable[tuple[str, Sequence[float]]]) -> None:
        raise NotImplementedError

    def search(self, query_vector: Sequence[float], k: int = 10, filter_ids: Sequence[str] = ()) -> list[VectorHit]:
        raise NotImplementedError

    def remove(self, doc_ids: Iterable[str]) -> None:
        raise NotImplementedError


class VectorField:
    def __init__(self, dimension: int, name: str = "") -> None:
        self.dimension = dimension
        self.name = name

    def vector_to_bytes(self, values: Sequence[float]) -> bytes:
        return struct.pack(f"{len(values)}d", *values)

    def bytes_to_vector(self, data: bytes) -> tuple[float, ...]:
        count = len(data) // 8
        return struct.unpack(f"{count}d", data)
