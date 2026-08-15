"""Term-based facet, a thin wrapper around :class:`whoosh.sorting.FieldFacet`.

It behaves exactly like a core ``FieldFacet`` (and therefore works as a
``groupedby=`` argument) while accepting the legacy ``limit`` and ``name``
keyword arguments.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any

from whoosh.sorting import FieldFacet


class TermsFacet(FieldFacet):
    """Term-based facet, a thin wrapper around :class:`whoosh.sorting.FieldFacet`.

    It behaves exactly like a core ``FieldFacet`` (and therefore works as a
    ``groupedby=`` argument) while accepting the legacy ``limit`` and ``name``
    keyword arguments.

    Attributes:
        limit: Maximum number of terms to report for this facet.
        name: Optional display name for the facet.
    """

    def __init__(
        self,
        fieldname: str = "",
        limit: int = 100,
        name: str | None = None,
        *,
        reverse: bool = False,
        allow_overlap: bool = False,
        maptype: Any = None,
    ) -> None:
        """Initialize a TermsFacet.

        Args:
            fieldname: Name of the field to facet on.
            limit: Maximum number of terms to report (default: 100).
            name: Optional display name for the facet.
            reverse: Reverse the sort order of this facet.
            allow_overlap: Allow documents to appear in multiple groups.
            maptype: Optional core ``FacetMap`` type.
        """
        super().__init__(
            fieldname,
            reverse=reverse,
            allow_overlap=allow_overlap,
            maptype=maptype,
        )
        self.limit = limit
        self.name = name or fieldname
