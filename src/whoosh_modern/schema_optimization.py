"""Schema optimization report for Whoosh-NG.

Analyzes a schema against observed field usage and suggests type changes
that can improve index size and query performance.
"""

from __future__ import annotations

from collections import Counter
from typing import Any


class SchemaOptimizationReport:
    """Analyzes a schema and field usage to suggest optimizations.

    Example::

        report = SchemaOptimizationReport(schema, usage)
        print(report.text())
    """

    def __init__(self, schema: Any, usage: dict[str, dict[str, Any]] | None = None) -> None:
        self.schema = schema
        self.usage = usage or {}
        self._suggestions: list[dict[str, Any]] = []

    def analyze(self) -> list[dict[str, Any]]:
        suggestions = self._suggestions
        for fieldname, fieldobj in self.schema.items():
            usage = self.usage.get(fieldname, {})
            current = type(fieldobj).__name__
            suggested = self._suggest_type(fieldname, fieldobj, usage)
            if suggested and suggested != current:
                confidence = self._confidence(fieldname, fieldobj, usage)
                suggestions.append(
                    {
                        "field": fieldname,
                        "current": current,
                        "suggested": suggested,
                        "confidence": confidence,
                        "reason": self._reason(fieldname, fieldobj, usage, suggested),
                    }
                )
        self._suggestions = suggestions
        return suggestions

    def _suggest_type(self, fieldname: str, fieldobj: Any, usage: dict[str, Any]) -> str | None:
        current = type(fieldobj).__name__
        if current == "TEXT":
            if usage.get("unique_values", 0) / max(usage.get("doc_count", 1), 1) > 0.8:
                return "KEYWORD"
            if usage.get("is_id", False) and usage.get("unique", True):
                return "ID"
        if current == "TEXT" and usage.get("is_datetime", False):
            return "DATETIME"
        return None

    def _confidence(self, fieldname: str, fieldobj: Any, usage: dict[str, Any]) -> str:
        if usage.get("unique_values", 0) / max(usage.get("doc_count", 1), 1) > 0.95:
            return "high"
        return "medium"

    def _reason(self, fieldname: str, fieldobj: Any, usage: dict[str, Any], suggested: str) -> str:
        if suggested == "KEYWORD":
            return (
                "Valeurs très discriminantes ; KEYWORD évite l'analyse "
                "et réduit la taille de l'index."
            )
        if suggested == "ID":
            return "Valeur unique par document ; ID est plus compact et plus rapide."
        if suggested == "DATETIME":
            return "Valeurs date/heure détectées ; DATETIME permet le tri et le filtrage efficace."
        return ""

    def text(self) -> str:
        suggestions = self._suggestions or self.analyze()
        lines = ["Schema Optimization Report", "=" * 40, ""]
        if not suggestions:
            lines.append("Aucune suggestion d'optimisation.")
            return "\n".join(lines)
        for s in suggestions:
            lines.append(f"Field : {s['field']}")
            lines.append(f"  {s['current']} -> {s['suggested']} ({s['confidence']})")
            lines.append(f"  Raison : {s['reason']}")
            lines.append("")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "suggestions": self._suggestions or self.analyze(),
        }
