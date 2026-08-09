"""Pydantic DataSource implementation for Pydantic model collections.

Author: dorel14
Version: 3.0.0
"""

import logging
from collections.abc import Iterator, Mapping
from typing import Any

from whoosh.fields import Schema
from whoosh_modern.exceptions import DataSourceError
from whoosh_modern.schema_discovery import SchemaDiscovery

logger = logging.getLogger(__name__)

Document = Mapping[str, Any]


def _get_pydantic_model_fields(model: Any) -> list[str]:
    """Extract field names from a Pydantic model (v1 or v2).

    Args:
        model: A Pydantic model class (v1 or v2).

    Returns:
        A list of field name strings.

    Raises:
        DataSourceError: If the model has neither ``model_fields``
            nor ``__fields__``.
    """
    if hasattr(model, "model_fields"):
        return list(model.model_fields.keys())
    if hasattr(model, "__fields__"):
        return list(model.__fields__.keys())
    raise DataSourceError(
        f"Unsupported Pydantic model type: {type(model)}",
        source="pydantic",
    )


def _model_to_dict(model: Any) -> dict[str, Any]:
    """Convert a Pydantic model instance to a dict (v1 or v2).

    Args:
        model: A Pydantic model instance (v1 or v2).

    Returns:
        A dictionary representation of the model.

    Raises:
        DataSourceError: If the model has neither ``model_dump`` nor
            ``dict`` method.
    """
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="python")  # type: ignore[no-any-return]
    if hasattr(model, "dict"):
        return model.dict()  # type: ignore[no-any-return]
    raise DataSourceError(
        f"Unsupported Pydantic model instance: {type(model)}",
        source="pydantic",
    )


class PydanticSource:
    """Pydantic model collection data source implementing the DataSource protocol.

    Iterates over a pre-built list of Pydantic model instances,
    converting each to a dictionary for Whoosh indexing.

    Args:
        models: A non-empty list of Pydantic model instances.
        model: Optional Pydantic model class. If not provided, the
            type of the first instance is used.
        incremental_field: Optional field name for incremental syncs.
        id_field: Optional field name that uniquely identifies a
            document.
        sample_size: Number of instances to inspect during schema
            discovery.
    """

    def __init__(
        self,
        models: list[Any],
        model: type[Any] | None = None,
        incremental_field: str | None = None,
        id_field: str | None = None,
        sample_size: int = 5,
    ) -> None:
        if not models:
            raise DataSourceError(
                "PydanticSource requires a non-empty models list",
                source="pydantic",
            )

        self._models = models
        self._model_type = model or type(models[0])
        self.incremental_field = incremental_field
        self.id_field = id_field
        self.sample_size = sample_size
        self._schema: Schema | None = None
        self._compiled_mapper: Any = None

    @property
    def name(self) -> str:
        """Return the data source name.

        Returns:
            A string in the form ``pydantic:<model_name>``.
        """
        model_name = getattr(self._model_type, "__name__", "unknown")
        return f"pydantic:{model_name}"

    def health_check(self) -> bool:
        """Return True if the model collection is non-empty.

        Returns:
            ``True`` if at least one model instance exists,
            ``False`` otherwise.
        """
        return len(self._models) > 0

    def discover_schema(self) -> Schema:
        """Discover schema from Pydantic model fields.

        Inspects the model class's field definitions and infers
        Whoosh field types for each.

        Returns:
            A Whoosh :class:`~whoosh.fields.Schema` derived from the
            model's field names.
        """
        fields = {}
        for field_name in _get_pydantic_model_fields(self._model_type):
            fields[field_name] = SchemaDiscovery._infer_field_type(None)

        self._schema = Schema(**fields)
        return self._schema

    def compile_mapper(self) -> Any:
        """Return a compiled document mapper for this source.

        Pre-computes the model_to_dict function for repeated use.

        Returns:
            A callable that accepts a Pydantic model instance and
            returns a dictionary.
        """
        if self._compiled_mapper is not None:
            return self._compiled_mapper

        model_type = self._model_type
        if hasattr(model_type, "model_dump"):

            def _mapper_v2(model: Any) -> dict[str, Any]:
                return model.model_dump(mode="python")  # type: ignore[no-any-return]

            self._compiled_mapper = _mapper_v2
        elif hasattr(model_type, "dict"):

            def _mapper_v1(model: Any) -> dict[str, Any]:
                return model.dict()  # type: ignore[no-any-return]

            self._compiled_mapper = _mapper_v1
        else:
            self._compiled_mapper = _model_to_dict
        return self._compiled_mapper

    def iter_documents(self) -> Iterator[Document]:
        """Yield documents from the Pydantic model list.

        Yields:
            Document dictionaries, one per model instance.
        """
        for model_instance in self._models:
            yield _model_to_dict(model_instance)

    def stream_batches(self, batch_size: int = 1000) -> Iterator[list[dict[str, Any]]]:
        """Yield documents from the Pydantic model list in batches.

        Args:
            batch_size: Maximum number of documents per batch.

        Yields:
            Lists of document dictionaries, each list containing at
            most ``batch_size`` items.
        """
        batch: list[dict[str, Any]] = []
        for model_instance in self._models:
            batch.append(_model_to_dict(model_instance))
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch

    def iter_changes(self, since: Any) -> Iterator[Document]:
        """Yield documents changed since a timestamp (not implemented for PydanticSource).

        Args:
            since: A timestamp or cursor value (accepted but ignored).

        Yields:
            Nothing — incremental changes are not supported for this
            data source.
        """
        return iter([])

    def document_count(self) -> int:
        """Return total model count.

        Returns:
            The number of model instances in the collection.
        """
        return len(self._models)

    def metadata(self) -> dict[str, Any]:
        """Return metadata about this Pydantic source.

        Returns:
            A dictionary with keys ``type``, ``model``, ``count``,
            ``incremental_field``, and ``id_field``.
        """
        model_name = getattr(self._model_type, "__name__", "unknown")
        return {
            "type": "pydantic",
            "model": model_name,
            "count": len(self._models),
            "incremental_field": self.incremental_field,
            "id_field": self.id_field,
        }
