"""Variant catalog operations."""

from __future__ import annotations

import time
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
from katana_public_api_client.models.get_all_variants_extend_item import (
    GetAllVariantsExtendItem,
)
from katana_public_api_client.models.update_variant_request import UpdateVariantRequest
from katana_public_api_client.models.variant import Variant
from katana_public_api_client.utils import unwrap, unwrap_data


class VariantCache:
    """Cache for variant data with multiple access patterns.

    Provides:
    - List of all variants (for iteration/filtering)
    - Dict by variant ID (O(1) lookup by ID)
    - Dict by SKU (O(1) lookup by SKU)
    - TTL-based invalidation
    """

    def __init__(self, ttl_seconds: int = 300):
        """Initialize cache with TTL.

        Args:
            ttl_seconds: Time-to-live in seconds. Default 5 minutes.
        """
        self.ttl_seconds = ttl_seconds
        self.variants: list[Variant] = []
        self.by_id: dict[int, Variant] = {}
        self.by_sku: dict[str, Variant] = {}
        self.cached_at: float = 0

    def is_valid(self) -> bool:
        """Check if cache is still valid."""
        if not self.variants:
            return False
        age = time.time() - self.cached_at
        return age < self.ttl_seconds

    def update(self, variants: list[Variant]) -> None:
        """Update cache with new variant list.

        Args:
            variants: List of variants to cache
        """
        self.variants = variants
        self.cached_at = time.time()

        # Build lookup dictionaries
        self.by_id = {v.id: v for v in variants}
        self.by_sku = {v.sku: v for v in variants if v.sku}

    def clear(self) -> None:
        """Clear all cached data."""
        self.variants = []
        self.by_id = {}
        self.by_sku = {}
        self.cached_at = 0


class Variants(Base):
    """Variant catalog management.

    Provides CRUD operations for product variants in the Katana catalog.
    Includes caching for improved search performance.

    Example:
        >>> async with KatanaClient() as client:
        ...     # CRUD operations
        ...     variants = await client.variants.list()
        ...     variant = await client.variants.get(123)
        ...     new_variant = await client.variants.create({"name": "Large"})
        ...
        ...     # Fast repeated searches (uses cache)
        ...     results1 = await client.variants.search("fox")
        ...     results2 = await client.variants.search(
        ...         "fork"
        ...     )  # Instant - uses cached data
    """

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize with variant cache."""
        super().__init__(*args, **kwargs)
        self._cache = VariantCache(ttl_seconds=300)  # 5 minute cache

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
        # Clear cache since data changed
        self._cache.clear()
        # unwrap() raises on errors, so cast is safe
        return cast(Variant, unwrap(response))

    async def update(
        self, variant_id: int, variant_data: UpdateVariantRequest
    ) -> Variant:
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
        # Clear cache since data changed
        self._cache.clear()
        # unwrap() raises on errors, so cast is safe
        return cast(Variant, unwrap(response))

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
        # Clear cache since data changed
        self._cache.clear()

    async def _fetch_all_variants(self) -> list[Variant]:
        """Fetch all variants with parent info. Uses cache if valid.

        Returns:
            List of all Variant objects with product_or_material_name populated.
        """
        # Check cache first
        if self._cache.is_valid():
            return self._cache.variants

        # Fetch from API - automatic pagination fetches ALL variants
        response = await get_all_variants.asyncio_detailed(
            client=self._client,
            extend=[GetAllVariantsExtendItem.PRODUCT_OR_MATERIAL],
            # No limit = fetch all pages automatically (up to max_pages in client)
        )
        all_variants = unwrap_data(response)

        # Update cache
        self._cache.update(all_variants)

        return all_variants

    def _get_variant_name(self, variant: Variant) -> str:
        """Extract the product/material name from a variant.

        When using extend=product_or_material, the API returns variants with
        a nested product_or_material object (Product or Material) instead of
        a flat product_or_material_name string.

        Args:
            variant: Variant object

        Returns:
            Name of the product or material, or empty string
        """
        # Check if we have the flat name field (without extend)
        if hasattr(variant, "product_or_material_name") and isinstance(
            variant.product_or_material_name, str
        ):
            return variant.product_or_material_name

        # Check if we have the nested object (with extend)
        if hasattr(variant, "product_or_material"):
            product_or_material = variant.product_or_material
            if hasattr(product_or_material, "name"):
                return product_or_material.name or ""

        return ""

    def _calculate_relevance(self, variant: Variant, query_tokens: list[str]) -> int:
        """Calculate relevance score for a variant against query tokens.

        Scoring:
        - 100: Exact SKU match (all tokens)
        - 80: SKU starts with query
        - 60: SKU contains all tokens
        - 40: Name starts with query
        - 20: Name contains all tokens
        - 0: No match

        Args:
            variant: Variant to score
            query_tokens: List of lowercase query tokens

        Returns:
            Relevance score (0-100)
        """
        query = " ".join(query_tokens)
        sku_lower = (variant.sku or "").lower()
        name_lower = self._get_variant_name(variant).lower()

        # Check for exact SKU match
        if sku_lower == query:
            return 100

        # Check if SKU starts with query
        if sku_lower.startswith(query):
            return 80

        # Check if SKU contains all tokens
        if all(token in sku_lower for token in query_tokens):
            return 60

        # Check if name starts with query
        if name_lower.startswith(query):
            return 40

        # Check if name contains all tokens
        if all(token in name_lower for token in query_tokens):
            return 20

        return 0

    async def search(self, query: str, limit: int = 50) -> list[Variant]:
        """Search variants by SKU or parent product/material name with relevance ranking.

        Used by: MCP tool search_products

        Features:
        - Fetches all variants with parent product/material info (cached for 5 min)
        - Multi-token matching (all tokens must match)
        - Relevance-based ranking (exact matches first)
        - Case-insensitive substring matching

        Args:
            query: Search query (e.g., "fox fork 160")
            limit: Maximum number of results to return

        Returns:
            List of matching Variant objects, sorted by relevance

        Example:
            >>> # First search: fetches from API (~1-2s)
            >>> variants = await client.variants.search("fox fork", limit=10)
            >>>
            >>> # Subsequent searches: instant (<10ms, uses cache)
            >>> variants = await client.variants.search("fox 160", limit=10)
            >>>
            >>> for variant in variants:
            ...     print(f"{variant.sku}: {variant.product_or_material_name}")
        """
        # Tokenize query
        query_tokens = query.lower().split()
        if not query_tokens:
            return []

        # Fetch all variants (uses cache if valid)
        all_variants = await self._fetch_all_variants()

        # Score and filter variants
        scored_matches: list[tuple[Variant, int]] = []

        for variant in all_variants:
            score = self._calculate_relevance(variant, query_tokens)
            if score > 0:
                scored_matches.append((variant, score))

        # Sort by relevance (highest first)
        scored_matches.sort(key=lambda x: x[1], reverse=True)

        # Return top N variants
        return [variant for variant, _score in scored_matches[:limit]]
