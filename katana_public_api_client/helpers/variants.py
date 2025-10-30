"""Variant catalog operations."""

from __future__ import annotations

import logging
import time

# Import list from builtins to avoid shadowing by our list() method
from builtins import list as List
from typing import Any, cast

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
from katana_public_api_client.utils import unwrap, unwrap_data

logger = logging.getLogger(__name__)


class VariantCache:
    """Cache for variant data with multiple access patterns.

    Provides:
    - List of all variants (for iteration/filtering)
    - Dict by variant ID (O(1) lookup by ID)
    - Dict by SKU (O(1) lookup by SKU)
    - TTL-based invalidation

    Note: Cache stores Pydantic KatanaVariant models (not attrs models).
    """

    def __init__(self, ttl_seconds: int = 300):
        """Initialize cache with TTL.

        Args:
            ttl_seconds: Time-to-live in seconds. Default 5 minutes.
        """
        self.ttl_seconds = ttl_seconds
        self.variants: List[KatanaVariant] = []
        self.by_id: dict[int, KatanaVariant] = {}
        self.by_sku: dict[str, KatanaVariant] = {}
        self.cached_at: float = 0

    def is_valid(self) -> bool:
        """Check if cache is still valid."""
        if not self.variants:
            return False
        age = time.monotonic() - self.cached_at
        return age < self.ttl_seconds

    def update(self, variants: List[KatanaVariant]) -> None:
        """Update cache with new variant list.

        Args:
            variants: List of domain variants to cache
        """
        self.variants = variants
        self.cached_at = time.monotonic()

        # Build lookup dictionaries
        self.by_id = {v.id: v for v in variants}

        # Build SKU lookup with duplicate detection
        self.by_sku = {}
        for v in variants:
            if v.sku:
                if v.sku in self.by_sku:
                    logger.warning(
                        f"Duplicate SKU detected: {v.sku} "
                        f"(variant IDs: {self.by_sku[v.sku].id} and {v.id})"
                    )
                self.by_sku[v.sku] = v

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
        # unwrap() raises on errors, so cast is safe
        attrs_variant = cast(Variant, unwrap(response))
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
        # Clear cache since data changed
        self._cache.clear()
        # unwrap() raises on errors, so cast is safe
        attrs_variant = cast(Variant, unwrap(response))
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
        # Clear cache since data changed
        self._cache.clear()
        # unwrap() raises on errors, so cast is safe
        attrs_variant = cast(Variant, unwrap(response))
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
        # Clear cache since data changed
        self._cache.clear()

    async def _fetch_all_variants(self) -> List[KatanaVariant]:
        """Fetch all variants with parent info. Uses cache if valid.

        Returns:
            List of all KatanaVariant objects with product_or_material_name populated.
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
        all_variants_attrs = unwrap_data(response)

        # Convert to domain models
        all_variants = variants_to_katana(all_variants_attrs)

        # Update cache
        self._cache.update(all_variants)

        return all_variants

    def _calculate_relevance(
        self, variant: KatanaVariant, query_tokens: List[str]
    ) -> int:
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
        name_lower = variant.get_display_name().lower()

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

    async def search(self, query: str, limit: int = 50) -> List[KatanaVariant]:
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
        scored_matches: list[tuple[KatanaVariant, int]] = []

        for variant in all_variants:
            score = self._calculate_relevance(variant, query_tokens)
            if score > 0:
                scored_matches.append((variant, score))

        # Sort by relevance (highest first)
        scored_matches.sort(key=lambda x: x[1], reverse=True)

        # Return top N variants
        return [variant for variant, _score in scored_matches[:limit]]
