"""Dense vector field type.

Author: dorel14
Version: 1.0.0
"""

from __future__ import annotations

from whoosh.fields.numeric import STORED


class VECTOR(STORED):
    """Dense vector field for storing embedding vectors.

    Behaves like :class:`whoosh.fields.numeric.STORED` but carries
    explicit semantics for dense embedding vectors. Values are stored
    as-is and are not indexed for full-text search.

    Args:
        stored: Whether the field value is stored in the index.
        dimension: Optional dimensionality of the vector. This is not
            enforced by Whoosh itself, but can be used by higher-level
            code or validation logic to ensure consistency.
    """

    def __init__(self, stored: bool = True, dimension: int | None = None) -> None:
        """Initialize the dense vector field.

        Args:
            stored: Whether the field value is stored in the index.
            dimension: Optional vector dimensionality for validation.
        """
        super().__init__()
        self.stored = stored
        self.dimension = dimension
