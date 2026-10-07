"""Dense vector field type with native column storage and binary encoding.

Provides the VECTOR field type for storing embedding vectors efficiently
as packed binary blobs (float32 or float16) in a native Whoosh column,
dramatically reducing index size and serialization overhead.

When ``dimension`` is set, the field uses a :class:`VectorColumn` for
native per-document storage readable by :class:`VectorSearcher`.

Author: dorel14
Version: 2.0.0
"""

from __future__ import annotations

import numpy as np

from whoosh.fields.numeric import STORED

_DTYPE_MAP = {"float32": np.float32, "float16": np.float16}


class VECTOR(STORED):
    """Dense vector field for storing embedding vectors efficiently.

    Unlike a plain STORED field which pickles Python objects, VECTOR
    encourages storing vectors as packed binary blobs via
    :meth:`to_bytes`. When ``dimension`` is set, the field also uses a
    native :class:`~whoosh_modern.columns.VectorColumn` for direct
    column access by :class:`~whoosh_modern.searching.VectorSearcher`.

    Consumers (NumpyProvider, HnswlibProvider) accept both ``bytes`` and
    sequence inputs for backward compatibility.

    Args:
        stored: Whether the field value is stored in the index.
        dimension: Optional dimensionality of the vector. When set,
            the field uses a native VectorColumn for direct column access.
        dtype: Element dtype for binary storage: ``"float32"`` (default)
            or ``"float16"`` (half the storage, lower precision).
        normalized: If True, vectors are L2-normalized at storage time so
            that cosine similarity reduces to a dot product at query time.
    """

    def __init__(
        self,
        stored: bool = True,
        dimension: int | None = None,
        dtype: str = "float32",
        normalized: bool = False,
    ) -> None:
        super().__init__()
        if dtype not in _DTYPE_MAP:
            raise ValueError(f"Unsupported dtype: {dtype!r}. Use float32 or float16.")
        self.stored = stored
        self.dimension = dimension
        self.dtype = dtype
        self.normalized = normalized

        if dimension is not None:
            from whoosh_modern.columns import VectorColumn
            self.column_type = VectorColumn(
                dimension=dimension,
                dtype=dtype,
                normalized=normalized,
            )
        else:
            self.column_type = None

    def to_bytes(self, vector: object) -> bytes:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Encode a vector as a packed binary blob with validation.

        Args:
            vector: A sequence of floats or a numpy array.

        Returns:
            Packed binary representation (float32 or float16).

        Raises:
            ValueError: If the vector dimension does not match the field
                dimension (when set), is not 1-dimensional, contains
                non-finite values, or an unsupported dtype is configured.
        """
        arr = np.asarray(vector, dtype=_DTYPE_MAP[self.dtype])
        if arr.ndim != 1:
            raise ValueError(f"Vector must be 1-dimensional, got {arr.ndim}d")
        if self.dimension is not None and arr.shape[0] != self.dimension:
            raise ValueError(
                f"Vector dimension {arr.shape[0]} does not match "
                f"field dimension {self.dimension}"
            )
        if not np.all(np.isfinite(arr)):
            raise ValueError("Vector contains NaN or Inf values")
        if self.normalized:
            norm = np.linalg.norm(arr)
            if norm > 0:
                arr = arr / norm
        return arr.tobytes()

    def from_bytes(self, data: bytes) -> np.ndarray:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Decode a packed binary blob back into a numpy array.

        Args:
            data: Binary blob produced by :meth:`to_bytes`.

        Returns:
            NumPy array of the configured dtype.
        """
        return np.frombuffer(data, dtype=_DTYPE_MAP[self.dtype])

    def to_column_value(self, value: object) -> bytes:
        """Convert a vector value to the on-disk column representation.

        Args:
            value: A sequence of floats or a numpy array.

        Returns:
            Packed binary representation suitable for the VectorColumn.
        """
        return self.to_bytes(value)

    def from_column_value(self, value: bytes) -> np.ndarray:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Convert a raw column value back to a numpy array.

        Args:
            value: Raw bytes from the VectorColumn.

        Returns:
            NumPy array of the configured dtype.
        """
        return self.from_bytes(value)

