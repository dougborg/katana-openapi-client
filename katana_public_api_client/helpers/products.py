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

    async def create(
        self, product_data: dict[str, Any] | CreateProductRequest
    ) -> Product:
        """Create a new product.

        Args:
            product_data: Product data dictionary or CreateProductRequest model.

        Returns:
            Created Product object.

        Example:
            >>> new_product = await client.products.create(
            ...     {
            ...         "name": "New Widget",
            ...         "sku": "WIDGET-NEW",
            ...         "is_sellable": True,
            ...     }
            ... )
        """
        # Convert dict to model if needed
        if isinstance(product_data, dict):
            body = CreateProductRequest.from_dict(product_data)
        else:
            body = product_data

        response = await create_product.asyncio_detailed(
            client=self._client,
            body=body,
        )
        # unwrap() raises on errors, so cast is safe
        return cast(Product, unwrap(response))

    async def update(
        self, product_id: int, product_data: dict[str, Any] | UpdateProductRequest
    ) -> Product:
        """Update an existing product.

        Args:
            product_id: The product ID to update.
            product_data: Product data dictionary or UpdateProductRequest model with fields to update.

        Returns:
            Updated Product object.

        Example:
            >>> updated = await client.products.update(123, {"name": "Updated Name"})
        """
        # Convert dict to model if needed
        if isinstance(product_data, dict):
            body = UpdateProductRequest.from_dict(product_data)
        else:
            body = product_data

        response = await update_product.asyncio_detailed(
            client=self._client,
            id=product_id,
            body=body,
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
        """Search products by name.

        Used by: MCP tool search_products

        Args:
            query: Search query to match against product names.
            limit: Maximum number of results to return.

        Returns:
            List of matching Product objects.

        Example:
            >>> products = await client.products.search("widget", limit=10)
            >>> for product in products:
            ...     print(f"{product.sku}: {product.name}")
        """
        # Search by product name using the 'name' parameter
        response = await get_all_products.asyncio_detailed(
            client=self._client,
            name=query,
            limit=limit,
        )
        return unwrap_data(response)
