# type: ignore
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from whoosh.vector.base import VectorField, VectorHit, VectorProvider


@dataclass(frozen=True)
class VectorQuery:
    vector: tuple[float, ...]
    k: int = 10
    filter_ids: Sequence[str] = ()


__all__ = ["VectorField", "VectorHit", "VectorProvider", "VectorQuery"]
