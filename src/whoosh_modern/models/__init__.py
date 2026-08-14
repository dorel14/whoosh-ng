"""Module d'intégration de modèles pour Whoosh-NG.

Fournit l'indexation automatique de modèles Python (dataclass, Pydantic,
SQLAlchemy, SQLModel, msgspec) vers Whoosh. Le ModelIndex mappe automatiquement
les types Python vers les types de champs Whoosh.

Auteur: SoniqueBay Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

from .auto import AutoIndexer
from .dataclass_integration import register_model as register_dataclass_model
from .model_index import ModelIndex
from .msgspec_integration import register_model as register_msgspec_model
from .pydantic_integration import register_model as register_pydantic_model
from .sqlalchemy_integration import register_model as register_sqlalchemy_model
from .sqlmodel_integration import register_model as register_sqlmodel_model
from .type_mapper import TypeMapper
from .types import SearchField, SearchOptions

__all__ = [
    "AutoIndexer",
    "ModelIndex",
    "SearchField",
    "SearchOptions",
    "TypeMapper",
    "index_document",
    "register_dataclass_model",
    "register_msgspec_model",
    "register_pydantic_model",
    "register_sqlalchemy_model",
    "register_sqlmodel_model",
    "remove_document",
]


def index_document(index: Any, instance: Any, on_error: str = "raise") -> None:
    """Indexe un document modèle dans un index Whoosh.

    Args:
        index: L'index Whoosh cible.
        instance: L'instance de modèle à indexer.
        on_error: Stratégie de gestion des erreurs ("raise", "log", "skip").
    """
    auto = AutoIndexer(index, on_error=on_error)
    auto.index(instance)


def remove_document(index: Any, instance: Any, on_error: str = "raise") -> None:
    """Supprime un document modèle de l'index Whoosh.

    Args:
        index: L'index Whoosh cible.
        instance: L'instance de modèle à supprimer.
        on_error: Stratégie de gestion des erreurs ("raise", "log", "skip").
    """
    auto = AutoIndexer(index, on_error=on_error)
    auto.remove(instance)
