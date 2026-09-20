"""Base class for Katana Pydantic models with attrs conversion support.

This module provides the base class that all generated Pydantic models inherit from,
enabling bi-directional conversion between attrs models (used by the API transport layer)
and Pydantic models (for validation, serialization, and user-facing operations).
"""

from __future__ import annotations

import datetime
import enum
import types
from collections.abc import Callable
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
)

from pydantic import RootModel
from sqlmodel import SQLModel
from sqlmodel._compat import SQLModelConfig

if TYPE_CHECKING:
    pass

T = TypeVar("T", bound="KatanaPydanticBase")


def _is_unset(value: Any) -> bool:
    """Check if a value is the UNSET sentinel.

    The attrs models use an Unset class instance as a sentinel for
    fields that were not provided in the API response.
    """
    return type(value).__name__ == "Unset"


# Katana serializes some absent values as the literal *string* ``"null"`` or
# ``"undefined"`` rather than a JSON null — documented on serial-number transfer
# responses (see ``models/serial_number.py``: ``transaction_id`` may be
# ``"undefined"``, ``resource_id`` may be ``"null"``). The generated attrs
# parsers pass the raw string straight through (their ``_parse_<field>``
# fallbacks ``return`` the value on parse failure), so it only blows up when the
# value reaches a *typed* pydantic field — e.g. ``transaction_date:
# AwareDatetime`` or ``resource_id: int`` rejects ``"null"`` with a
# ``ValidationError``. In the typed-cache sync that single bad record would abort
# the whole batch. Coerce the sentinel to ``None`` for any field that cannot hold
# a string; leave string-typed fields (``transaction_id``, ``serial_number``)
# untouched so a legitimate value that happens to be ``"null"`` still survives.
_SENTINEL_NULL_STRINGS = frozenset({"null", "undefined"})


def _flatten_member_types(annotation: Any) -> list[Any]:
    """Flatten an annotation into its concrete member types.

    Unwraps ``Annotated[T, ...]`` to ``T`` and expands unions (both
    ``typing.Union`` and the ``X | Y`` ``types.UnionType`` form) so callers can
    reason about each alternative of an ``Optional``/union field.
    """
    origin = get_origin(annotation)
    if origin is Annotated:
        return _flatten_member_types(get_args(annotation)[0])
    if origin is Union or origin is types.UnionType:
        flattened: list[Any] = []
        for arg in get_args(annotation):
            flattened.extend(_flatten_member_types(arg))
        return flattened
    return [annotation]


def _annotation_accepts_str(annotation: Any) -> bool:
    """Whether a plain ``str`` is a valid value for a field of this annotation.

    ``True`` if any non-``None`` member is ``str`` / a ``str`` subclass (e.g. a
    ``StrEnum``) or a permissive non-class construct (``Any``, ``object``);
    ``False`` only when every member is a concrete non-string type. Used to gate
    the ``"null"``/``"undefined"`` sentinel coercion so string-bearing fields are
    never touched.
    """
    members = [m for m in _flatten_member_types(annotation) if m is not type(None)]
    if not members:
        return True
    for member in members:
        # Non-class constructs (``Any``, bare ``object`` reached via typing)
        # accept anything, so a string is valid — stay permissive.
        if not isinstance(member, type):
            return True
        if member is object or issubclass(member, str):
            return True
    return False


def _coerce_sentinel_null(value: Any, annotation: Any) -> Any:
    """Map Katana's literal ``"null"``/``"undefined"`` string to ``None`` when the
    target field cannot hold a string; otherwise return ``value`` unchanged."""
    if not isinstance(value, str) or value not in _SENTINEL_NULL_STRINGS:
        return value
    return None if not _annotation_accepts_str(annotation) else value


