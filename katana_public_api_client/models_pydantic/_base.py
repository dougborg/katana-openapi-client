"""Base class for Katana Pydantic models with attrs conversion support.

This module provides the base class that all generated Pydantic models inherit from,
enabling bi-directional conversion between attrs models (used by the API transport layer)
and Pydantic models (for validation, serialization, and user-facing operations).
"""

from __future__ import annotations

import datetime
import enum
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar, cast, get_args, get_origin

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    pass

T = TypeVar("T", bound="KatanaPydanticBase")


def _is_unset(value: Any) -> bool:
    """Check if a value is the UNSET sentinel.

    The attrs models use an Unset class instance as a sentinel for
    fields that were not provided in the API response.
    """
    return type(value).__name__ == "Unset"


def _get_unset() -> Any:
    """Get the UNSET sentinel value from client_types."""
    from ..client_types import UNSET

    return UNSET


class KatanaPydanticBase(BaseModel):
    """Base class for all generated Pydantic models.

    This base class provides:
    - Immutable (frozen) models for data integrity
    - Strict validation that forbids extra fields
    - Bi-directional conversion with attrs models

    Example:
        ```python
        from katana_public_api_client.models import Product as AttrsProduct
        from katana_public_api_client.models_pydantic import (
            Product as PydanticProduct,
        )

        # Convert attrs -> pydantic
        attrs_product = await get_product(client, 123)
        pydantic_product = PydanticProduct.from_attrs(attrs_product)

        # Convert pydantic -> attrs (for API calls)
        attrs_product = pydantic_product.to_attrs()
        ```
    """

    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True,
        extra="forbid",
        # Use enum values for serialization
        use_enum_values=False,
        # Validate default values
        validate_default=True,
    )

    # Class variable to store the corresponding attrs model class
    # This is set by the registry after model generation
    _attrs_model: ClassVar[type | None] = None

    @classmethod
    def from_attrs(cls: type[T], attrs_obj: Any) -> T:
        """Convert an attrs model instance to this Pydantic model.

        Handles:
        - UNSET sentinel -> None conversion
        - Nested object conversion (via registry lookup)
        - Enum value extraction
        - Field name mapping (type_ -> type)

        Args:
            attrs_obj: An instance of the corresponding attrs model.

        Returns:
            A new instance of this Pydantic model.

        Raises:
            ValueError: If the attrs object type doesn't match the expected type.
        """
        from . import _registry

        if attrs_obj is None:
            return None  # type: ignore[return-value]

        # Extract field values from attrs object
        data: dict[str, Any] = {}

        # Get the attrs object's fields
        if hasattr(attrs_obj, "__attrs_attrs__"):
            field_names = [attr.name for attr in attrs_obj.__attrs_attrs__]
        else:
            # Fallback: use __dict__ for non-attrs objects
            field_names = list(vars(attrs_obj).keys())

        for field_name in field_names:
            value = getattr(attrs_obj, field_name)

            # Skip additional_properties field (handled separately)
            if field_name == "additional_properties":
                continue

            # Convert UNSET -> None
            if _is_unset(value):
                value = None
            elif isinstance(value, list):
                # Handle lists of nested objects
                value = [_convert_nested_value(item, _registry) for item in value]
            elif isinstance(value, dict) and field_name != "additional_properties":
                # Handle dict values (but not additional_properties)
                value = {
                    k: _convert_nested_value(v, _registry) for k, v in value.items()
                }
            else:
                value = _convert_nested_value(value, _registry)

            # Map field names (type_ -> type for pydantic)
            pydantic_field_name = field_name
            if field_name.endswith("_") and not field_name.startswith("_"):
                # Remove trailing underscore for pydantic field
                pydantic_field_name = field_name[:-1]

            data[pydantic_field_name] = value

        return cls.model_validate(data)

    def to_attrs(self) -> Any:
        """Convert this Pydantic model to the corresponding attrs model.

        Handles:
        - None -> UNSET conversion (where appropriate based on attrs field types)
        - Nested object conversion (via registry lookup)
        - Enum reconstruction from values
        - Field name mapping (type -> type_)

        Returns:
            An instance of the corresponding attrs model.

        Raises:
            RuntimeError: If no attrs model is registered for this class.
        """
        from . import _registry

        attrs_class = _registry.get_attrs_class(type(self))
        if attrs_class is None:
            msg = f"No attrs model registered for {type(self).__name__}"
            raise RuntimeError(msg)

        # Get UNSET sentinel
        unset = _get_unset()

        # Build kwargs for attrs constructor
        kwargs: dict[str, Any] = {}

        # Get attrs field info to know which fields accept UNSET
        attrs_fields: dict[str, Any] = {}
        if hasattr(attrs_class, "__attrs_attrs__"):
            attrs_attrs = cast(Iterable[Any], attrs_class.__attrs_attrs__)
            for attr in attrs_attrs:
                attrs_fields[attr.name] = attr

        for field_name, field_value in self.model_dump().items():
            # Map field names (type -> type_ for attrs)
            attrs_field_name = field_name
            # Check if attrs model uses trailing underscore (skip private fields)
            if not field_name.startswith("_") and f"{field_name}_" in attrs_fields:
                attrs_field_name = f"{field_name}_"

            # Convert None -> UNSET where the attrs field type includes Unset
            converted_value = field_value
            if field_value is None and attrs_field_name in attrs_fields:
                # Check if the field type includes Unset
                attr_info = attrs_fields[attrs_field_name]
                type_hint = attr_info.type if hasattr(attr_info, "type") else None
                if type_hint is not None and "Unset" in str(type_hint):
                    converted_value = unset

            # Handle nested objects
            if isinstance(converted_value, dict):
                # Try to find the corresponding attrs class for nested objects
                nested_pydantic_class = _get_field_type(type(self), field_name)
                if nested_pydantic_class and issubclass(
                    nested_pydantic_class, KatanaPydanticBase
                ):
                    nested_attrs_class = _registry.get_attrs_class(
                        nested_pydantic_class
                    )
                    if nested_attrs_class and hasattr(nested_attrs_class, "from_dict"):
                        from_dict_fn = cast(
                            Callable[[dict[str, Any]], Any],
                            nested_attrs_class.from_dict,
                        )
                        converted_value = from_dict_fn(converted_value)
            elif isinstance(converted_value, list):
                # Handle lists of nested objects
                new_list = []
                for item in converted_value:
                    if isinstance(item, dict):
                        # We'd need more type info to convert dicts in lists properly
                        new_list.append(item)
                    else:
                        new_list.append(
                            _convert_to_attrs_value(item, _registry, attrs_fields, None)
                        )
                converted_value = new_list
            else:
                converted_value = _convert_to_attrs_value(
                    converted_value, _registry, attrs_fields, attrs_field_name
                )

            kwargs[attrs_field_name] = converted_value

        return attrs_class(**kwargs)


