"""SearchView that integrates all data source components.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from typing import Any

from whoosh.fields import Schema
from whoosh.index import create_in, exists_in, open_dir
from whoosh.middleware.context import MiddlewareContext
from whoosh_modern.exceptions import ValidationError
from whoosh_modern.middleware import Middleware
from whoosh_modern.validation import ValidationFramework, ValidationResult

logger = logging.getLogger(__name__)

_SCHEMA_VERSION_FIELD = "_schema_version"
_SCHEMA_UPDATED_AT_FIELD = "_schema_updated_at"


class SearchView:
    """View that integrates a DataSource with Whoosh indexing.

    Provides a high-level interface for building, refreshing, and reindexing
    a Whoosh index from any DataSource implementation. Supports incremental
    refreshes, schema evolution, and multi-level validation.

    Attributes:
        name: Human-readable name for this search view.
        source: The DataSource providing documents for indexing.
        fields: Optional field type overrides applied during schema building.
        facets: Facet configuration dict keyed by field name.
        incremental_field: Field name used for incremental refresh tracking.
        strict: If True, raises on validation errors instead of logging.
        middleware: List of Middleware instances applied during processing.
        schema_version: Schema version string stored in index metadata.
    """

    def __init__(
        self,
        name: str,
        source: Any,
        fields: dict[str, Any] | None = None,
        facets: dict[str, dict[str, Any]] | None = None,
        incremental_field: str | None = None,
        strict: bool = False,
        middleware: list[Middleware] | None = None,
        schema_version: str | None = None,
    ) -> None:
        """Initialize a SearchView.

        Args:
            name: Human-readable name for this search view.
            source: The DataSource providing documents for indexing.
            fields: Optional field type overrides applied during schema building.
            facets: Facet configuration dict keyed by field name.
            incremental_field: Field name used for incremental refresh tracking.
            strict: If True, raises ValidationError on failed validation.
            middleware: List of Middleware instances applied during processing.
            schema_version: Schema version string; defaults to "1.0".
        """
        self.name = name
        self.source = source
        self.fields = fields or {}
        self.facets = facets or {}
        self.incremental_field = incremental_field
        self.strict = strict
        self.middleware = middleware or []
        self.schema_version = schema_version or "1.0"
        self._validator = ValidationFramework()
        self._validation_results: list[ValidationResult] = []
        self._index: Any | None = None
        self._index_path: str | None = None
        self._last_sync_value: Any = None
        self._schema: Schema | None = None

    def build(self, index_path: str) -> Any:
        """Create and populate index from source.

        Discover the schema from the data source, apply field overrides,
        run validation, and create or open a Whoosh index at ``index_path``.

        Args:
            index_path: Path to the Whoosh index directory.

        Returns:
            The Whoosh Index object.

        Raises:
            ValidationError: If validation fails in strict mode.
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
        """Perform an incremental refresh of the index.

        Uses the ``incremental_field`` to fetch only changed documents
        since the last sync and updates them in the index.

        Returns:
            The count of documents that were updated.

        Raises:
            RuntimeError: If the index has not been built yet.
        """
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
        """Perform a full reindex of all documents from the source.

        Returns:
            The count of documents that were indexed.

        Raises:
            RuntimeError: If the index has not been built yet.
        """
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
        """Run all validation levels against the data source.

        Returns:
            A list of ValidationResult objects, one per validation level.
        """
        return self._validator.validate(self.source)

    def _apply_field_overrides(self, schema: Schema) -> Schema:
        """Apply field type overrides from the fields parameter.

        Also injects embedding target fields declared by any
        :class:`EmbeddingMiddleware` so that the generated schema always
        contains the fields required to store computed vectors.

        Args:
            schema: The original discovered Whoosh Schema.

        Returns:
            A new Schema with overridden field types where specified.
        """
        fields: dict[str, Any] = {}
        for field_name, field_type in schema.items():
            fields[field_name] = field_type

        for field_name, field_type in self.fields.items():
            fields[field_name] = field_type

        for middleware in self.middleware:
            embedding_fields = getattr(middleware, "_embedding_fields", None)
            if embedding_fields:
                for field_config in embedding_fields:
                    target_field = field_config.get("target_field")
                    if target_field and target_field not in fields:
                        from whoosh_modern.fields import VECTOR

                        fields[target_field] = VECTOR()
            else:
                target_field = getattr(middleware, "_target_field", None)
                if target_field and target_field not in fields:
                    from whoosh_modern.fields import VECTOR

                    fields[target_field] = VECTOR()

        return Schema(**fields)

    def _prepare_doc(self, doc: dict[str, Any], schema: Schema) -> dict[str, Any]:
        """Prepare a document for indexing.

        Preserves list/tuple values as multi-valued fields instead of
        joining them into a single string. Converts non-string scalar values
        (e.g. integers from SQL) to strings for Whoosh compatibility.
        Runs middleware ``before_index`` hooks when configured.

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
                if value is not None and not isinstance(value, str | bytes | list | tuple):
                    value = str(value)
                prepared[field_name] = value

        if self.middleware:
            context = MiddlewareContext("index")
            context.document = prepared
            for middleware in self.middleware:
                context = middleware.before_index(context)
            if context.document is not None:
                prepared = context.document

        return prepared

    def _store_schema_metadata(self, schema: Schema) -> None:
        """Store schema version and update timestamp in index metadata.

        Args:
            schema: The Whoosh Schema to version.
        """
        if self._index is None or self._index_path is None:
            return

        try:
            if not exists_in(self._index_path):
                return

            ix = open_dir(self._index_path)
            with ix.writer() as writer:
                writer.add_document(
                    **{
                        _SCHEMA_VERSION_FIELD: self.schema_version,
                        _SCHEMA_UPDATED_AT_FIELD: str(time.time()),
                    }
                )
        except Exception:
            logger.debug("Could not store schema metadata", exc_info=True)

    def check_schema_version(self) -> bool:
        """Check if the stored schema version matches the current version.

        Returns:
            True if the schema is up to date, False otherwise.
        """
        if self._index is None or self._index_path is None:
            return True

        try:
            return _SCHEMA_VERSION_FIELD in self._index.schema
        except Exception:
            return False

    def evolve_schema(self, new_fields: dict[str, Any]) -> None:
        """Evolve the schema by adding new fields without a full reindex.

        Args:
            new_fields: Dict of field_name -> Whoosh field type to add.

        Raises:
            RuntimeError: If the index has not been built yet.
        """
        if self._index is None or self._index_path is None:
            raise RuntimeError("Index not built yet, call build() first")

        assert self._schema is not None
        existing_fields = {name for name, _ in self._schema.items()}
        fields_to_add = {name: ft for name, ft in new_fields.items() if name not in existing_fields}

        if not fields_to_add:
            return

        from whoosh.index import open_dir

        ix = open_dir(self._index_path)
        with ix.writer() as writer:
            for field_name, field_type in fields_to_add.items():
                try:
                    writer.add_field(field_name, field_type)
                except Exception:
                    logger.debug("Could not add field %s", field_name, exc_info=True)
