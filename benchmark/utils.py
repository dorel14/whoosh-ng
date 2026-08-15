"""Shared benchmark utilities for Whoosh-NG.

Author: dorel14
Version: 3.1.0
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BENCHMARK_DIR = ROOT / "benchmark"
PARQUET_PATH = BENCHMARK_DIR / "Datas" / "stock-stockunitelegale-parquet.parquet"

_COMMON_TEXT_FIELDS = [
    "denominationUniteLegale",
    "denominationUsuelle1UniteLegale",
    "denominationUsuelle2UniteLegale",
    "denominationUsuelle3UniteLegale",
    "activitePrincipaleUniteLegale",
    "nomUniteLegale",
    "prenom1UniteLegale",
]


def join_text_fields(
    document: Mapping[str, Any],
    fields: list[str] | None = None,
) -> str:
    """Join specified text fields from a document into a single string.

    Handles non-string values and empty/ falsy values by skipping them.

    Args:
        document: Source document as a dict.
        fields: List of field names to join. Defaults to common text fields.

    Returns:
        A single string joining all non-empty string values from the
        requested fields.
    """
    if fields is None:
        fields = _COMMON_TEXT_FIELDS
    return " ".join(
        str(value)
        for key, value in document.items()
        if key in fields and isinstance(value, str) and value
    )
