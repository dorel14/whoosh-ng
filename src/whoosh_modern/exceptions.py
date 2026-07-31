"""Typed exceptions with source and field context."""


class DataSourceError(Exception):
    """Base exception for DataSource errors."""

    def __init__(
        self,
        message: str,
        source: str | None = None,
        field: str | None = None,
    ) -> None:
        super().__init__(message)
        self.source = source
        self.field = field


class SchemaDiscoveryError(DataSourceError):
    """Failed to discover schema from source."""


class DocumentIterationError(DataSourceError):
    """Error during document iteration."""


class ValidationError(DataSourceError):
    """Validation failed at any level."""


class DataSourceNotFoundError(DataSourceError):
    """Requested DataSource not found."""
