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
from katana_public_api_client.domain import (
    KatanaProduct,
    product_to_katana,
    products_to_katana,
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

    async def list(self, **filters: Any) -> list[KatanaProduct]:
        """List all products with optional filters.

        Args:
            **filters: Filtering parameters (e.g., is_sellable, is_producible, include_deleted).

        Returns:
            List of KatanaProduct domain model objects.

        Example:
            >>> products = await client.products.list(is_sellable=True, limit=100)
        """
        response = await get_all_products.asyncio_detailed(
            client=self._client,
            **filters,
        )
        attrs_products = unwrap_data(response)
        return products_to_katana(attrs_products)

    async def get(self, product_id: int) -> KatanaProduct:
        """Get a specific product by ID.

        Args:
            product_id: The product ID.

        Returns:
            KatanaProduct domain model object.

        Example:
            >>> product = await client.products.get(123)
        """
        response = await get_product.asyncio_detailed(
            client=self._client,
            id=product_id,
        )
        # unwrap() raises on errors, so cast is safe
        attrs_product = cast(Product, unwrap(response))
        return product_to_katana(attrs_product)

    async def create(self, product_data: CreateProductRequest) -> KatanaProduct:
        """Create a new product.

        Args:
            product_data: CreateProductRequest model with product details.

        Returns:
            Created KatanaProduct domain model object.

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
        attrs_product = cast(Product, unwrap(response))
        return product_to_katana(attrs_product)

    async def update(
        self, product_id: int, product_data: UpdateProductRequest
    ) -> KatanaProduct:
        """Update an existing product.

        Args:
            product_id: The product ID to update.
            product_data: UpdateProductRequest model with fields to update.

        Returns:
            Updated KatanaProduct domain model object.

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
        attrs_product = cast(Product, unwrap(response))
        return product_to_katana(attrs_product)

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

    async def search(self, query: str, limit: int = 50) -> builtins.list[KatanaProduct]:
        """Search products by name and category (case-insensitive substring search).

        Used by: MCP tool search_products

        Note: The Katana API 'name' parameter only does exact matches, so we
        fetch all products and perform client-side substring searching against
        product names and categories.

        Args:
            query: Search query to match against product names (case-insensitive).
            limit: Maximum number of results to return.

        Returns:
            List of matching KatanaProduct domain model objects, sorted by relevance.

        Example:
            >>> products = await client.products.search("fox", limit=10)
            >>> for product in products:
            ...     print(f"{product.id}: {product.name}")
        """
        # Fetch all products (the API doesn't support partial/fuzzy search)
        response = await get_all_products.asyncio_detailed(
            client=self._client,
            limit=1000,  # Fetch up to 1000 products for searching
        )
        attrs_products = unwrap_data(response)

        # Convert to domain models
        domain_products = products_to_katana(attrs_products)

        # Use domain model's matches_search method
        matches = [p for p in domain_products if p.matches_search(query)]

        return matches[:limit]
