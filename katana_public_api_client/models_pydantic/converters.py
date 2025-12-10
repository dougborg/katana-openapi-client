"""Batch conversion utilities for attrs <-> Pydantic model conversion.

This module provides convenience functions for converting API responses
and collections of models between attrs and Pydantic representations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, overload

from . import _registry
from ._base import KatanaPydanticBase

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ..client_types import Response


T = TypeVar("T", bound=KatanaPydanticBase)


@overload
def convert_response[T: KatanaPydanticBase](
    response: Response[None],
    pydantic_class: type[T],
) -> None: ...


@overload
def convert_response[T: KatanaPydanticBase](
    response: Response[list[object]],
    pydantic_class: type[T],
) -> list[T]: ...


@overload
def convert_response[T: KatanaPydanticBase](
    response: Response[object],
    pydantic_class: type[T],
) -> T: ...


def convert_response[T: KatanaPydanticBase](
    response: Response[object] | Response[list[object]] | Response[None],
    pydantic_class: type[T],
) -> T | list[T] | None:
    """Convert an API response's parsed data to Pydantic models.

    This is the recommended way to convert API responses when you want
    Pydantic models instead of attrs models.

    Args:
        response: The Response object from an API call.
        pydantic_class: The Pydantic model class to convert to.

    Returns:
        - None if response.parsed is None
        - A list of Pydantic models if response.parsed is a list
        - A single Pydantic model otherwise

    Example:
        ```python
        from katana_public_api_client.api.product import get_all_products
        from katana_public_api_client.models_pydantic import Product
        from katana_public_api_client.models_pydantic.converters import (
            convert_response,
        )

        response = await get_all_products.asyncio_detailed(client=client)
        products = convert_response(response, Product)  # list[Product]
        ```
    """
    if response.parsed is None:
        return None

    if isinstance(response.parsed, list):
        return batch_convert(response.parsed, pydantic_class)

    return pydantic_class.from_attrs(response.parsed)


def batch_convert[T: KatanaPydanticBase](
    attrs_objects: Sequence[object],
    pydantic_class: type[T],
) -> list[T]:
    """Convert a list of attrs objects to Pydantic models.

    Args:
        attrs_objects: A sequence of attrs model instances.
        pydantic_class: The Pydantic model class to convert to.

    Returns:
        A list of Pydantic model instances.

    Example:
        ```python
        from katana_public_api_client.models_pydantic import Product
        from katana_public_api_client.models_pydantic.converters import (
            batch_convert,
        )

        pydantic_products = batch_convert(attrs_products, Product)
        ```
    """
    return [pydantic_class.from_attrs(obj) for obj in attrs_objects]


def batch_convert_to_attrs(
    pydantic_objects: Sequence[KatanaPydanticBase],
) -> list[object]:
    """Convert a list of Pydantic models to attrs objects.

    Args:
        pydantic_objects: A sequence of Pydantic model instances.

    Returns:
        A list of attrs model instances.

    Example:
        ```python
        attrs_products = batch_convert_to_attrs(pydantic_products)
        ```
    """
    return [obj.to_attrs() for obj in pydantic_objects]


def to_pydantic(attrs_obj: object) -> KatanaPydanticBase | None:
    """Convert any registered attrs object to its Pydantic equivalent.

    This function automatically looks up the correct Pydantic class
    from the registry.

    Args:
        attrs_obj: An attrs model instance.

    Returns:
        The corresponding Pydantic model instance, or None if the class
        is not registered.

    Example:
        ```python
        from katana_public_api_client.models_pydantic.converters import (
            to_pydantic,
        )

        pydantic_product = to_pydantic(attrs_product)
        ```
    """
    if attrs_obj is None:
        return None

    pydantic_class = _registry.get_pydantic_class(type(attrs_obj))
    if pydantic_class is None:
        return None

    return pydantic_class.from_attrs(attrs_obj)


def to_attrs(pydantic_obj: KatanaPydanticBase) -> object | None:
    """Convert any registered Pydantic object to its attrs equivalent.

    This is equivalent to calling pydantic_obj.to_attrs() but provides
    a consistent functional interface.

    Args:
        pydantic_obj: A Pydantic model instance.

    Returns:
        The corresponding attrs model instance.

    Example:
        ```python
        from katana_public_api_client.models_pydantic.converters import to_attrs

        attrs_product = to_attrs(pydantic_product)
        ```
    """
    if pydantic_obj is None:
        return None

    return pydantic_obj.to_attrs()
