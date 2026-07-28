from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SearchOptions:
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
    """Descriptor that stores search metadata for model fields."""

    def __init__(self, **kwargs: Any) -> None:
        self.options = SearchOptions(**kwargs)
        self.name: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def __get__(self, obj: Any, objtype: type | None = None) -> Any:
        if obj is None:
            return self
        return getattr(obj, self.name, None)

    def __set__(self, obj: Any, value: Any) -> None:
        setattr(obj, self.name, value)
