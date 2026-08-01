"""DataSource protocol and capability interfaces."""

from collections.abc import AsyncIterator, Callable, Iterator, Mapping
from typing import Any, Protocol, runtime_checkable

from whoosh.fields import Schema

Document = Mapping[str, Any]
SearchSchema = Schema


@runtime_checkable
class DataSource(Protocol):
    """Protocol for searchable data sources."""

    @property
    def name(self) -> str:
        """Return the data source name."""
        ...

    def discover_schema(self) -> Schema:
        """Return Whoosh Schema inferred from data source."""
        ...

    def iter_documents(self) -> Iterator[Document]:
        """Yield documents from source as dict-like mappings."""
        ...


@runtime_checkable
class IncrementalDataSource(Protocol):
    """Protocol for data sources that support incremental updates."""

    def iter_changes(self, since: Any) -> Iterator[Document]:
        """Yield documents changed since timestamp."""
        ...


@runtime_checkable
class AsyncDataSource(Protocol):
    """Protocol for async data sources."""

    async def aiter_documents(self) -> AsyncIterator[Document]:
        """Async document streaming."""
        ...


@runtime_checkable
class RefreshableDataSource(Protocol):
    """Protocol for refreshable data sources."""

    def refresh(self) -> None:
        """Refresh source state."""
        ...


@runtime_checkable
class CountableDataSource(Protocol):
    """Protocol for data sources that support document counting."""

    def document_count(self) -> int:
        """Return total document count."""
        ...


@runtime_checkable
class MetadataDataSource(Protocol):
    """Protocol for data sources that expose metadata."""

    def metadata(self) -> Mapping[str, Any]:
        """Return source metadata."""
        ...


@runtime_checkable
class ObservableDataSource(Protocol):
    """Protocol for data sources that emit change events."""

    def add_observer(self, callback: Callable[[str, Document], None]) -> None:
        """Register an observer callback for document events."""
        ...

    def remove_observer(self, callback: Callable[[str, Document], None]) -> None:
        """Unregister an observer callback."""
        ...
