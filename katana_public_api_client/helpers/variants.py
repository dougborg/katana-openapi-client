"""Variant catalog operations."""

from __future__ import annotations

from typing import Any

from katana_public_api_client.api.variant import (
    create_variant,
    delete_variant,
    get_all_variants,
    get_variant,
    update_variant,
)
from katana_public_api_client.helpers.base import Base
from katana_public_api_client.models.variant import Variant
from katana_public_api_client.utils import unwrap_data


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
        return unwrap_data(response)

    async def create(self, variant_data: dict[str, Any]) -> Variant:
        """Create a new variant.

        Args:
            variant_data: Variant data dictionary.

        Returns:
            Created Variant object.

        Example:
            >>> new_variant = await client.variants.create({"name": "Large"})
        """
        response = await create_variant.asyncio_detailed(
            client=self._client,
            body=variant_data,
        )
        return unwrap_data(response)

    async def update(self, variant_id: int, variant_data: dict[str, Any]) -> Variant:
        """Update an existing variant.

        Args:
            variant_id: The variant ID to update.
            variant_data: Variant data dictionary with fields to update.

        Returns:
            Updated Variant object.

        Example:
            >>> updated = await client.variants.update(123, {"name": "XL"})
        """
        response = await update_variant.asyncio_detailed(
            client=self._client,
            id=variant_id,
            body=variant_data,
        )
        return unwrap_data(response)

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
