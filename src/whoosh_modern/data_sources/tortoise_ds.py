"""Tortoise ORM DataSource implementation (optional backend)."""

import logging
from collections.abc import Iterator, Mapping
from typing import Any

from whoosh_modern.exceptions import DataSourceError

logger = logging.getLogger(__name__)

Document = Mapping[str, Any]


class TortoiseSource:
    """Tortoise ORM data source implementing the DataSource protocol.

    Supports selecting from a Tortoise ORM model.

    Uses Tortoise field metadata to infer the Whoosh schema directly, so
    ``SchemaDiscovery`` is not needed here.

    Example:
        from tortoise import Tortoise
        from whoosh_modern.data_sources.tortoise_ds import TortoiseSource

        await Tortoise.init(db_url="sqlite://:memory:", modules={"models": ["models"]})
        source = TortoiseSource(model=Article)
    """

    def __init__(
        self,
        model: Any,
        incremental_field: str | None = None,
        id_field: str | None = None,
        sample_size: int = 5,
    ) -> None:
        self._model = model
        self.incremental_field = incremental_field
        self.id_field = id_field
        self.sample_size = sample_size
        self._schema: Any = None

    @property
    def name(self) -> str:
        """Return the data source name."""
        return f"tortoise:{self._model._meta.db_table}"

    def health_check(self) -> bool:
        """Return True if the Tortoise ORM connection is healthy."""
        try:
            from tortoise import Tortoise

            return Tortoise.is_inited()  # type: ignore[no-any-return]
        except Exception:
            return False

    def discover_schema(self) -> Any:
        """Discover schema from Tortoise ORM model fields."""
        if self._schema is not None:
            return self._schema

        if self._model is None:
            raise DataSourceError(
                "TortoiseSource requires a 'model' to discover schema",
                source="tortoise",
            )

        columns: dict[str, Any] = {}
        for field_name, field in self._model._meta.fields_map.items():
            columns[field_name] = self._map_tortoise_field(field)

        from whoosh.fields import Schema

        self._schema = Schema(**columns)
        return self._schema

    def _map_tortoise_field(self, field: Any) -> Any:
        """Map Tortoise ORM field to Whoosh field."""
        from whoosh.fields import BOOLEAN, DATETIME, NUMERIC, TEXT

        field_type = type(field).__name__.lower()

        if "char" in field_type or "text" in field_type:
            return TEXT(stored=True)
        if "int" in field_type or "bigint" in field_type:
            return NUMERIC(int, stored=True)
        if "float" in field_type or "decimal" in field_type:
            return NUMERIC(float, stored=True)
        if "bool" in field_type:
            return BOOLEAN(stored=True)
        if "date" in field_type or "time" in field_type or "datetime" in field_type:
            return DATETIME(stored=True)

        return TEXT(stored=True)

    async def _fetch_all(self) -> list[dict[str, Any]]:
        """Fetch all records from the Tortoise model."""
        if self._model is None:
            raise DataSourceError(
                "TortoiseSource requires a 'model' to fetch documents",
                source="tortoise",
            )
        queryset = self._model.all()
        return list(await queryset.values())

    def iter_documents(self) -> Iterator[Document]:
        """Yield documents from the Tortoise ORM model."""
        import asyncio

        coro = self._fetch_all()
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            docs = asyncio.run(coro)
        else:
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(asyncio.run, coro)
                docs = future.result()
        yield from docs

    def iter_changes(self, since: Any) -> Iterator[Document]:
        """Yield documents changed since a timestamp (not implemented for Tortoise)."""
        return iter([])

    def document_count(self) -> int:
        """Return total document count."""
        import asyncio

        if self._model is None:
            raise DataSourceError(
                "TortoiseSource requires a 'model' to count documents",
                source="tortoise",
            )

        async def _count() -> int:
            return int(await self._model.all().count())

        coro = _count()
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        else:
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()

    def metadata(self) -> dict[str, Any]:
        """Return metadata about this Tortoise source."""
        return {
            "type": "tortoise",
            "table": self._model._meta.db_table,
            "incremental_field": self.incremental_field,
            "id_field": self.id_field,
        }
