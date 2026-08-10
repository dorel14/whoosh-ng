"""Peewee DataSource implementation (optional backend).

Author: dorel14
Version: 3.0.0
"""

import logging
from collections.abc import Iterator, Mapping
from typing import Any

from whoosh.fields import Schema
from whoosh_modern.exceptions import DataSourceError

logger = logging.getLogger(__name__)

Document = Mapping[str, Any]


class PeeweeSource:
    """Peewee ORM data source implementing the DataSource protocol.

    Supports selecting from a Peewee model or raw query.

    Uses Peewee field metadata to infer the Whoosh schema directly, so
    ``SchemaDiscovery`` is not needed here.

    Example:
        from peewee import SqliteDatabase, Model, CharField
        from whoosh_modern.data_sources.peewee_ds import PeeweeSource

        db = SqliteDatabase(":memory:")
        class Article(Model):
            title = CharField()
            class Meta:
                database = db

        source = PeeweeSource(model=Article)

    Args:
        model: A Peewee ``Model`` subclass to query (optional if
            ``query`` is provided).
        query: A raw SQL query string (optional if ``model`` is
            provided).
        database: A Peewee ``Database`` instance. If not provided it is
            derived from the model.
        incremental_field: Optional column name for incremental syncs.
        id_field: Optional column name that uniquely identifies a
            document.
        sample_size: Number of records to inspect during schema
            discovery.
    """

    def __init__(
        self,
        model: Any = None,
        query: str | None = None,
        database: Any = None,
        incremental_field: str | None = None,
        id_field: str | None = None,
        sample_size: int = 5,
    ) -> None:
        self._model = model
        self.query = query
        self._database = database
        self.incremental_field = incremental_field
        self.id_field = id_field
        self.sample_size = sample_size
        self._schema: Schema | None = None

        if model is None and query is None:
            raise DataSourceError(
                "PeeweeSource requires either a 'model' or 'query'",
                source="peewee",
            )

    @property
    def name(self) -> str:
        """Return the data source name.

        Returns:
            A string in the form ``peewee:<table>`` or
            ``peewee:<query_prefix>``.
        """
        if self._model is not None:
            return f"peewee:{self._model._meta.table_name}"
        return f"peewee:{self.query[:50] if self.query is not None else ''}"

    def health_check(self) -> bool:
        """Return True if the database connection is healthy.

        Returns:
            ``True`` if a trivial ``SELECT 1`` succeeds, ``False``
            otherwise.
        """
        try:
            db = self._get_database()
            db.execute_sql("SELECT 1")
            return True
        except Exception:
            return False

    def _get_database(self) -> Any:
        """Get the Peewee database instance.

        Returns:
            The Peewee database from the constructor or from the
            model's metadata.

        Raises:
            DataSourceError: If no database can be determined.
        """
        if self._database is not None:
            return self._database
        if self._model is not None:
            return self._model._meta.database
        raise DataSourceError("No database available", source="peewee")

    def _get_query(self) -> Any:
        """Get the Peewee query object.

        Returns:
            A Peewee ``Select`` query from the model or a raw
            query result from the database.

        Raises:
            DataSourceError: If neither a model nor a query was
                provided.
        """
        if self._model is not None:
            return self._model.select()
        if self.query is not None:
            return self._get_database().execute_sql(self.query)
        raise DataSourceError("No query or model provided", source="peewee")

    def discover_schema(self) -> Schema:
        """Discover schema from Peewee model fields.

        Returns:
            A Whoosh :class:`~whoosh.fields.Schema` derived from the
            model's field definitions. Returns an empty schema if no
            model was provided.
        """
        if self._schema is not None:
            return self._schema

        if self._model is None:
            from whoosh.fields import Schema

            return Schema()

        columns: dict[str, Any] = {}
        for field in self._model._meta.fields.values():
            columns[field.name] = self._map_peewee_field(field)

        from whoosh.fields import Schema

        self._schema = Schema(**columns)
        return self._schema

    def _map_peewee_field(self, field: Any) -> Any:
        """Map Peewee field to Whoosh field.

        Delegates to the canonical
        :meth:`whoosh_modern.models.base.TypeMapper.map_dtype`, using the
        Peewee field class name as the dtype name.

        Args:
            field: A Peewee field instance.

        Returns:
            A Whoosh field instance (``TEXT``, ``NUMERIC``,
            ``BOOLEAN``, or ``DATETIME``) configured as stored.
        """
        from whoosh_modern.models.base import TypeMapper

        return TypeMapper.map_dtype(type(field).__name__)

    def iter_documents(self) -> Iterator[Document]:
        """Yield documents from the Peewee query.

        Yields:
            Document dictionaries from the model or raw query.
        """
        query = self._get_query()
        db = self._get_database()

        with db.connection_context():
            for row in query:
                if self._model is not None:
                    yield self._model_to_dict(row)
                else:
                    yield dict(row._mapping)

    def _model_to_dict(self, model: Any) -> dict[str, Any]:
        """Convert a Peewee model instance to a dict.

        Args:
            model: A Peewee model instance.

        Returns:
            A dictionary mapping field names to values.
        """
        return {field.name: getattr(model, field.name) for field in model._meta.fields.values()}

    def iter_changes(self, since: Any) -> Iterator[Document]:
        """Yield documents changed since a timestamp (not implemented for Peewee).

        Args:
            since: A timestamp or cursor value (accepted but ignored).

        Yields:
            Nothing — incremental changes are not supported for this
            data source.
        """
        return iter([])

    def document_count(self) -> int:
        """Return total document count.

        Returns:
            The number of rows returned by the configured model or
            query.
        """
        query = self._get_query()
        db = self._get_database()

        with db.connection_context():
            return int(query.count())

    def metadata(self) -> dict[str, Any]:
        """Return metadata about this Peewee source.

        Returns:
            A dictionary with keys ``type``, ``table``,
            ``incremental_field``, and ``id_field``.
        """
        table_name = "unknown"
        if self._model is not None:
            table_name = self._model._meta.table_name
        elif self.query is not None:
            table_name = self.query[:50]

        return {
            "type": "peewee",
            "table": table_name,
            "incremental_field": self.incremental_field,
            "id_field": self.id_field,
        }
