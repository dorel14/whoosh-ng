"""4-level validation framework with different error handling.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

import datetime as _dt
from contextlib import suppress
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from whoosh.fields import Schema
from whoosh_modern.exceptions import ValidationError


@dataclass
class ValidationResult:
    """Result of a validation check.

    Attributes:
        level: Validation level number (1-4).
        passed: Whether the validation level passed without errors.
        warnings: List of warning messages from the validation level.
        errors: List of error messages from the validation level.
    """

    level: int
    passed: bool
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class ValidationFramework:
    """Main validation orchestrator with 4 levels.

    Level 1: Structural validation (DataSource availability, schema detection).
    Level 2: Search validation (indexable fields, analyzer compatibility).
    Level 3: Performance validation (performance warnings).
    Level 4: Runtime validation (sample iteration, type validation).
    """

    def validate_structural(self, source: Any) -> list[str]:
        """Level 1: DataSource availability, schema detection.

        Args:
            source: The data source to validate.

        Returns:
            List of error/warning messages.
        """
        errors: list[str] = []
        try:
            schema = source.discover_schema()
            if not schema:
                errors.append("Schema discovery returned empty schema")
        except Exception as e:
            errors.append(f"Schema discovery failed: {e}")
        return errors

    def validate_search(self, schema: Schema) -> list[str]:
        """Level 2: Indexable fields, analyzer compatibility.

        Checks for fields that are stored but not searchable
        (i.e., fields with no term vectors and no searchable analyzer).

        Args:
            schema: The Whoosh Schema to validate.

        Returns:
            List of error/warning messages.
        """
        errors: list[str] = []
        for field_name, field_type in schema.items():
            if field_type.stored and not field_type.vector:
                errors.append(
                    f"Field '{field_name}' is stored but has no term vector "
                    f"and will not be searchable"
                )
        return errors

    def validate_performance(self, schema: Schema, source: Any) -> list[str]:
        """Level 3: Performance warnings.

        Args:
            schema: The Whoosh Schema to validate.
            source: The data source to validate.

        Returns:
            List of warning messages.
        """
        warnings: list[str] = []
        for field_name, field_type in schema.items():
            field_type_name = type(field_type).__name__
            if field_type_name == "TEXT":
                warnings.append(
                    f"Field '{field_name}' is TEXT which may be slow for large datasets"
                )
        return warnings

    def validate_runtime(
        self, source: Any, schema: Schema | None = None, sample_size: int = 100
    ) -> list[str]:
        """Level 4: Sample iteration, type validation.

        Args:
            source: The data source to validate.
            schema: Optional schema to enforce type conformance.
            sample_size: Number of documents to sample.

        Returns:
            List of error/warning messages.
        """
        errors: list[str] = []
        try:
            for count, doc in enumerate(source.iter_documents(), start=1):
                if count >= sample_size:
                    break
                if not isinstance(doc, dict):
                    errors.append(f"Document {count} is not a dict-like mapping")
                if schema is not None:
                    for field_name, field_type in schema.items():
                        if field_name in doc:
                            value = doc[field_name]
                            if value is None:
                                continue
                            try:
                                self.coerce_value(value, field_type, field_name=field_name)
                            except ValidationError as exc:
                                errors.append(f"Document {count}, field '{field_name}': {exc}")
        except Exception as e:
            errors.append(f"Document iteration failed: {e}")
        return errors

    @staticmethod
    def _normalize_value(value: Any, field_type: Any) -> Any:
        """Normalize a Python value into a form the field can consume.

        Only the small set of conversions Whoosh fields cannot perform
        themselves is applied here (``date`` -> ``datetime`` for DATETIME
        fields, ``Decimal`` -> ``float`` for NUMERIC fields declared without
        ``decimal_places``).

        Args:
            value: The raw value coming from the data source.
            field_type: The target Whoosh field type instance.

        Returns:
            The value, possibly adapted for the field's own converter.
        """
        from whoosh.fields import DATETIME, NUMERIC

        if isinstance(field_type, DATETIME):
            if isinstance(value, _dt.datetime):
                return value
            if isinstance(value, _dt.date):
                return _dt.datetime(value.year, value.month, value.day)
            if isinstance(value, int | float) and not isinstance(value, bool):
                # Interpret plain numbers as POSIX timestamps.
                return _dt.datetime.fromtimestamp(float(value), tz=_dt.UTC).replace(tzinfo=None)
            return value

        if (
            isinstance(field_type, NUMERIC)
            and isinstance(value, Decimal)
            and not getattr(field_type, "decimal_places", 0)
        ):
            return float(value)

        return value

    @staticmethod
    def coerce_value(value: Any, field_type: Any, field_name: str | None = None) -> Any:
        """Coerce a value using the target field's own conversion mechanism.

        Instead of re-implementing type checks with ``isinstance`` chains, this
        delegates to the Whoosh field itself (``FieldType.to_bytes`` and, for
        boolean fields, ``BOOLEAN._obj_to_bool``), which already implements the
        correct coercion rules for ID, KEYWORD, TEXT, NUMERIC, DATETIME and
        BOOLEAN fields.

        Args:
            value: The value to coerce.
            field_type: The Whoosh field type instance.
            field_name: Optional field name used in the error message.

        Returns:
            The value accepted by the field (possibly normalized).

        Raises:
            ValidationError: If the field cannot coerce the value.
        """
        from whoosh.fields import BOOLEAN

        normalized = ValidationFramework._normalize_value(value, field_type)
        try:
            if isinstance(field_type, BOOLEAN):
                field_type._obj_to_bool(normalized)
            else:
                to_bytes = getattr(field_type, "to_bytes", None)
                if to_bytes is None:
                    return normalized
                to_bytes(normalized)
        except Exception as exc:
            raise ValidationError(
                f"value {value!r} of type {type(value).__name__} is not compatible with "
                f"{type(field_type).__name__} field: {exc}",
                field=field_name,
            ) from exc
        return normalized

    @staticmethod
    def _check_type(value: Any, field_type: Any) -> bool:
        """Check if a value can be coerced by a Whoosh field type.

        Args:
            value: The value to check.
            field_type: The Whoosh field type instance.

        Returns:
            True if the field's own converter accepts the value.
        """
        try:
            ValidationFramework.coerce_value(value, field_type)
        except ValidationError:
            return False
        return True

    def validate(self, source: Any) -> list[ValidationResult]:
        """Run all validation levels.

        Args:
            source: The data source to validate.

        Returns:
            List of ValidationResult objects, one per level.
        """
        # Discover schema once and cache it for all levels
        schema: Schema | None = None
        with suppress(Exception):
            schema = source.discover_schema()

        results: list[ValidationResult] = []

        # Level 1: Structural
        structural_errors = self.validate_structural(source)
        results.append(
            ValidationResult(
                level=1,
                passed=len(structural_errors) == 0,
                errors=structural_errors,
            )
        )

        # Level 2: Search
        if schema is not None:
            search_errors = self.validate_search(schema)
        else:
            search_errors = ["Schema discovery failed, cannot validate search"]
        results.append(
            ValidationResult(
                level=2,
                passed=len(search_errors) == 0,
                errors=search_errors,
            )
        )

        # Level 3: Performance
        perf_warnings = self.validate_performance(schema, source) if schema is not None else []
        results.append(
            ValidationResult(
                level=3,
                passed=True,
                warnings=perf_warnings,
            )
        )

        # Level 4: Runtime
        runtime_errors = self.validate_runtime(source, schema=schema)
        results.append(
            ValidationResult(
                level=4,
                passed=len(runtime_errors) == 0,
                errors=runtime_errors,
            )
        )

        return results
