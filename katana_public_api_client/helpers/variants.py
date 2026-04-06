"""Variant catalog operations."""

from __future__ import annotations

import logging

# Import list from builtins to avoid shadowing by our list() method
from builtins import list as List
from typing import Any

from katana_public_api_client.api.variant import (
    create_variant,
    delete_variant,
    get_all_variants,
    get_variant,
    update_variant,
)
from katana_public_api_client.domain import KatanaVariant, variants_to_katana
from katana_public_api_client.domain.converters import variant_to_katana
from katana_public_api_client.helpers.base import Base
from katana_public_api_client.models.create_variant_request import CreateVariantRequest
from katana_public_api_client.models.get_all_variants_extend_item import (
    GetAllVariantsExtendItem,
)
from katana_public_api_client.models.update_variant_request import UpdateVariantRequest
from katana_public_api_client.models.variant import Variant
from katana_public_api_client.utils import unwrap_as, unwrap_data

logger = logging.getLogger(__name__)


class Variants(Base):
    """Variant catalog management.

    Provides CRUD operations and search for product variants in the Katana catalog.

    Note: Caching is handled by the MCP server's CatalogCache (SQLite + FTS5),
    not by this client-level helper. The client is a pure API wrapper.

    Example:
        >>> async with KatanaClient() as client:
        ...     variants = await client.variants.list()
        ...     variant = await client.variants.get(123)
        ...     results = await client.variants.search("fox fork")
    """

    async def list(self, **filters: Any) -> List[KatanaVariant]:
        """List all variants with optional filters.

        Args:
            **filters: Filtering parameters.

        Returns:
            List of KatanaVariant objects.

        Example:
            >>> variants = await client.variants.list(limit=100)
            >>> for v in variants:
            ...     print(f"{v.get_display_name()}: {v.profit_margin}%")
        """
        response = await get_all_variants.asyncio_detailed(
            client=self._client,
            **filters,
        )
        attrs_variants = unwrap_data(response)
        return variants_to_katana(attrs_variants)

    async def get(self, variant_id: int) -> KatanaVariant:
        """Get a specific variant by ID.

        Args:
            variant_id: The variant ID.

        Returns:
            KatanaVariant object.

        Example:
            >>> variant = await client.variants.get(123)
            >>> print(variant.get_display_name())
            >>> print(f"Profit margin: {variant.profit_margin}%")
        """
        response = await get_variant.asyncio_detailed(
            client=self._client,
            id=variant_id,
        )
        attrs_variant = unwrap_as(response, Variant)
        return variant_to_katana(attrs_variant)

    async def create(self, variant_data: CreateVariantRequest) -> KatanaVariant:
        """Create a new variant.

        Note: Clears the variant cache after creation.

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
        attrs_variant = unwrap_as(response, Variant)
        return variant_to_katana(attrs_variant)

    async def update(
        self, variant_id: int, variant_data: UpdateVariantRequest
    ) -> KatanaVariant:
        """Update an existing variant.

        Note: Clears the variant cache after update.

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
        attrs_variant = unwrap_as(response, Variant)
        return variant_to_katana(attrs_variant)

    async def delete(self, variant_id: int) -> None:
        """Delete a variant.

        Note: Clears the variant cache after deletion.

        Args:
            variant_id: The variant ID to delete.

        Example:
            >>> await client.variants.delete(123)
        """
        await delete_variant.asyncio_detailed(
            client=self._client,
            id=variant_id,
        )

    async def search(self, query: str, limit: int = 50) -> List[KatanaVariant]:
        """Search variants by SKU or name with tokenization and fuzzy matching.

        Fetches all variants from the API and searches client-side.
        For cached/persistent search, use the MCP server's CatalogCache.

        Args:
            query: Search query (e.g., "fox fork 160")
            limit: Maximum number of results to return

        Returns:
            List of matching Variant objects, sorted by relevance

        Example:
            >>> variants = await client.variants.search("fox fork", limit=10)
            >>> for variant in variants:
            ...     print(f"{variant.sku}: {variant.product_or_material_name}")
        """
        from katana_public_api_client.helpers.search import search_and_rank

        if not query or not query.strip():
            return []

        # Fetch all variants from API (no client-side caching)
        response = await get_all_variants.asyncio_detailed(
            client=self._client,
            extend=[GetAllVariantsExtendItem.PRODUCT_OR_MATERIAL],
        )
        all_variants = variants_to_katana(unwrap_data(response))

        return search_and_rank(
            query=query,
            items=all_variants,
            field_extractor=lambda v: {
                "sku": (v.sku or "", 100),
                "name": (v.get_display_name(), 30),
                "parent_name": (v.product_or_material_name or "", 20),
            },
            limit=limit,
        )
