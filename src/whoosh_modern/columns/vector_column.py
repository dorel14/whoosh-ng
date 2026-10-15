"""Vector column type for dense embedding storage.

Provides a fixed-length binary column optimized for storing dense
vectors (float32/float16) with optional L2 normalization.

Author: dorel14
Version: 1.0.0
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from whoosh.columns import Column, ColumnReader, ColumnWriter
from whoosh.system import emptybytes

if TYPE_CHECKING:
    pass


class VectorColumn(Column):
    """Fixed-length binary column for dense float vectors.

    Stores each vector as a packed binary blob of fixed size
    (dimension * dtype.itemsize). Supports float32 and float16.

    Args:
        dimension: Dimensionality of the vectors.
        dtype: Element dtype: ``"float32"`` (default) or ``"float16"``.
        normalized: If True, vectors are L2-normalized before storage so
            that cosine similarity reduces to a dot product at query time.
    """

    reversible = False

    def __init__(
        self,
        dimension: int,
        dtype: str = "float32",
        normalized: bool = False,
    ) -> None:
        if dtype not in ("float32", "float16"):
            raise ValueError(f"Unsupported dtype: {dtype!r}. Use float32 or float16.")
        self.dimension = dimension
        self.dtype = dtype
        self.normalized = normalized
        self._np_dtype = np.float32 if dtype == "float32" else np.float16
        self.itemsize = int(dimension * np.dtype(self._np_dtype).itemsize)
        self._default = emptybytes * self.itemsize

    def writer(self, dbfile):
        return self.Writer(
            dbfile,
            self.itemsize,
            self._default,
            self.dtype,
            self.normalized,
            self.dimension,
        )

    def reader(self, dbfile, basepos, length, doccount):
        return self.Reader(
            dbfile,
            basepos,
            length,
            doccount,
            self.itemsize,
            self._default,
            self.dtype,
            self.dimension,
        )

    def default_value(self, reverse=False) -> np.ndarray:
        return np.zeros(self.dimension, dtype=self._np_dtype)

    class Writer(ColumnWriter):
        def __init__(
            self,
            dbfile,
            itemsize: int,
            default: bytes,
            dtype: str,
            normalized: bool,
            dimension: int,
        ) -> None:
            self._dbfile = dbfile
            self._itemsize = itemsize
            self._default = self._defaultbytes = default
            self._dtype = dtype
            self._normalized = normalized
            self._dimension = dimension
            self._count = 0

        def fill(self, docnum: int) -> None:
            if docnum > self._count:
                for _ in range(docnum - self._count):
                    self._dbfile.write(self._defaultbytes)
                self._count = docnum

        def add(self, docnum: int, value) -> None:
            if isinstance(value, bytes):
                data = value
            else:
                np_dtype = np.float32 if self._dtype == "float32" else np.float16
                arr = np.asarray(value, dtype=np_dtype)
                if arr.ndim != 1:
                    raise ValueError(f"Vector must be 1-dimensional, got {arr.ndim}d")
                if arr.shape[0] != self._dimension:
                    raise ValueError(
                        f"Vector dimension {arr.shape[0]} does not match "
                        f"field dimension {self._dimension}"
                    )
                if not np.all(np.isfinite(arr)):
                    raise ValueError("Vector contains NaN or Inf values")
                if self._normalized:
                    norm = float(np.linalg.norm(arr))
                    if norm > 0:
                        arr = arr / norm
                data = arr.tobytes()
            if len(data) != self._itemsize:
                raise ValueError(
                    f"Packed vector size {len(data)} does not match expected {self._itemsize}"
                )
            if docnum > self._count:
                self.fill(docnum)
            self._dbfile.write(data)
            self._count = docnum + 1

        def finish(self, docnum: int) -> None:
            if self._count < docnum:
                for _ in range(docnum - self._count):
                    self._dbfile.write(self._defaultbytes)

    class Reader(ColumnReader):
        def __init__(
            self,
            dbfile,
            basepos: int,
            length: int,
            doccount: int,
            itemsize: int,
            default: bytes,
            dtype: str,
            dimension: int,
        ) -> None:
            self._dbfile = dbfile
            self._basepos = basepos
            self._length = length
            self._doccount = doccount
            self._itemsize = itemsize
            self._default = self._defaultbytes = default
            self._dtype = dtype
            self._dimension = dimension
            self._count = length // itemsize if itemsize else 0

        def __getitem__(self, docnum: int) -> bytes:
            if docnum >= self._count:
                return self._defaultbytes
            pos = self._basepos + self._itemsize * docnum
            return self._dbfile.get(pos, self._itemsize)

        def __iter__(self):
            count = self._count
            default = self._defaultbytes
            for i in range(self._doccount):
                if i < count:
                    yield self[i]
                else:
                    yield default


__all__ = ["VectorColumn"]
