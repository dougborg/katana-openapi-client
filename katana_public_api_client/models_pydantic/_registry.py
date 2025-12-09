"""Registry for mapping between attrs and Pydantic model classes.

This module provides a registry that maps attrs model classes to their
corresponding Pydantic model classes and vice versa. This is essential
for the bi-directional conversion functionality in _base.py.

The registry is populated automatically when models are generated,
via the _auto_registry.py module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._base import KatanaPydanticBase

# Registries mapping class names and types
_attrs_to_pydantic: dict[type, type[KatanaPydanticBase]] = {}
_pydantic_to_attrs: dict[type[KatanaPydanticBase], type] = {}
_attrs_name_to_class: dict[str, type] = {}
_pydantic_name_to_class: dict[str, type[KatanaPydanticBase]] = {}


def register(attrs_class: type, pydantic_class: type[KatanaPydanticBase]) -> None:
    """Register a mapping between an attrs class and a Pydantic class.

    This function should be called for each model pair after generation.
    It enables the from_attrs() and to_attrs() conversion methods to work.

    Args:
        attrs_class: The attrs model class (from models/).
        pydantic_class: The corresponding Pydantic model class.
    """
    _attrs_to_pydantic[attrs_class] = pydantic_class
    _pydantic_to_attrs[pydantic_class] = attrs_class
    _attrs_name_to_class[attrs_class.__name__] = attrs_class
    _pydantic_name_to_class[pydantic_class.__name__] = pydantic_class

    # Also set the _attrs_model class variable on the pydantic class
    pydantic_class._attrs_model = attrs_class


def get_pydantic_class(attrs_class: type) -> type[KatanaPydanticBase] | None:
    """Get the Pydantic class for a given attrs class.

    Args:
        attrs_class: An attrs model class.

    Returns:
        The corresponding Pydantic model class, or None if not registered.
    """
    return _attrs_to_pydantic.get(attrs_class)


def get_attrs_class(pydantic_class: type[KatanaPydanticBase]) -> type | None:
    """Get the attrs class for a given Pydantic class.

    Args:
        pydantic_class: A Pydantic model class.

    Returns:
        The corresponding attrs model class, or None if not registered.
    """
    return _pydantic_to_attrs.get(pydantic_class)


def get_pydantic_class_by_name(name: str) -> type[KatanaPydanticBase] | None:
    """Get a Pydantic class by its name.

    Args:
        name: The class name to look up.

    Returns:
        The Pydantic model class, or None if not found.
    """
    return _pydantic_name_to_class.get(name)


def get_attrs_class_by_name(name: str) -> type | None:
    """Get an attrs class by its name.

    Args:
        name: The class name to look up.

    Returns:
        The attrs model class, or None if not found.
    """
    return _attrs_name_to_class.get(name)


def list_registered_models() -> list[tuple[str, str]]:
    """List all registered model pairs.

    Returns:
        List of (attrs_class_name, pydantic_class_name) tuples.
    """
    return [
        (attrs_cls.__name__, pydantic_cls.__name__)
        for attrs_cls, pydantic_cls in _attrs_to_pydantic.items()
    ]


def is_registered(model_class: type) -> bool:
    """Check if a model class is registered (either attrs or pydantic).

    Args:
        model_class: A model class to check.

    Returns:
        True if the class is registered in either direction.
    """
    return model_class in _attrs_to_pydantic or model_class in _pydantic_to_attrs


def clear_registry() -> None:
    """Clear all registrations. Mainly for testing purposes."""
    _attrs_to_pydantic.clear()
    _pydantic_to_attrs.clear()
    _attrs_name_to_class.clear()
    _pydantic_name_to_class.clear()


def get_registration_stats() -> dict[str, Any]:
    """Get statistics about the current registry state.

    Returns:
        Dictionary with counts and other stats.
    """
    return {
        "total_pairs": len(_attrs_to_pydantic),
        "attrs_classes": len(_attrs_name_to_class),
        "pydantic_classes": len(_pydantic_name_to_class),
    }
