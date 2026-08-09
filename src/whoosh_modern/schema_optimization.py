"""Schema optimization report for Whoosh-NG.

Analyzes a schema against observed field usage and suggests type changes
that can improve index size and query performance.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any


class SchemaOptimizationReport:
    """Analyzes a schema and field usage to suggest optimizations.

    Example::

        report = SchemaOptimizationReport(schema, usage)
        print(report.text())
    """

    def __init__(self, schema: Any, usage: dict[str, dict[str, Any]] | None = None) -> None:
        """Initialize the SchemaOptimizationReport.

        Args:
            schema: A Whoosh Schema to analyze.
            usage: Optional usage statistics per field, where each value is a
                dict containing keys such as ``doc_count``, ``unique_values``,
                ``is_id``, ``is_datetime``, etc.
        """
        self.schema = schema
        self.usage = usage or {}
        self._suggestions: list[dict[str, Any]] = []

    def analyze(self) -> list[dict[str, Any]]:
        """Analyze the schema and field usage to produce optimization suggestions.

        Returns:
            A list of suggestion dicts, each containing keys: ``field``,
            ``current``, ``suggested``, ``confidence``, and ``reason``.
        """
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
        """Suggest an optimized field type based on usage statistics.

        Args:
            fieldname: The name of the field being analyzed.
            fieldobj: The Whoosh field object.
            usage: Usage statistics dict for this field.

        Returns:
            The suggested type name, or None if no change is recommended.
        """
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
        """Compute the confidence level for a suggestion.

        Args:
            fieldname: The name of the field.
            fieldobj: The Whoosh field object.
            usage: Usage statistics dict for this field.

        Returns:
            Either ``"high"`` or ``"medium"``.
        """
        if usage.get("unique_values", 0) / max(usage.get("doc_count", 1), 1) > 0.95:
            return "high"
        return "medium"

    def _reason(self, fieldname: str, fieldobj: Any, usage: dict[str, Any], suggested: str) -> str:
        """Generate a human-readable reason for a type suggestion.

        Args:
            fieldname: The name of the field.
            fieldobj: The Whoosh field object.
            usage: Usage statistics dict for this field.
            suggested: The suggested type name.

        Returns:
            A localized explanation string.
        """
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
        """Render the optimization report as a human-readable text string.

        Returns:
            A multi-line string containing the full report.
        """
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
        """Serialize the report to a dictionary.

        Returns:
            A dict with a single ``suggestions`` key holding the list of
            suggestion dicts.
        """
        return {
            "suggestions": self._suggestions or self.analyze(),
        }