class KatanaPydanticBase(SQLModel):
    """Base class for all generated Pydantic models.

    Extends ``SQLModel`` (not plain ``pydantic.BaseModel``) so that subclasses
    can opt into SQLAlchemy table semantics via ``table=True`` without forking
    the generated model hierarchy. ``SQLModel`` is itself a pydantic
    ``BaseModel`` subclass, so existing consumers continue working unchanged.

    This base class provides:
    - Immutable (frozen) models for data integrity
    - Strict validation that forbids extra fields (request models)
    - BaseEntity overrides with extra="ignore" for API response tolerance
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

    # SQLModel re-declares ``model_config`` as ``SQLModelConfig`` (a ConfigDict
    # subclass adding ``table`` / ``registry``). Construct that exact type rather
    # than a plain ``ConfigDict`` so the assignment matches the inherited
    # attribute's declared type — ty 0.0.42+ flags the supertype as invalid.
    model_config = SQLModelConfig(
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
            ValueError: If attrs_obj is None or type doesn't match expected.
        """
        from . import _registry

        if attrs_obj is None:
            msg = f"Cannot convert None to {cls.__name__}"
            raise ValueError(msg)

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
                name = (
                    field_name[:-1]
                    if field_name.endswith("_") and not field_name.startswith("_")
                    else field_name
                )
                field_info = cls.model_fields.get(name)
                if field_info is not None and not field_info.is_required():
                    continue
                value = None
            elif isinstance(value, list):
                # Handle lists of nested objects
                value = [_convert_nested_value(item, _registry) for item in value]
            elif isinstance(value, dict) and field_name != "additional_properties":
                # Normalize an empty dict to None. Katana sometimes returns {}
                # instead of null for absent optional nested objects (e.g.
                # shipping_fee). An empty mapping cannot satisfy any schema
                # that has required fields, so treat it the same as null.
                if not value:
                    value = None
                else:
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

            # Normalize Katana's literal ``"null"``/``"undefined"`` sentinel to
            # None for typed (non-string) fields so a single quirky record
            # doesn't fail ``model_validate`` below (and, in the typed-cache
            # sync, abort the whole batch).
            model_field = cls.model_fields.get(pydantic_field_name)
            if model_field is not None:
                value = _coerce_sentinel_null(value, model_field.annotation)

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

        # The generated parser knows each field's actual wire shape, including
        # free-form object wrappers, unions and RootModel-backed legacy arrays.
        # Reconstruct through it instead of guessing nested types from generic
        # annotations or passing model_dump dictionaries to attrs constructors.
        data = self.model_dump(mode="json", by_alias=True, exclude_unset=True)
        attrs_fields = {
            attr.name: attr for attr in getattr(attrs_class, "__attrs_attrs__", ())
        }
        for field_name, field_info in type(self).model_fields.items():
            wire_name = field_info.serialization_alias or field_info.alias or field_name
            if wire_name in data and data[wire_name] is not None:
                data[wire_name] = _nested_wire_value(
                    getattr(self, field_name), data[wire_name]
                )
            attrs_name = (
                f"{field_name}_" if f"{field_name}_" in attrs_fields else field_name
            )
            attr = attrs_fields.get(attrs_name)
            if data.get(wire_name) is not None or attr is None:
                continue
            annotation = str(attr.type)
            if "Unset" in annotation and (
                field_name not in self.model_fields_set or "None" not in annotation
            ):
                data.pop(wire_name, None)
        if not hasattr(attrs_class, "from_dict"):
            raise TypeError(
                f"Registered attrs model {attrs_class.__name__} has no wire parser"
            )
        from_dict = cast(Callable[[dict[str, Any]], Any], attrs_class.from_dict)
        return from_dict(data)


def _nested_wire_value(value: Any, serialized: Any) -> Any:
    """Apply nested models' UNSET/null rules without losing maps or root arrays."""
    from . import _registry

    if isinstance(value, KatanaPydanticBase):
        if _registry.get_attrs_class(type(value)) is not None:
            return value.to_attrs().to_dict()
    elif isinstance(value, RootModel):
        return _nested_wire_value(value.root, serialized)
    elif isinstance(value, list) and isinstance(serialized, list):
        return [
            _nested_wire_value(item, wire)
            for item, wire in zip(value, serialized, strict=True)
        ]
    elif isinstance(value, dict) and isinstance(serialized, dict):
        return {
            key: _nested_wire_value(value[key], wire)
            for key, wire in serialized.items()
        }
    return serialized


def _convert_nested_value(value: Any, registry: Any) -> Any:
    """Convert a nested value from attrs to pydantic representation.

    Args:
        value: The value to convert.
        registry: The model registry module.

    Returns:
        The converted value suitable for a Pydantic model.

    Note:
        For attrs objects without a registered pydantic class, falls back
        to ``value.to_dict()`` when the attrs side exposes that method —
        covers the OpenAPI ``type: object`` (no $ref / no inline properties)
        case where the pydantic generator emits ``dict[str, Any]`` while
        the attrs generator still synthesizes a concrete class. When the
        attrs object also has no ``to_dict``, the value is returned as-is
        with a warning; pydantic validation will surface the mismatch
        downstream.
    """
    import logging

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
        # No registered pydantic class — happens when the OpenAPI spec
        # declares the field as a bare ``type: object`` (no $ref, no
        # inline properties), so the pydantic generator emits
        # ``dict[str, Any]`` while the attrs generator still synthesizes
        # a concrete class. The pydantic model expects a dict, so fall
        # back to ``to_dict()`` when the attrs side exposes it as a
        # callable (``callable`` rather than ``hasattr`` guards against
        # an exotic non-callable ``to_dict`` attribute, which would
        # otherwise raise ``TypeError`` at call time).
        to_dict_fn = getattr(value, "to_dict", None)
        if callable(to_dict_fn):
            return to_dict_fn()
        # Last resort: warn and pass through. Pydantic validation will
        # surface the type mismatch loudly enough.
        logger = logging.getLogger(__name__)
        logger.warning(
            "Nested attrs class %s is not registered in the pydantic registry "
            "and has no ``to_dict`` fallback. Conversion may fail or produce "
            "unexpected results.",
            type(value).__name__,
        )

    return value
