"""Backward-compatibility shim for the former ``models/base.py`` module.

The original ``TypeMapper`` and ``ModelIndex`` classes were split into
dedicated modules for maintainability. This file re-exports them so that
existing imports continue to work unchanged:

.. deprecated::
    Import :class:`TypeMapper` from :mod:`whoosh_modern.models.type_mapper`
    and :class:`ModelIndex` from :mod:`whoosh_modern.models.model_index`
    in new code.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from whoosh_modern.models.model_index import ModelIndex
from whoosh_modern.models.type_mapper import TypeMapper

__all__ = [
    "ModelIndex",
    "TypeMapper",
]
