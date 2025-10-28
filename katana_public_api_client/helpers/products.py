"""Product catalog operations."""

from __future__ import annotations

import builtins
from typing import Any, cast

from katana_public_api_client.api.product import (
    create_product,
    delete_product,
    get_all_products,
    get_product,
    update_product,
)
from katana_public_api_client.helpers.base import Base
from katana_public_api_client.models.create_product_request import CreateProductRequest
from katana_public_api_client.models.product import Product
from katana_public_api_client.models.update_product_request import UpdateProductRequest
from katana_public_api_client.utils import unwrap, unwrap_data


class Products(Base):
    """Product catalog management.

    Provides CRUD operations and search for products in the Katana catalog.

    Example:
        >>> async with KatanaClient() as client:
        ...     # Search products
        ...     products = await client.products.search("widget")
        ...
        ...     # CRUD operations
        ...     products = await client.products.list(is_sellable=True)
        ...     product = await client.products.get(123)
        ...     new_product = await client.products.create({"name": "Widget"})
    """

    async def list(self, **filters: Any) -> list[Product]:
        """List all products with optional filters.

        Args:
            **filters: Filtering parameters (e.g., is_sellable, is_producible, include_deleted).

        Returns:
            List of Product objects.

        Example:
            >>> products = await client.products.list(is_sellable=True, limit=100)
        """
        response = await get_all_products.asyncio_detailed(
            client=self._client,
            **filters,
        )
        return unwrap_data(response)

    async def get(self, product_id: int) -> Product:
        """Get a specific product by ID.

        Args:
            product_id: The product ID.

        Returns:
            Product object.

        Example:
            >>> product = await client.products.get(123)
        """
        response = await get_product.asyncio_detailed(
            client=self._client,
            id=product_id,
        )
        # unwrap() raises on errors, so cast is safe
        return cast(Product, unwrap(response))

    async def create(self, product_data: CreateProductRequest) -> Product:
        """Create a new product.

        Args:
            product_data: CreateProductRequest model with product details.

        Returns:
            Created Product object.

        Example:
            >>> from katana_public_api_client.models import CreateProductRequest
            >>> new_product = await client.products.create(
            ...     CreateProductRequest(
            ...         name="New Widget",
            ...         sku="WIDGET-NEW",
            ...         is_sellable=True,
            ...         variants=[],
            ...     )
            ... )
        """
        response = await create_product.asyncio_detailed(
            client=self._client,
            body=product_data,
        )
        # unwrap() raises on errors, so cast is safe
        return cast(Product, unwrap(response))

    async def update(
        self, product_id: int, product_data: UpdateProductRequest
    ) -> Product:
        """Update an existing product.

        Args:
            product_id: The product ID to update.
            product_data: UpdateProductRequest model with fields to update.

        Returns:
            Updated Product object.

        Example:
            >>> from katana_public_api_client.models import UpdateProductRequest
            >>> updated = await client.products.update(
            ...     123, UpdateProductRequest(name="Updated Name")
            ... )
        """
        response = await update_product.asyncio_detailed(
            client=self._client,
            id=product_id,
            body=product_data,
        )
        # unwrap() raises on errors, so cast is safe
        return cast(Product, unwrap(response))

    async def delete(self, product_id: int) -> None:
        """Delete a product.

        Args:
            product_id: The product ID to delete.

        Example:
            >>> await client.products.delete(123)
        """
        await delete_product.asyncio_detailed(
            client=self._client,
            id=product_id,
        )

    async def search(self, query: str, limit: int = 50) -> builtins.list[Product]:
        """Search products by name or SKU (fuzzy search).

        Used by: MCP tool search_products

        Note: The Katana API 'name' parameter only does exact matches, so we
        fetch all products and perform client-side fuzzy searching across both
        product names and variant SKUs.

        Args:
            query: Search query to match against product names and SKUs (case-insensitive).
            limit: Maximum number of results to return.

        Returns:
            List of matching Product objects, sorted by relevance.

        Example:
            >>> products = await client.products.search("fox", limit=10)
            >>> for product in products:
            ...     print(f"{product.sku}: {product.name}")
        """
        # Fetch all products (the API doesn't support partial/fuzzy search)
        response = await get_all_products.asyncio_detailed(
            client=self._client,
            limit=1000,  # Fetch up to 1000 products for searching
        )
        all_products = unwrap_data(response)

        # Perform case-insensitive fuzzy search on product names and variant SKUs
        query_lower = query.lower()
        matches = []

        for product in all_products:
            # Check product name
            if product.name and query_lower in product.name.lower():
                matches.append(product)
                continue

            # Check variant SKUs
            if product.variants:
                for variant in product.variants:
                    if variant.sku and query_lower in variant.sku.lower():
                        matches.append(product)
                        break

        return matches[:limit]
