"""Search-as-you-type field type.

Generates sub-fields for n-gram indexed text search.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any

from whoosh.fields import TEXT, Schema


class SEARCH_AS_YOU_TYPE(TEXT):  # noqa: N801
    """Field type for search-as-you-type.

    Generates sub-fields ``_2gram``, ``_3gram``, and ``_prefix`` by
    default. The main field stores the original text.

    Args:
        stored: Whether the field value is stored.
        kwargs: Additional keyword arguments forwarded to
            :class:`whoosh.fields.TEXT`.
    """

    def __init__(self, stored: bool = True, **kwargs: Any) -> None:
        """Initialize the search-as-you-type field.

        Args:
            stored: Whether the field value is stored in the index.
            **kwargs: Additional keyword arguments forwarded to
                :class:`whoosh.fields.TEXT`.
        """
        kwargs.setdefault("field_boost", 1.0)
        super().__init__(stored=stored, **kwargs)


__all__ = ["SEARCH_AS_YOU_TYPE"]
