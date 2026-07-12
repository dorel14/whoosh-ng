from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from whoosh.vector.base import VectorField, VectorHit, VectorProvider


@dataclass(frozen=True)
class VectorQuery:
    vector: tuple[float, ...]
    k: int = 10
    filter_ids: Sequence[str] = ()


__all__ = ["VectorField", "VectorHit", "VectorProvider", "VectorQuery"]
