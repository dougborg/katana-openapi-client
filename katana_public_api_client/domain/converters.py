"""Converters from attrs API models to Pydantic domain models.

This module provides conversion utilities to transform the generated attrs models
(from the OpenAPI client) into clean Pydantic domain models optimized for ETL
and data processing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

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

    This function delegates to KatanaVariant.from_attrs(), which uses the
    auto-generated Pydantic model's from_attrs() for UNSET conversion.

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
        print(variant_domain.get_display_name())
        ```
    """
    from .variant import KatanaVariant

    return KatanaVariant.from_attrs(variant)


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

    This function delegates to KatanaProduct.from_attrs(), which uses the
    auto-generated Pydantic model's from_attrs() for UNSET conversion.

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

    return KatanaProduct.from_attrs(product)


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

    This function delegates to KatanaMaterial.from_attrs(), which uses the
    auto-generated Pydantic model's from_attrs() for UNSET conversion.

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

    return KatanaMaterial.from_attrs(material)


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

    This function delegates to KatanaService.from_attrs(), which uses the
    auto-generated Pydantic model's from_attrs() for UNSET conversion.

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

    return KatanaService.from_attrs(service)


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