def _convert_nested_value(value: Any, registry: Any) -> Any:
    """Convert a nested value from attrs to pydantic representation."""
    if value is None:
        return None

    if _is_unset(value):
        return None

    # Handle enums - extract the value
    if isinstance(value, enum.Enum):
        return value.value

    # Handle datetime objects
    if isinstance(value, datetime.datetime):
        return value

    # Handle datetime.date objects
    if isinstance(value, datetime.date):
        return value

    # Handle nested attrs objects
    if hasattr(value, "__attrs_attrs__"):
        pydantic_class = registry.get_pydantic_class(type(value))
        if pydantic_class:
            return pydantic_class.from_attrs(value)

    return value


def _convert_to_attrs_value(
    value: Any,
    registry: Any,
    attrs_fields: dict[str, Any],
    field_name: str | None,
) -> Any:
    """Convert a value from pydantic to attrs representation."""
    if value is None:
        return value

    # Handle pydantic models -> attrs models
    if isinstance(value, KatanaPydanticBase):
        return value.to_attrs()

    # Handle enums - the attrs model expects enum instances
    if isinstance(value, str) and field_name and field_name in attrs_fields:
        attr_info = attrs_fields[field_name]
        type_hint = attr_info.type if hasattr(attr_info, "type") else None
        # Try to reconstruct enum from string value
        if type_hint:
            enum_class = _extract_enum_class(type_hint)
            if enum_class:
                try:
                    return enum_class(value)
                except ValueError:
                    pass

    return value


def _extract_enum_class(type_hint: Any) -> type[enum.Enum] | None:
    """Extract an enum class from a type hint."""
    # Handle Union types
    origin = get_origin(type_hint)
    if origin is not None:
        args = get_args(type_hint)
        for arg in args:
            result = _extract_enum_class(arg)
            if result:
                return result
        return None

    # Check if it's an enum class
    if isinstance(type_hint, type) and issubclass(type_hint, enum.Enum):
        return type_hint

    return None


def _get_field_type(
    model_class: type[KatanaPydanticBase], field_name: str
) -> type | None:
    """Get the type of a field from a pydantic model class."""
    if field_name in model_class.model_fields:
        field_info = model_class.model_fields[field_name]
        annotation = field_info.annotation
        if annotation:
            # Handle Optional types
            origin = get_origin(annotation)
            if origin is not None:
                args = get_args(annotation)
                for arg in args:
                    if arg is not type(None):
                        return arg
            return annotation
    return None
