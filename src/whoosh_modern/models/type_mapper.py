"""Central registry mapping Python types to Whoosh field types.

This module provides :class:`TypeMapper`, the single canonical registry
mapping Python types, runtime values, and native dtype names to Whoosh field
types. All data sources and schema discovery utilities delegate to it instead
of maintaining their own ``_map_*_dtype`` helpers.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

import datetime
import decimal
import enum
from collections.abc import Callable, Sequence
from typing import Any, TypeVar, get_args, get_origin

from whoosh.fields import BOOLEAN, DATETIME, ID, KEYWORD, NUMERIC, STORED, TEXT

from .types import SearchField, SearchOptions

T = TypeVar("T")


def _unwrap_annotated(annotation: Any) -> tuple[Any, list[Any]]:
    """Return (base_type, metadata) from an Annotated type.

    Args:
        annotation: A type annotation, possibly wrapped in ``Annotated``.

    Returns:
        A tuple of (base_type, metadata_list).
    """
    origin = get_origin(annotation)
    if origin is not None:
        try:
            import typing

            if origin is typing.Annotated:
                annotated_args = get_args(annotation)
                return annotated_args[0], list(annotated_args[1:])
        except Exception:
            pass
    return annotation, []


def _is_list_like(annotation: Any) -> bool:
    """Check whether the annotation represents a list-like type.

    Args:
        annotation: A type annotation.

    Returns:
        True if the annotation is ``list``, ``tuple``, or ``Sequence``.
    """
    origin = get_origin(annotation)
    return origin is list or origin is tuple or origin is Sequence


def _extract_search_options(annotation: Any, default: SearchOptions) -> SearchOptions:
    """Extract SearchOptions from an Annotated type's metadata.

    Args:
        annotation: A type annotation, possibly wrapped in ``Annotated``.
        default: Default SearchOptions to return if no SearchField is found.

    Returns:
        SearchOptions extracted from metadata or the default.
    """
    _, metadata = _unwrap_annotated(annotation)
    for item in metadata:
        if isinstance(item, SearchField):
            return item.options
    return default


def _unwrap_optional(annotation: Any) -> Any:
    """Strip ``None`` from an optional/union annotation.

    Args:
        annotation: A type annotation, possibly ``X | None`` or ``Union[X, None]``.

    Returns:
        The single non-``None`` member of the union, or the annotation itself.
    """
    import types as _types
    import typing

    origin = get_origin(annotation)
    if origin is typing.Union or origin is _types.UnionType:
        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(args) == 1:
            return args[0]
    return annotation


# Ordered substring rules used by :meth:`TypeMapper.map_dtype`. Order matters:
# "datetime64[ns]" must match DATETIME before "int"/"float" heuristics.
_DTYPE_RULES: list[tuple[tuple[str, ...], Callable[[SearchOptions], Any]]] = [
    (("bool",), lambda opt: BOOLEAN(stored=opt.stored)),
    (
        ("datetime", "timestamp", "date", "time"),
        lambda opt: DATETIME(stored=opt.stored, sortable=opt.sortable),
    ),
    (("uuid",), lambda opt: ID(stored=opt.stored, unique=opt.unique)),
    (("json", "enum", "array", "list"), lambda opt: KEYWORD(stored=opt.stored)),
    (("char", "text", "str", "utf"), lambda opt: TEXT(stored=opt.stored)),
    (
        ("float", "double", "real", "decimal", "numeric"),
        lambda opt: NUMERIC(float, stored=opt.stored, sortable=opt.sortable),  # pyright: ignore[reportArgumentType]
    ),
    (
        ("int", "auto", "serial", "long", "short"),
        lambda opt: NUMERIC(int, stored=opt.stored, sortable=opt.sortable),
    ),
]


def _default_mappings() -> None:
    """Register default Python-to-Whoosh type mappings."""
    TypeMapper.register(str, lambda opt: TEXT(stored=opt.stored, analyzer=opt.analyzer or None))
    TypeMapper.register(
        SearchField, lambda opt: TEXT(stored=opt.stored, analyzer=opt.analyzer or None)
    )
    TypeMapper.register(int, lambda opt: NUMERIC(int, stored=opt.stored, sortable=opt.sortable))
    TypeMapper.register(
        float,
        lambda opt: NUMERIC(float, stored=opt.stored, sortable=opt.sortable),  # pyright: ignore[reportArgumentType]
    )
    TypeMapper.register(bool, lambda opt: BOOLEAN(stored=opt.stored))
    TypeMapper.register(type(None), lambda opt: STORED)


class TypeMapper:
    """Central registry mapping Python types to Whoosh field types."""

    _registry: dict[Any, Callable[[SearchOptions], Any]] = {}

    @classmethod
    def register(cls, py_type: Any, factory: Callable[[SearchOptions], Any]) -> None:
        """Register a Python type -> Whoosh field factory mapping.

        Args:
            py_type: Python type to map.
            factory: Function that takes SearchOptions and returns a Whoosh field type.
        """
        cls._registry[py_type] = factory

    @classmethod
    def map(cls, py_type: Any, options: SearchOptions) -> Any:
        """Map a Python type to a Whoosh field type.

        Args:
            py_type: Python type to map.
            options: SearchOptions associated with the field.

        Returns:
            A Whoosh field type instance (TEXT, NUMERIC, etc.).
        """
        if py_type in cls._registry:
            return cls._registry[py_type](options)
        origin = get_origin(py_type)
        if origin is not None:
            if _is_list_like(py_type):
                return KEYWORD(
                    stored=options.stored,
                    sortable=options.sortable,
                )
            if origin is dict:
                return STORED
        if isinstance(py_type, type) and issubclass(py_type, enum.Enum):
            return KEYWORD(stored=options.stored, sortable=options.sortable)
        if isinstance(py_type, type) and issubclass(py_type, datetime.datetime):
            return DATETIME(stored=options.stored, sortable=options.sortable)
        if isinstance(py_type, type) and issubclass(py_type, datetime.date):
            return DATETIME(stored=options.stored, sortable=options.sortable)
        if isinstance(py_type, type) and issubclass(py_type, decimal.Decimal):
            return NUMERIC(
                int,
                stored=options.stored,
                sortable=options.sortable,
                decimal_places=2,
            )
        if isinstance(py_type, type) and py_type is bytes:
            return KEYWORD(stored=options.stored, sortable=options.sortable)
        return STORED

    @classmethod
    def map_annotation(cls, annotation: Any, options: SearchOptions | None = None) -> Any:
        """Map a (possibly ``Annotated``/``Optional``) annotation to a Whoosh field.

        Unwraps ``Annotated[...]`` metadata and optional/union annotations
        (``int | None``) before delegating to :meth:`map`.

        Args:
            annotation: A Python type annotation.
            options: SearchOptions to apply. Defaults to ``SearchOptions()``.

        Returns:
            A Whoosh field type instance.

        Example:
            >>> from whoosh.fields import NUMERIC
            >>> isinstance(TypeMapper.map_annotation(int | None), NUMERIC)
            True
        """
        opts = options if options is not None else SearchOptions()
        base, metadata = _unwrap_annotated(annotation)
        for item in metadata:
            if isinstance(item, SearchField):
                opts = item.options
        base = _unwrap_optional(base)
        return cls.map(base, opts)

    @classmethod
    def map_value(cls, value: Any, options: SearchOptions | None = None) -> Any:
        """Map a runtime Python value to a Whoosh field type instance.

        Args:
            value: A sample value taken from a document.
            options: SearchOptions to apply. Defaults to ``SearchOptions()``.

        Returns:
            A Whoosh field type instance. ``None`` and unknown values map to
            ``TEXT``; ``dict`` and ``list`` values map to ``KEYWORD``.
        """
        opts = options if options is not None else SearchOptions()
        if value is None:
            return TEXT(stored=opts.stored, analyzer=opts.analyzer or None)
        if isinstance(value, dict | list | tuple | set):
            return KEYWORD(stored=opts.stored, sortable=opts.sortable)
        mapped = cls.map(type(value), opts)
        if mapped is STORED:
            return TEXT(stored=opts.stored, analyzer=opts.analyzer or None)
        return mapped

    @classmethod
    def map_dtype(cls, dtype: Any, options: SearchOptions | None = None) -> Any:
        """Map a native dtype / column type name to a Whoosh field type.

        This is the canonical replacement for the per-data-source
        ``_map_pandas_dtype`` / ``_map_polars_dtype`` / ``_map_peewee_field``
        / ``_map_tortoise_field`` helpers. The dtype is converted to a
        lowercase string and matched against well-known substrings
        (``bool``, ``datetime``, ``float``, ``int``, ``char``...).

        Args:
            dtype: A dtype, column type, field instance or type name. It is
                converted with ``str()`` (or its class name when the object
                has no informative ``str``).
            options: SearchOptions to apply. Defaults to ``SearchOptions(stored=True)``
                since data sources always store discovered columns.

        Returns:
            A Whoosh field type instance (NUMERIC, BOOLEAN, DATETIME, ID,
            KEYWORD or TEXT).

        Example:
            >>> from whoosh.fields import NUMERIC
            >>> isinstance(TypeMapper.map_dtype("int64"), NUMERIC)
            True
        """
        opts = options if options is not None else SearchOptions(stored=True)
        name = cls._dtype_name(dtype)
        for keywords, factory in _DTYPE_RULES:
            if any(keyword in name for keyword in keywords):
                return factory(opts)
        return TEXT(stored=opts.stored, analyzer=opts.analyzer or None)

    @staticmethod
    def _dtype_name(dtype: Any) -> str:
        """Return a normalized lowercase name for a dtype-like object.

        Args:
            dtype: A dtype, type, field instance or string.

        Returns:
            A lowercase string usable for substring matching.
        """
        if isinstance(dtype, str):
            return dtype.lower()
        if isinstance(dtype, type):
            return dtype.__name__.lower()
        text = str(dtype).lower()
        if text.startswith("<") or not text:
            return type(dtype).__name__.lower()
        return text

    @classmethod
    def suggest_type(
        cls,
        current: str,
        usage: dict[str, Any] | None = None,
    ) -> str | None:
        """Suggest a more specific Whoosh field type name for a TEXT field.

        This is the canonical optimization rule shared by
        :meth:`whoosh_modern.schema_discovery.SchemaDiscovery.from_sample_optimized`
        and :meth:`whoosh_modern.schema_optimization.SchemaOptimizationReport._suggest_type`
        so that both can no longer diverge.

        Args:
            current: The current Whoosh field type name (e.g. ``"TEXT"``).
            usage: Optional usage statistics with keys such as ``doc_count``,
                ``unique_values``, ``is_id``, ``unique``, ``is_bool`` and
                ``is_datetime``.

        Returns:
            The suggested field type name (``"KEYWORD"``, ``"ID"``,
            ``"BOOLEAN"`` or ``"DATETIME"``), or ``None`` when the current
            type should be kept.
        """
        stats = usage or {}
        if current != "TEXT":
            return None
        if stats.get("is_bool", False):
            return "BOOLEAN"
        ratio = stats.get("unique_values", 0) / max(stats.get("doc_count", 1), 1)
        if ratio > 0.8:
            return "KEYWORD"
        if stats.get("is_id", False) and stats.get("unique", True):
            return "ID"
        if stats.get("is_datetime", False):
            return "DATETIME"
        return None


_default_mappings()
