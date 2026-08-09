"""Runtime-checkable protocols for model introspection.

Defines lightweight :class:`typing.Protocol` classes used by
:class:`~whoosh_modern.models.base.ModelIndex` and the various ORM
integration modules to detect structural conformance of model classes
without requiring a shared base class.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class HasFields(Protocol):
    """Protocol for models that expose field definitions.

    Models conforming to this protocol provide a ``model_fields`` mapping
    (commonly found on Pydantic ``BaseModel`` subclasses and SQLModel
    instances). The :class:`~whoosh_modern.models.base.ModelIndex` uses
    this protocol to introspect field annotations and metadata when
    constructing a Whoosh schema.
    """

    model_fields: dict[str, Any]


@runtime_checkable
class HasInfo(Protocol):
    """Protocol for columns/fields that carry search metadata in ``.info``.

    Models or column objects conforming to this protocol expose an ``info``
    dictionary that may contain a ``"search"`` key with search-related
    configuration. The SQLAlchemy and SQLModel integration modules use this
    protocol to extract per-column indexing options.
    """

    info: dict[str, Any]
