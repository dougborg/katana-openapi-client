"""Inventory management tools for Katana MCP Server."""

from __future__ import annotations

from fastmcp import Context
from pydantic import BaseModel, Field

from katana_mcp.server import mcp

# ============================================================================
# Tool 1: check_inventory
# ============================================================================


class CheckInventoryRequest(BaseModel):
    """Request model for checking inventory."""

    sku: str = Field(..., description="Product SKU to check")


class StockInfo(BaseModel):
    """Stock information for a product."""

    sku: str
    product_name: str
    available_stock: int
    in_production: int
    committed: int


async def _check_inventory_impl(
    request: CheckInventoryRequest, context: Context
) -> StockInfo:
    """Implementation of check_inventory tool.

    Args:
        request: Request containing SKU to check
        context: Server context with KatanaClient

    Returns:
        StockInfo with current stock levels
    """
    client = context.server_context.client  # type: ignore[attr-defined]
    result = await client.inventory.check_stock(request.sku)

    return StockInfo(
        sku=result["sku"],
        product_name=result.get("product_name", ""),
        available_stock=result.get("available", 0),
        in_production=0,  # Not available in current API
        committed=result.get("allocated", 0),
    )


@mcp.tool()
async def check_inventory(
    request: CheckInventoryRequest, context: Context
) -> StockInfo:
    """Check stock levels for a specific product SKU.

    This tool retrieves current inventory levels including available stock,
    items in production, and committed quantities.

    Args:
        request: Request containing SKU to check
        context: Server context with KatanaClient

    Returns:
        StockInfo with current stock levels

    Example:
        Request: {"sku": "WIDGET-001"}
        Returns: {"sku": "WIDGET-001", "product_name": "Widget", "available_stock": 100, ...}
    """
    return await _check_inventory_impl(request, context)


# ============================================================================
# Tool 2: list_low_stock_items
# ============================================================================


class LowStockRequest(BaseModel):
    """Request model for listing low stock items."""

    threshold: int = Field(default=10, description="Stock threshold level")
    limit: int = Field(default=50, description="Maximum items to return")


class LowStockItem(BaseModel):
    """Low stock item information."""

    sku: str
    product_name: str
    current_stock: int
    threshold: int


class LowStockResponse(BaseModel):
    """Response containing low stock items."""

    items: list[LowStockItem]
    total_count: int


async def _list_low_stock_items_impl(
    request: LowStockRequest, context: Context
) -> LowStockResponse:
    """Implementation of list_low_stock_items tool.

    Args:
        request: Request with threshold and limit
        context: Server context with KatanaClient

    Returns:
        List of products below threshold with current levels
    """
    client = context.server_context.client  # type: ignore[attr-defined]
    items = await client.inventory.list_low_stock(threshold=request.threshold)

    # Limit results
    limited_items = items[: request.limit]

    return LowStockResponse(
        items=[
            LowStockItem(
                sku=item["sku"] or "",
                product_name=item["name"] or "",
                current_stock=item["in_stock"],
                threshold=request.threshold,
            )
            for item in limited_items
        ],
        total_count=len(items),
    )


@mcp.tool()
async def list_low_stock_items(
    request: LowStockRequest, context: Context
) -> LowStockResponse:
    """List products below stock threshold.

    Identifies products that have fallen below a specified stock threshold,
    useful for proactive inventory management and reordering.

    Args:
        request: Request with threshold and limit
        context: Server context with KatanaClient

    Returns:
        List of products below threshold with current levels

    Example:
        Request: {"threshold": 5, "limit": 10}
        Returns: {"items": [...], "total_count": 15}
    """
    return await _list_low_stock_items_impl(request, context)


# ============================================================================
# Tool 3: search_products
# ============================================================================


class SearchProductsRequest(BaseModel):
    """Request model for searching products."""

    query: str = Field(..., description="Search query (name, SKU, etc.)")
    limit: int = Field(default=20, description="Maximum results to return")


class ProductInfo(BaseModel):
    """Product information."""

    id: int
    sku: str
    name: str
    is_sellable: bool
    stock_level: int | None = None


class SearchProductsResponse(BaseModel):
    """Response containing search results."""

    products: list[ProductInfo]
    total_count: int


async def _search_products_impl(
    request: SearchProductsRequest, context: Context
) -> SearchProductsResponse:
    """Implementation of search_products tool.

    Args:
        request: Request with search query and limit
        context: Server context with KatanaClient

    Returns:
        List of matching products with basic info
    """
    client = context.server_context.client  # type: ignore[attr-defined]
    results = await client.products.search(request.query, limit=request.limit)

    return SearchProductsResponse(
        products=[
            ProductInfo(
                id=product.id,
                sku=product.sku or "",
                name=product.name or "",
                is_sellable=product.is_sellable or False,
                stock_level=getattr(product, "stock_level", None),
            )
            for product in results
        ],
        total_count=len(results),
    )


@mcp.tool()
async def search_products(
    request: SearchProductsRequest, context: Context
) -> SearchProductsResponse:
    """Search for products by name or SKU.

    Performs a search across product catalog to find items matching
    the search query. Useful for quick product lookup.

    Args:
        request: Request with search query and limit
        context: Server context with KatanaClient

    Returns:
        List of matching products with basic info

    Example:
        Request: {"query": "widget", "limit": 10}
        Returns: {"products": [...], "total_count": 5}
    """
    return await _search_products_impl(request, context)
