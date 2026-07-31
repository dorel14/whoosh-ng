"""4-level validation framework with different error handling."""

from contextlib import suppress
from dataclasses import dataclass, field
from typing import Any

from whoosh.fields import BOOLEAN, DATETIME, ID, KEYWORD, NUMERIC, TEXT, Schema
from whoosh_modern.exceptions import ValidationError
from whoosh_modern.schema_discovery import SchemaDiscovery


@dataclass
class ValidationResult:
    """Result of a validation check."""

    level: int
    passed: bool
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class ValidationFramework:
    """Main validation orchestrator with 4 levels."""

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
                            if value is not None and not self._check_type(value, field_type):
                                errors.append(
                                    f"Document {count}, field '{field_name}': "
                                    f"expected {type(field_type).__name__}, "
                                    f"got {type(value).__name__}"
                                )
        except Exception as e:
            errors.append(f"Document iteration failed: {e}")
        return errors

    @staticmethod
    def _check_type(value: Any, field_type: Any) -> bool:
        """Check if a value is compatible with a Whoosh field type."""
        from whoosh.fields import BOOLEAN, DATETIME, ID, KEYWORD, NUMERIC, TEXT

        if isinstance(field_type, ID):
            return isinstance(value, str)
        if isinstance(field_type, KEYWORD):
            return isinstance(value, str)
        if isinstance(field_type, NUMERIC):
            return isinstance(value, (int, float))
        if isinstance(field_type, DATETIME):
            return isinstance(value, (int, float))
        if isinstance(field_type, TEXT):
            return isinstance(value, (str, bytes))
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
