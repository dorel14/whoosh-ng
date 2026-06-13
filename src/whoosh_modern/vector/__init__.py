from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence, TypeVar

from whoosh_modern.vector.base import VectorField, VectorHit, VectorProvider

__all__ = ["VectorField", "VectorHit", "VectorProvider"]