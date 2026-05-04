"""Inventory and stock management operations."""

from __future__ import annotations

from katana_public_api_client.api.product import get_all_products
from katana_public_api_client.helpers.base import Base
from katana_public_api_client.models.product import Product
from katana_public_api_client.utils import unwrap_data


class Inventory(Base):
    """Inventory and stock operations.

    For per-SKU stock lookups, call
    ``katana_public_api_client.api.inventory.get_inventory.asyncio_detailed``
    directly with a ``sku`` filter — the inventory endpoint provides the
    canonical stock view (on-hand, allocations, incoming) without the
    per-page pagination guess that the legacy ``check_stock`` helper
    had to make.

    For product catalog CRUD, use ``client.products`` instead.

    .. warning::
       ``list_low_stock`` reads ``product.stock_information`` which is
       not a typed field on the generated ``Product`` attrs model. The
       helper currently returns ``[]`` against live API data regardless
       of inventory state. Migration to the inventory endpoint is
       tracked in #510; until then prefer that endpoint directly.

    Example:
        >>> async with KatanaClient() as client:
        ...     low_stock = await client.inventory.list_low_stock(threshold=10)
    """

    # === MCP Tool Support Methods ===

    async def list_low_stock(self, threshold: int | None = None) -> list[Product]:
        """Find products below their reorder point.

        Used by: MCP tool list_low_stock_items

        Args:
            threshold: Optional stock threshold. Products with stock below this will be returned.
                      If None, uses each product's reorder point.

        Returns:
            List of Product models that are below stock threshold.

        Example:
            >>> low_stock = await client.inventory.list_low_stock(threshold=10)
            >>> for product in low_stock:
            ...     stock = product.stock_information
            ...     print(f"{product.sku}: {stock.in_stock} units")
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
                low_stock_items.append(product)

        return low_stock_items
