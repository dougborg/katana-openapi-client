"""Converters from attrs API models to Pydantic domain models.

This module provides conversion utilities to transform the generated attrs models
(from the OpenAPI client) into clean Pydantic domain models optimized for ETL
and data processing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, cast

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.material import Material
    from ..models.product import Product
    from ..models.service import Service
    from ..models.variant import Variant
    from .material import KatanaMaterial
    from .product import KatanaProduct
    from .service import KatanaService
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
    return default if value is UNSET else value  # type: ignore[return-value]


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
    # Note: product_or_material_name flat field doesn't exist in API
    # Only product_or_material.name exists (when extend=product_or_material is used)
    product_or_material_name = None
    if hasattr(variant, "product_or_material"):
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


def product_to_katana(product: Product) -> KatanaProduct:
    """Convert attrs Product model to Pydantic KatanaProduct.

    Handles:
    - Unwrapping Unset sentinel values
    - Extracting enum values
    - Converting nested variants/configs to counts

    Args:
        product: attrs Product model from API response

    Returns:
        KatanaProduct with all fields populated

    Example:
        ```python
        from katana_public_api_client.api.product import get_product
        from katana_public_api_client.utils import unwrap

        response = await get_product.asyncio_detailed(client=client, id=123)
        product_attrs = unwrap(response)
        product_domain = product_to_katana(product_attrs)

        # Now use domain model features
        print(product_domain.get_display_name())
        print(product_domain.to_csv_row())
        ```
    """
    from .product import KatanaProduct

    # Count nested collections
    variants_list = unwrap_unset(product.variants, [])
    configs_list = unwrap_unset(product.configs, [])
    variant_count = len(variants_list) if variants_list else 0
    config_count = len(configs_list) if configs_list else 0

    # Handle archived_at datetime conversion
    archived_at_raw = unwrap_unset(product.archived_at)
    archived_at_str: str | None = None
    if archived_at_raw and hasattr(archived_at_raw, "isoformat"):
        archived_at_str = archived_at_raw.isoformat()

    return KatanaProduct(
        id=product.id,
        name=product.name,
        type="product",  # Always "product" literal
        uom=unwrap_unset(product.uom),
        category_name=unwrap_unset(product.category_name),
        is_sellable=unwrap_unset(product.is_sellable),
        is_producible=unwrap_unset(product.is_producible),
        is_purchasable=unwrap_unset(product.is_purchasable),
        is_auto_assembly=unwrap_unset(product.is_auto_assembly),
        batch_tracked=unwrap_unset(product.batch_tracked),
        serial_tracked=unwrap_unset(product.serial_tracked),
        operations_in_sequence=unwrap_unset(product.operations_in_sequence),
        default_supplier_id=unwrap_unset(product.default_supplier_id),
        lead_time=unwrap_unset(product.lead_time),
        minimum_order_quantity=unwrap_unset(product.minimum_order_quantity),
        purchase_uom=unwrap_unset(product.purchase_uom),
        purchase_uom_conversion_rate=unwrap_unset(product.purchase_uom_conversion_rate),
        additional_info=unwrap_unset(product.additional_info),
        custom_field_collection_id=unwrap_unset(product.custom_field_collection_id),
        archived_at=archived_at_str,
        variant_count=variant_count,
        config_count=config_count,
        created_at=unwrap_unset(product.created_at),
        updated_at=unwrap_unset(product.updated_at),
        deleted_at=None,  # Product model has archived_at, not deleted_at
    )


def products_to_katana(products: list[Product]) -> list[KatanaProduct]:
    """Convert list of attrs Product models to list of KatanaProduct.

    Args:
        products: List of attrs Product models

    Returns:
        List of KatanaProduct models

    Example:
        ```python
        from katana_public_api_client.api.product import get_all_products
        from katana_public_api_client.utils import unwrap_data

        response = await get_all_products.asyncio_detailed(client=client)
        products_attrs = unwrap_data(response)
        products_domain = products_to_katana(products_attrs)

        # Now use domain model features
        sellable = [p for p in products_domain if p.is_sellable]
        ```
    """
    return [product_to_katana(p) for p in products]


def material_to_katana(material: Material) -> KatanaMaterial:
    """Convert attrs Material model to Pydantic KatanaMaterial.

    Handles:
    - Unwrapping Unset sentinel values
    - Extracting enum values
    - Converting nested variants/configs to counts

    Args:
        material: attrs Material model from API response

    Returns:
        KatanaMaterial with all fields populated

    Example:
        ```python
        from katana_public_api_client.api.material import get_material
        from katana_public_api_client.utils import unwrap

        response = await get_material.asyncio_detailed(client=client, id=123)
        material_attrs = unwrap(response)
        material_domain = material_to_katana(material_attrs)

        # Now use domain model features
        print(material_domain.get_display_name())
        print(material_domain.to_csv_row())
        ```
    """
    from .material import KatanaMaterial

    # Count nested collections
    variants_list = unwrap_unset(material.variants, [])
    configs_list = unwrap_unset(material.configs, [])
    variant_count = len(variants_list) if variants_list else 0
    config_count = len(configs_list) if configs_list else 0

    # Handle archived_at datetime conversion
    archived_at_raw = unwrap_unset(material.archived_at)
    archived_at_str: str | None = None
    if archived_at_raw and hasattr(archived_at_raw, "isoformat"):
        archived_at_str = archived_at_raw.isoformat()

    return KatanaMaterial(
        id=material.id,
        name=material.name,
        type="material",  # Always "material" literal
        uom=unwrap_unset(material.uom),
        category_name=unwrap_unset(material.category_name),
        is_sellable=unwrap_unset(material.is_sellable),
        batch_tracked=unwrap_unset(material.batch_tracked),
        default_supplier_id=unwrap_unset(material.default_supplier_id),
        purchase_uom=unwrap_unset(material.purchase_uom),
        purchase_uom_conversion_rate=unwrap_unset(
            material.purchase_uom_conversion_rate
        ),
        additional_info=unwrap_unset(material.additional_info),
        custom_field_collection_id=unwrap_unset(material.custom_field_collection_id),
        archived_at=archived_at_str,
        variant_count=variant_count,
        config_count=config_count,
        created_at=unwrap_unset(material.created_at),
        updated_at=unwrap_unset(material.updated_at),
        deleted_at=unwrap_unset(material.deleted_at)
        if hasattr(material, "deleted_at")
        else None,
    )


def materials_to_katana(materials: list[Material]) -> list[KatanaMaterial]:
    """Convert list of attrs Material models to list of KatanaMaterial.

    Args:
        materials: List of attrs Material models

    Returns:
        List of KatanaMaterial models

    Example:
        ```python
        from katana_public_api_client.api.material import get_all_materials
        from katana_public_api_client.utils import unwrap_data

        response = await get_all_materials.asyncio_detailed(client=client)
        materials_attrs = unwrap_data(response)
        materials_domain = materials_to_katana(materials_attrs)

        # Now use domain model features
        batch_tracked = [m for m in materials_domain if m.batch_tracked]
        ```
    """
    return [material_to_katana(m) for m in materials]


def service_to_katana(service: Service) -> KatanaService:
    """Convert attrs Service model to Pydantic KatanaService.

    Handles:
    - Unwrapping Unset sentinel values
    - Extracting enum values
    - Converting nested variants to count

    Args:
        service: attrs Service model from API response

    Returns:
        KatanaService with all fields populated

    Example:
        ```python
        from katana_public_api_client.api.service import get_service
        from katana_public_api_client.utils import unwrap

        response = await get_service.asyncio_detailed(client=client, id=123)
        service_attrs = unwrap(response)
        service_domain = service_to_katana(service_attrs)

        # Now use domain model features
        print(service_domain.get_display_name())
        print(service_domain.to_csv_row())
        ```
    """
    from .service import KatanaService

    # Extract type value from enum if present
    type_enum = unwrap_unset(service.type_)
    type_value = getattr(type_enum, "value", None) if type_enum else None

    # Count nested collections
    variants_list = unwrap_unset(service.variants, [])
    variant_count = len(variants_list) if variants_list else 0

    return KatanaService(
        id=service.id,
        name=unwrap_unset(service.name),
        type=type_value,
        uom=unwrap_unset(service.uom),
        category_name=unwrap_unset(service.category_name),
        is_sellable=unwrap_unset(service.is_sellable),
        additional_info=unwrap_unset(service.additional_info),
        custom_field_collection_id=unwrap_unset(service.custom_field_collection_id),
        archived_at=unwrap_unset(service.archived_at),
        variant_count=variant_count,
        created_at=unwrap_unset(service.created_at),
        updated_at=unwrap_unset(service.updated_at),
        deleted_at=None,  # Service model uses deleted_at as string, not datetime
    )


def services_to_katana(services: list[Service]) -> list[KatanaService]:
    """Convert list of attrs Service models to list of KatanaService.

    Args:
        services: List of attrs Service models

    Returns:
        List of KatanaService models

    Example:
        ```python
        from katana_public_api_client.api.service import get_all_services
        from katana_public_api_client.utils import unwrap_data

        response = await get_all_services.asyncio_detailed(client=client)
        services_attrs = unwrap_data(response)
        services_domain = services_to_katana(services_attrs)

        # Now use domain model features
        sellable = [s for s in services_domain if s.is_sellable]
        ```
    """
    return [service_to_katana(s) for s in services]


__all__ = [
    "material_to_katana",
    "materials_to_katana",
    "product_to_katana",
    "products_to_katana",
    "service_to_katana",
    "services_to_katana",
    "unwrap_unset",
    "variant_to_katana",
    "variants_to_katana",
]
