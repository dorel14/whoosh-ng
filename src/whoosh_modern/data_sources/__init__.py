"""DataSource protocol and capability interfaces.

Data sources implement ``discover_schema()`` either by:

* **Using ``SchemaDiscovery``** — for raw/untyped records (JSON, CSV,
  REST, GraphQL, Pydantic models, SQL result sets) where schema must be
  inferred from actual values or DB metadata.
* **Implementing custom logic** — for strongly-typed backends
  (Pandas, Polars, PyArrow, SQLAlchemy, Peewee, Tortoise ORM) where the
  native type system provides a direct mapping to Whoosh fields.

Author: dorel14
Version: 3.0.0
"""

from collections.abc import AsyncIterator, Callable, Iterator, Mapping
from typing import Any, Protocol, runtime_checkable

from whoosh.fields import Schema

Document = Mapping[str, Any]
SearchSchema = Schema


@runtime_checkable
class DataSource(Protocol):
    """Protocol for searchable data sources.

    Defines the minimal interface that every data source must implement
    to be usable by the Whoosh-NG indexer pipeline. Implementations may
    also implement one or more of the optional capability protocols
    (e.g. :class:`IncrementalDataSource`, :class:`AsyncDataSource`).
    """

    @property
    def name(self) -> str:
        """Return the data source name.

        Returns:
            A human-readable identifier for this data source, typically
            in the form ``type:descriptor``.
        """
        ...

    def discover_schema(self) -> Schema:
        """Return Whoosh Schema inferred from data source.

        Inspects the underlying source to produce a Whoosh
        :class:`~whoosh.fields.Schema` suitable for indexing the
        documents yielded by :meth:`iter_documents`.

        Returns:
            A Whoosh ``Schema`` object derived from the data source.
        """
        ...

    def iter_documents(self) -> Iterator[Document]:
        """Yield documents from source as dict-like mappings.

        Returns:
            An iterator over documents, each represented as a
            mapping of field names to values.
        """
        ...

    def stream_batches(self, batch_size: int = 1000) -> Iterator[list[dict[str, Any]]]:
        """Yield documents in batches for efficient bulk indexing.

        Default implementation groups :meth:`iter_documents` into lists of
        ``batch_size``. DataSource implementations should override this when
        they can read batches natively (e.g. SQL cursor fetchmany, Parquet
        row-group reads, JSONL line buffering).

        Args:
            batch_size: Maximum number of documents per batch.

        Yields:
            Lists of document dictionaries, each list containing at most
            ``batch_size`` items.
        """
        ...

    def health_check(self) -> bool:
        """Return True if the data source is reachable and healthy.

        Returns:
            ``True`` if the data source is accessible and ready to
            provide documents, ``False`` otherwise.
        """
        ...


@runtime_checkable
class IncrementalDataSource(Protocol):
    """Protocol for data sources that support incremental updates.

    An incremental data source can report only documents that have
    changed since a given timestamp or sequence value.
    """

    def iter_changes(self, since: Any) -> Iterator[Document]:
        """Yield documents changed since timestamp.

        Args:
            since: A timestamp, sequence number, or cursor value from
                which to begin yielding changes. The exact semantics
                depend on the data source implementation.

        Yields:
            Documents that were created or modified after ``since``.
        """
        ...


@runtime_checkable
class AsyncDataSource(Protocol):
    """Protocol for async data sources.

    Async data sources provide document streaming via an asynchronous
    iterator, which is useful for sources that perform I/O-bound work
    such as network or database access.
    """

    async def aiter_documents(self) -> AsyncIterator[Document]:
        """Async document streaming.

        Yields:
            Documents asynchronously, each represented as a mapping of
            field names to values.
        """
        ...


@runtime_checkable
class RefreshableDataSource(Protocol):
    """Protocol for refreshable data sources.

    A refreshable data source can re-read its underlying state, which
    is useful when the source may change between indexing runs.
    """

    def refresh(self) -> None:
        """Refresh source state.

        Re-reads or re-validates the underlying data so that
        subsequent document iteration reflects the latest state.
        """
        ...


@runtime_checkable
class CountableDataSource(Protocol):
    """Protocol for data sources that support document counting.

    Countable data sources can report the total number of documents
    without iterating through all of them.
    """

    def document_count(self) -> int:
        """Return total document count.

        Returns:
            The number of documents available in the data source.
        """
        ...


@runtime_checkable
class MetadataDataSource(Protocol):
    """Protocol for data sources that expose metadata.

    Metadata sources provide descriptive information about themselves,
    such as configuration, statistics, or internal state.
    """

    def metadata(self) -> Mapping[str, Any]:
        """Return source metadata.

        Returns:
            A mapping of metadata key to value describing the
            data source.
        """
        ...


@runtime_checkable
class ObservableDataSource(Protocol):
    """Protocol for data sources that emit change events.

    Observable data sources allow external callers to register
    callbacks that are invoked when documents are added, updated, or
    removed.
    """

    def add_observer(self, callback: Callable[[str, Document], None]) -> None:
        """Register an observer callback for document events.

        Args:
            callback: A callable invoked with an event type string
                (e.g. ``"added"``, ``"updated"``, ``"removed"``) and
                the affected document.
        """
        ...

    def remove_observer(self, callback: Callable[[str, Document], None]) -> None:
        """Unregister an observer callback.

        Args:
            callback: The previously-registered callable to remove
                from the observer list.
        """
        ...
