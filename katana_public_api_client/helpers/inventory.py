"""Inventory and stock management operations."""

from __future__ import annotations

from typing import Any

from katana_public_api_client.api.product import get_all_products
from katana_public_api_client.helpers.base import Base
from katana_public_api_client.utils import unwrap_data


class Inventory(Base):
    """Inventory and stock operations.

    Provides methods for checking stock levels, movements, adjustments, and transfers.
    For product catalog CRUD, use client.products instead.

    Example:
        >>> async with KatanaClient() as client:
        ...     # Check stock levels (MCP tool support)
        ...     stock = await client.inventory.check_stock("WIDGET-001")
        ...     low_stock = await client.inventory.list_low_stock(threshold=10)
        ...
        ...     # Stock movements and adjustments
        ...     movements = await client.inventory.get_movements()
        ...     await client.inventory.create_adjustment(
        ...         {"product_id": 123, "quantity": 10}
        ...     )
    """

    # === MCP Tool Support Methods ===

    async def check_stock(self, sku: str) -> dict[str, Any]:
        """Check stock levels for a specific SKU.

        Used by: MCP tool check_inventory

        Args:
            sku: The SKU to check stock for.

        Returns:
            Dictionary with stock information including available, allocated, in_stock quantities.

        Example:
            >>> stock = await client.inventory.check_stock("WIDGET-001")
            >>> print(f"Available: {stock['available']}, In Stock: {stock['in_stock']}")
        """
        # Note: The API doesn't support direct SKU filtering yet
        # We need to fetch products and filter client-side
        # TODO: When API adds SKU parameter, use that instead
        response = await get_all_products.asyncio_detailed(
            client=self._client,
            limit=100,
        )
        products = unwrap_data(response)

        # Find product by SKU
        matching_product = None
        for product in products:
            if getattr(product, "sku", None) == sku:
                matching_product = product
                break

        if not matching_product:
            return {
                "sku": sku,
                "found": False,
                "available": 0,
                "allocated": 0,
                "in_stock": 0,
            }

        stock_info = getattr(matching_product, "stock_information", None)

        return {
            "sku": sku,
            "found": True,
            "product_id": matching_product.id,
            "product_name": matching_product.name,
            "available": getattr(stock_info, "available", 0) if stock_info else 0,
            "allocated": getattr(stock_info, "allocated", 0) if stock_info else 0,
            "in_stock": getattr(stock_info, "in_stock", 0) if stock_info else 0,
        }

    async def list_low_stock(
        self, threshold: int | None = None
    ) -> list[dict[str, Any]]:
        """Find products below their reorder point.

        Used by: MCP tool list_low_stock_items

        Args:
            threshold: Optional stock threshold. Products with stock below this will be returned.
                      If None, uses each product's reorder point.

        Returns:
            List of dictionaries with product and stock information.

        Example:
            >>> low_stock = await client.inventory.list_low_stock(threshold=10)
            >>> for item in low_stock:
            ...     print(f"{item['sku']}: {item['in_stock']} units")
        """
        # Note: Stock information is included in product response by default
        response = await get_all_products.asyncio_detailed(
            client=self._client,
            limit=100,  # KatanaClient handles pagination automatically
        )
        products = unwrap_data(response)

        low_stock_items = []
        for product in products:
            stock_info = getattr(product, "stock_information", None)
            if not stock_info:
                continue

            in_stock = getattr(stock_info, "in_stock", 0) or 0
            reorder_point = getattr(stock_info, "reorder_point", 0)

            # Determine if this is low stock
            is_low = False
            if threshold is not None:
                is_low = in_stock < threshold
            elif reorder_point > 0:
                is_low = in_stock < reorder_point

            if is_low:
                low_stock_items.append(
                    {
                        "product_id": product.id,
                        "sku": product.sku if hasattr(product, "sku") else None,
                        "name": product.name,
                        "in_stock": in_stock,
                        "available": stock_info.available or 0,
                        "allocated": stock_info.allocated or 0,
                        "reorder_point": reorder_point,
                    }
                )

        return low_stock_items

    # === Stock Operations (To be implemented with actual inventory APIs) ===
    # These will use the inventory/, inventory_movements/, stock_adjustment/ APIs
    # For now, providing the interface that MCP tools and users will call

    async def get_inventory_points(self, **filters: Any) -> list[dict[str, Any]]:
        """Get inventory points for all products.

        This will use the inventory API to get current stock levels,
        reorder points, and safety stock levels.

        Args:
            **filters: Filtering parameters.

        Returns:
            List of inventory point data.

        Note:
            To be implemented using katana_public_api_client.api.inventory
        """
        # TODO: Implement using get_all_inventory_point API
        raise NotImplementedError("Coming soon - will use inventory API")

    async def get_negative_stock(self) -> list[dict[str, Any]]:
        """Get products with negative stock.

        Returns:
            List of products with negative inventory.

        Note:
            To be implemented using katana_public_api_client.api.inventory
        """
        # TODO: Implement using get_all_negative_stock API
        raise NotImplementedError("Coming soon - will use inventory API")

    async def set_reorder_point(self, product_id: int, quantity: int) -> None:
        """Set reorder point for a product.

        Args:
            product_id: The product ID.
            quantity: The reorder point quantity.

        Note:
            To be implemented using katana_public_api_client.api.inventory
        """
        # TODO: Implement using create_inventory_reorder_point API
        raise NotImplementedError("Coming soon - will use inventory API")

    async def set_safety_stock(self, product_id: int, quantity: int) -> None:
        """Set safety stock level for a product.

        Args:
            product_id: The product ID.
            quantity: The safety stock quantity.

        Note:
            To be implemented using katana_public_api_client.api.inventory
        """
        # TODO: Implement using create_inventory_safety_stock_level API
        raise NotImplementedError("Coming soon - will use inventory API")
