"""FacetManager with auto-discovery and manual override capabilities.

This module re-exports the *real* core facet types from :mod:`whoosh.sorting`
(``FieldFacet``, ``RangeFacet``, ``DateRangeFacet``) instead of redefining
incompatible stubs. ``TermsFacet`` is a thin :class:`whoosh.sorting.FieldFacet`
subclass that additionally accepts a ``limit`` keyword for backward
compatibility. Consequently, every facet produced by :class:`FacetManager` is a
genuine core ``FacetType`` and can be passed directly to
``searcher.search(query, groupedby=...)``.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from whoosh.sorting import DateRangeFacet, FieldFacet, RangeFacet

from .manager import FacetManager
from .terms import TermsFacet

__all__ = (
    "DateRangeFacet",
    "Facet",
    "FacetManager",
    "FieldFacet",
    "RangeFacet",
    "TermsFacet",
)

#: Default numeric range used when auto-discovering a NUMERIC field.
DEFAULT_NUMERIC_START: int = 0
DEFAULT_NUMERIC_END: int = 1000
DEFAULT_NUMERIC_GAP: int = 100

#: Default date range used when auto-discovering a DATETIME field.
DEFAULT_DATE_START = __import__("datetime").datetime(1970, 1, 1)  # noqa: DTZ001
DEFAULT_DATE_END = __import__("datetime").datetime(2100, 1, 1)  # noqa: DTZ001
DEFAULT_DATE_GAP = __import__("datetime").timedelta(days=365)

#: Default maximum number of terms reported for a terms facet.
DEFAULT_TERMS_LIMIT: int = 100
