"""Converters from attrs API models to Pydantic domain models.

This module provides conversion utilities to transform the generated attrs models
(from the OpenAPI client) into clean Pydantic domain models optimized for ETL
and data processing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, cast

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.variant import Variant
    from .variant import KatanaVariant

T = TypeVar("T")


def unwrap_unset(value: T | Unset, default: T | None = None) -> T | None:
    """Unwrap an Unset sentinel value.

    Args:
        value: Value that might be Unset
        default: Default value to return if Unset

    Returns:
        The unwrapped value, or default if value is Unset

    Example:
        ```python
        from katana_public_api_client.client_types import UNSET

        unwrap_unset(42)  # 42
        unwrap_unset(UNSET)  # None
        unwrap_unset(UNSET, 0)  # 0
        ```
    """
    return default if isinstance(value, type(UNSET)) else value  # type: ignore[return-value]


def variant_to_katana(variant: Variant) -> KatanaVariant:
    """Convert attrs Variant model to Pydantic KatanaVariant.

    Handles:
    - Unwrapping Unset sentinel values
    - Extracting nested product_or_material name
    - Converting config_attributes to dicts
    - Converting custom_fields to dicts

    Args:
        variant: attrs Variant model from API response

    Returns:
        KatanaVariant with all fields populated

    Example:
        ```python
        from katana_public_api_client.api.variant import get_variant
        from katana_public_api_client.utils import unwrap

        response = await get_variant.asyncio_detailed(client=client, id=123)
        variant_attrs = unwrap(response)
        variant_domain = variant_to_katana(variant_attrs)

        # Now use domain model features
        print(variant_domain.profit_margin)
        print(variant_domain.get_display_name())
        ```
    """
    from .variant import KatanaVariant

    # Extract product/material name from nested object if available
    product_or_material_name = unwrap_unset(variant.product_or_material_name)

    # If not in flat field, try nested object (VariantResponse with extend)
    if not product_or_material_name and hasattr(variant, "product_or_material"):
        pom = unwrap_unset(variant.product_or_material)
        if pom and hasattr(pom, "name"):
            product_or_material_name = unwrap_unset(pom.name)

    # Convert config attributes to simple dicts
    config_attrs: list[dict[str, str]] = []
    if config_list := unwrap_unset(variant.config_attributes, []):
        for attr in config_list:
            config_name = unwrap_unset(
                cast(str | Unset, getattr(attr, "config_name", None))
            )
            config_value = unwrap_unset(
                cast(str | Unset, getattr(attr, "config_value", None))
            )
            config_attrs.append(
                {
                    "config_name": config_name or "",
                    "config_value": config_value or "",
                }
            )

    # Convert custom fields to simple dicts
    custom: list[dict[str, str]] = []
    if custom_list := unwrap_unset(variant.custom_fields, []):
        for field in custom_list:
            field_name = unwrap_unset(
                cast(str | Unset, getattr(field, "field_name", None))
            )
            field_value = unwrap_unset(
                cast(str | Unset, getattr(field, "field_value", None))
            )
            custom.append(
                {
                    "field_name": field_name or "",
                    "field_value": field_value or "",
                }
            )

    # Extract type value from enum if present
    type_value = None
    if type_enum := unwrap_unset(variant.type_):
        type_value = getattr(type_enum, "value", None)

    return KatanaVariant(
        id=variant.id,
        sku=unwrap_unset(variant.sku) or "",  # Ensure str, not None
        sales_price=unwrap_unset(variant.sales_price),
        purchase_price=unwrap_unset(variant.purchase_price),
        product_id=unwrap_unset(variant.product_id),
        material_id=unwrap_unset(variant.material_id),
        product_or_material_name=product_or_material_name,
        type=type_value,  # Pydantic uses 'type' not 'type_'
        internal_barcode=unwrap_unset(variant.internal_barcode),
        registered_barcode=unwrap_unset(variant.registered_barcode),
        supplier_item_codes=unwrap_unset(variant.supplier_item_codes)
        or [],  # Ensure list
        lead_time=unwrap_unset(variant.lead_time),
        minimum_order_quantity=unwrap_unset(variant.minimum_order_quantity),
        config_attributes=config_attrs,
        custom_fields=custom,
        created_at=unwrap_unset(variant.created_at),
        updated_at=unwrap_unset(variant.updated_at),
        deleted_at=unwrap_unset(variant.deleted_at),
    )


def variants_to_katana(variants: list[Variant]) -> list[KatanaVariant]:
    """Convert list of attrs Variant models to list of KatanaVariant.

    Args:
        variants: List of attrs Variant models

    Returns:
        List of KatanaVariant models

    Example:
        ```python
        from katana_public_api_client.api.variant import get_all_variants
        from katana_public_api_client.utils import unwrap_data

        response = await get_all_variants.asyncio_detailed(client=client)
        variants_attrs = unwrap_data(response)
        variants_domain = variants_to_katana(variants_attrs)

        # Now use domain model features
        high_margin = [v for v in variants_domain if v.is_high_margin]
        ```
    """
    return [variant_to_katana(v) for v in variants]


__all__ = [
    "unwrap_unset",
    "variant_to_katana",
    "variants_to_katana",
]
