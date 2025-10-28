"""Variant catalog operations."""

from __future__ import annotations

from typing import Any, cast

from katana_public_api_client.api.variant import (
    create_variant,
    delete_variant,
    get_all_variants,
    get_variant,
    update_variant,
)
from katana_public_api_client.helpers.base import Base
from katana_public_api_client.models.create_variant_request import CreateVariantRequest
from katana_public_api_client.models.update_variant_request import UpdateVariantRequest
from katana_public_api_client.models.variant import Variant
from katana_public_api_client.utils import unwrap, unwrap_data


class Variants(Base):
    """Variant catalog management.

    Provides CRUD operations for product variants in the Katana catalog.

    Example:
        >>> async with KatanaClient() as client:
        ...     # CRUD operations
        ...     variants = await client.variants.list()
        ...     variant = await client.variants.get(123)
        ...     new_variant = await client.variants.create({"name": "Large"})
    """

    async def list(self, **filters: Any) -> list[Variant]:
        """List all variants with optional filters.

        Args:
            **filters: Filtering parameters.

        Returns:
            List of Variant objects.

        Example:
            >>> variants = await client.variants.list(limit=100)
        """
        response = await get_all_variants.asyncio_detailed(
            client=self._client,
            **filters,
        )
        return unwrap_data(response)

    async def get(self, variant_id: int) -> Variant:
        """Get a specific variant by ID.

        Args:
            variant_id: The variant ID.

        Returns:
            Variant object.

        Example:
            >>> variant = await client.variants.get(123)
        """
        response = await get_variant.asyncio_detailed(
            client=self._client,
            id=variant_id,
        )
        # unwrap() raises on errors, so cast is safe
        return cast(Variant, unwrap(response))

    async def create(self, variant_data: CreateVariantRequest) -> Variant:
        """Create a new variant.

        Args:
            variant_data: CreateVariantRequest model with variant details.

        Returns:
            Created Variant object.

        Example:
            >>> from katana_public_api_client.models import CreateVariantRequest
            >>> new_variant = await client.variants.create(
            ...     CreateVariantRequest(name="Large", product_id=123)
            ... )
        """
        response = await create_variant.asyncio_detailed(
            client=self._client,
            body=variant_data,
        )
        # unwrap() raises on errors, so cast is safe
        return cast(Variant, unwrap(response))

    async def update(
        self, variant_id: int, variant_data: UpdateVariantRequest
    ) -> Variant:
        """Update an existing variant.

        Args:
            variant_id: The variant ID to update.
            variant_data: UpdateVariantRequest model with fields to update.

        Returns:
            Updated Variant object.

        Example:
            >>> from katana_public_api_client.models import UpdateVariantRequest
            >>> updated = await client.variants.update(
            ...     123, UpdateVariantRequest(name="XL")
            ... )
        """
        response = await update_variant.asyncio_detailed(
            client=self._client,
            id=variant_id,
            body=variant_data,
        )
        # unwrap() raises on errors, so cast is safe
        return cast(Variant, unwrap(response))

    async def delete(self, variant_id: int) -> None:
        """Delete a variant.

        Args:
            variant_id: The variant ID to delete.

        Example:
            >>> await client.variants.delete(123)
        """
        await delete_variant.asyncio_detailed(
            client=self._client,
            id=variant_id,
        )

    async def search(self, query: str, limit: int = 50) -> list[Variant]:
        """Search variants by SKU or parent product/material name (fuzzy search).

        Used by: MCP tool search_products

        This fetches all variants with their parent product/material information
        and performs client-side fuzzy searching.

        Args:
            query: Search query to match against SKU or product/material name (case-insensitive).
            limit: Maximum number of results to return.

        Returns:
            List of matching Variant objects with product_or_material_name populated.

        Example:
            >>> variants = await client.variants.search("fox", limit=10)
            >>> for variant in variants:
            ...     print(f"{variant.sku}: {variant.product_or_material_name}")
        """
        # Fetch all variants with parent product/material info
        response = await get_all_variants.asyncio_detailed(
            client=self._client,
            extend=["product_or_material"],
            limit=1000,  # Fetch up to 1000 variants for searching
        )
        all_variants = unwrap_data(response)

        # Perform case-insensitive fuzzy search on SKU and product/material name
        query_lower = query.lower()
        matches = []

        for variant in all_variants:
            # Check variant SKU
            if variant.sku and query_lower in variant.sku.lower():
                matches.append(variant)
                continue

            # Check parent product/material name
            if (
                variant.product_or_material_name
                and query_lower in variant.product_or_material_name.lower()
            ):
                matches.append(variant)
                continue

        return matches[:limit]
