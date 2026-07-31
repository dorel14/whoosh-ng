"""SearchView that integrates all data source components."""

import logging
import os
from datetime import datetime
from typing import Any

from whoosh.fields import Schema
from whoosh.index import create_in, exists_in, open_dir
from whoosh_modern.exceptions import ValidationError
from whoosh_modern.middleware import Middleware
from whoosh_modern.validation import ValidationFramework, ValidationResult

logger = logging.getLogger(__name__)


class SearchView:
    """View that integrates a DataSource with Whoosh indexing."""

    def __init__(
        self,
        name: str,
        source: Any,
        fields: dict[str, Any] | None = None,
        facets: dict[str, dict[str, Any]] | None = None,
        incremental_field: str | None = None,
        strict: bool = False,
        middleware: list[Middleware] | None = None,
    ) -> None:
        self.name = name
        self.source = source
        self.fields = fields or {}
        self.facets = facets or {}
        self.incremental_field = incremental_field
        self.strict = strict
        self.middleware = middleware or []
        self._validator = ValidationFramework()
        self._validation_results: list[ValidationResult] = []
        self._index: Any | None = None
        self._index_path: str | None = None
        self._last_sync_value: Any = None
        self._schema: Schema | None = None

    def build(self, index_path: str) -> Any:
        """Create and populate index from source.

        Args:
            index_path: Path to the Whoosh index directory.

        Returns:
            The Whoosh Index object.
        """
        self._index_path = index_path

        # Discover schema
        schema = self.source.discover_schema()
        self._schema = schema

        # Apply field overrides
        schema = self._apply_field_overrides(schema)

        # Run validation
        self._validation_results = self._validator.validate(self.source)

        if self.strict:
            failed = [r for r in self._validation_results if not r.passed]
            if failed:
                raise ValidationError(
                    "Validation failed in strict mode",
                )

        # Create index directory if needed
        os.makedirs(index_path, exist_ok=True)

        # Create index
        if exists_in(index_path):
            self._index = open_dir(index_path)
        else:
            self._index = create_in(index_path, schema)

        # Populate index
        writer = self._index.writer()
        for doc in self.source.iter_documents():
            writer.add_document(**self._prepare_doc(doc, schema))
        writer.commit()

        return self._index

    def refresh(self) -> int:
        """Incremental refresh, returns count of updated documents."""
        if self._index is None or self._index_path is None:
            raise RuntimeError("Index not built yet, call build() first")

        if not self.incremental_field:
            return 0

        since = self._last_sync_value if self._last_sync_value else datetime.min

        count = 0
        writer = self._index.writer()
        schema = self._schema if self._schema is not None else self.source.discover_schema()
        for doc in self.source.iter_changes(since):
            writer.update_document(**self._prepare_doc(doc, schema))
            count += 1
        writer.commit()

        if count > 0:
            self._last_sync_value = datetime.now()

        return count

    def reindex(self) -> int:
        """Full reindex, returns count of indexed documents."""
        if self._index_path is None:
            raise RuntimeError("Index not built yet, call build() first")
        assert self._index is not None

        schema = self._schema if self._schema is not None else self.source.discover_schema()
        schema = self._apply_field_overrides(schema)

        count = 0
        writer = self._index.writer()
        for doc in self.source.iter_documents():
            writer.add_document(**self._prepare_doc(doc, schema))
            count += 1
        writer.commit()
        return count

    def validate(self) -> list[ValidationResult]:
        """Run all validation levels."""
        return self._validator.validate(self.source)

    def _apply_field_overrides(self, schema: Schema) -> Schema:
        """Apply field type overrides from the fields parameter."""
        if not self.fields:
            return schema

        # Rebuild schema with overrides
        fields: dict[str, Any] = {}
        for field_name, field_type in schema.items():
            if field_name in self.fields:
                fields[field_name] = self.fields[field_name]
            else:
                fields[field_name] = field_type

        return Schema(**fields)

    def _prepare_doc(self, doc: dict[str, Any], schema: Schema) -> dict[str, Any]:
        """Prepare a document for indexing.

        Preserves list/tuple values as multi-valued fields instead of
        joining them into a single string.

        Args:
            doc: Source document as a dict.
            schema: The Whoosh Schema to use for type checking.

        Returns:
            Prepared document dict ready for indexing.
        """
        prepared: dict[str, Any] = {}
        for field_name, _field_type in schema.items():
            if field_name in doc:
                value = doc[field_name]
                prepared[field_name] = value
        return prepared
