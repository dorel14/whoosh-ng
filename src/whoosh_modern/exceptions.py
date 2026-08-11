"""Typed exceptions with source and field context for Whoosh-NG.

Author: dorel14
Version: 3.0.0
"""


class DataSourceError(Exception):
    """Base exception for DataSource errors.

    Attributes:
        source: Name of the data source where the error originated.
        field: Name of the field where the error originated.
    """

    def __init__(
        self,
        message: str,
        source: str | None = None,
        field: str | None = None,
    ) -> None:
        """Initialize the exception with optional source and field context.

        Args:
            message: Human-readable error message.
            source: Name of the data source where the error originated.
            field: Name of the field where the error originated.
        """
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
