"""Dense vector field type.

Author: SoniqueBay Team
Version: 1.0.0
"""

from __future__ import annotations

from whoosh.fields.numeric import STORED


class VECTOR(STORED):
    """Dense vector field for storing embedding vectors.

    Behaves like :class:`whoosh.fields.numeric.STORED` but carries
    explicit semantics for dense embedding vectors. Values are stored
    as-is and are not indexed for full-text search.
    """
