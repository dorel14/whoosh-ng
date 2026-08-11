"""Search field metadata types.

Defines :class:`SearchOptions` (a dataclass encapsulating per-field search
configuration) and :class:`SearchField` (a descriptor that associates search
metadata with a model attribute).

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SearchOptions:
    """Configuration options for a searchable model field.

    These options control how an individual model attribute is mapped to a
    Whoosh field type and what indexing behaviour is applied.

    Attributes:
        fulltext: Whether the field should be full-text indexed (``True``
            maps to a ``TEXT`` Whoosh field).
        stored: Whether the field value should be stored in the index so it
            can be retrieved without accessing the original object.
        sortable: Whether the field should be sortable in search results.
        faceted: Whether the field should be usable for faceted search.
        id: Whether the field is an identifier (``ID`` Whoosh field).
        multi: Whether the field supports multi-valued content (``KEYWORD``).
        nullable: Whether the field value may be ``None``.
        analyzer: Name of a custom analyzer to apply (empty string means the
            default analyzer is used).
        unique: Whether the field value must be unique across documents.
    """

    fulltext: bool = False
    stored: bool = False
    sortable: bool = False
    faceted: bool = False
    id: bool = False
    multi: bool = False
    nullable: bool = False
    analyzer: str = ""
    unique: bool = False


class SearchField:
    """Descriptor that stores search metadata for model fields.

    When a :class:`SearchField` is placed on a model class, it captures the
    attribute name (via ``__set_name__``) and holds a
    :class:`SearchOptions` instance describing how the field should be
    indexed in Whoosh. The descriptor forwards ``__get__`` and ``__set__``
    to the underlying instance attribute.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the SearchField with search options.

        Args:
            **kwargs: Keyword arguments forwarded to
                :class:`SearchOptions` (e.g. ``fulltext=True``,
                ``stored=True``).
        """
        self.options = SearchOptions(**kwargs)
        self.name: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        """Store the attribute name assigned to this descriptor.

        Args:
            owner: The class that owns the descriptor.
            name: The attribute name under which the descriptor was assigned.
        """
        self.name = name

    def __get__(self, obj: Any, objtype: type | None = None) -> Any:
        """Retrieve the value of the underlying attribute.

        When accessed on the class (i.e. ``obj`` is ``None``), returns the
        :class:`SearchField` instance itself so that type-introspection code
        can read ``.options``.

        Args:
            obj: The instance accessing the descriptor, or ``None`` when
                accessed on the class.
            objtype: The class that owns the descriptor.

        Returns:
            The :class:`SearchField` descriptor when accessed on the class,
            or the value of the underlying instance attribute otherwise.
        """
        if obj is None:
            return self
        return getattr(obj, self.name, None)

    def __set__(self, obj: Any, value: Any) -> None:
        """Set the value of the underlying attribute.

        Args:
            obj: The instance on which to set the value.
            value: The value to assign to the underlying attribute.
        """
        setattr(obj, self.name, value)
