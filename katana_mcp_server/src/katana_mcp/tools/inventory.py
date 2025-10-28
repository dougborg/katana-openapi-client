"""Inventory management tools for Katana MCP Server."""

from __future__ import annotations

import logging

from fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

from katana_public_api_client.utils import get_variant_display_name

logger = logging.getLogger(__name__)

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

    Raises:
        ValueError: If SKU is empty or invalid
        Exception: If API call fails
    """
    if not request.sku or not request.sku.strip():
        raise ValueError("SKU cannot be empty")

    logger.info(f"Checking inventory for SKU: {request.sku}")

    try:
        # Access KatanaClient from lifespan context
        server_context = context.request_context.lifespan_context  # type: ignore[attr-defined]
        client = server_context.client  # type: ignore[attr-defined]
        product = await client.inventory.check_stock(request.sku)

        if not product:
            # Product not found - return zero stock
            stock_info = StockInfo(
                sku=request.sku,
                product_name="",
                available_stock=0,
                in_production=0,
                committed=0,
            )
            logger.warning(f"SKU not found: {request.sku}")
            return stock_info

        # Extract stock information from Product model
        stock = getattr(product, "stock_information", None)
        stock_info = StockInfo(
            sku=request.sku,
            product_name=product.name or "",
            available_stock=getattr(stock, "available", 0) if stock else 0,
            in_production=0,  # Not available in current API
            committed=getattr(stock, "allocated", 0) if stock else 0,
        )

        logger.info(
            f"Stock check complete for {request.sku}: "
            f"{stock_info.available_stock} available"
        )
        return stock_info

    except Exception as e:
        logger.error(f"Failed to check inventory for SKU {request.sku}: {e}")
        raise


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

    Raises:
        ValueError: If threshold or limit are invalid
        Exception: If API call fails
    """
    if request.threshold < 0:
        raise ValueError("Threshold must be non-negative")
    if request.limit <= 0:
        raise ValueError("Limit must be positive")

    logger.info(
        f"Listing low stock items (threshold={request.threshold}, limit={request.limit})"
    )

    try:
        # Access KatanaClient from lifespan context
        server_context = context.request_context.lifespan_context  # type: ignore[attr-defined]
        client = server_context.client  # type: ignore[attr-defined]
        products = await client.inventory.list_low_stock(threshold=request.threshold)

        # Limit results
        limited_products = products[: request.limit]

        response = LowStockResponse(
            items=[
                LowStockItem(
                    sku=getattr(product, "sku", "") or "",
                    product_name=product.name or "",
                    current_stock=(
                        getattr(product.stock_information, "in_stock", 0)
                        if hasattr(product, "stock_information")
                        and product.stock_information
                        else 0
                    ),
                    threshold=request.threshold,
                )
                for product in limited_products
            ],
            total_count=len(products),
        )

        logger.info(
            f"Found {response.total_count} low stock items, returning {len(response.items)}"
        )
        return response

    except Exception as e:
        logger.error(f"Failed to list low stock items: {e}")
        raise


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
        List of matching product variants with extended names

    Raises:
        ValueError: If query is empty or limit is invalid
        Exception: If API call fails
    """
    if not request.query or not request.query.strip():
        raise ValueError("Search query cannot be empty")
    if request.limit <= 0:
        raise ValueError("Limit must be positive")

    logger.info(
        f"Searching variants for query: '{request.query}' (limit={request.limit})"
    )

    try:
        # Access KatanaClient from lifespan context
        server_context = context.request_context.lifespan_context  # type: ignore[attr-defined]
        client = server_context.client  # type: ignore[attr-defined]

        # Search variants (which have SKUs) with parent product/material info
        variants = await client.variants.search(request.query, limit=request.limit)

        # Build response - format names matching Katana UI
        products_info = []
        for variant in variants:
            # Build variant name using utility function
            # Format: "Product Name / Config1 / Config2 / ..."
            name = get_variant_display_name(variant)

            # Determine if variant is sellable (products are sellable, materials are not)
            is_sellable = variant.type_.value == "product" if variant.type_ else False

            products_info.append(
                ProductInfo(
                    id=variant.id,
                    sku=variant.sku or "",
                    name=name,
                    is_sellable=is_sellable,
                    stock_level=None,  # Variants don't have stock_level directly
                )
            )

        response = SearchProductsResponse(
            products=products_info,
            total_count=len(products_info),
        )

        logger.info(f"Found {response.total_count} variants matching '{request.query}'")
        return response

    except Exception as e:
        logger.error(f"Failed to search products for query '{request.query}': {e}")
        raise


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


def register_tools(mcp: FastMCP) -> None:
    """Register all inventory tools with the FastMCP instance.

    Args:
        mcp: FastMCP server instance to register tools with
    """
    mcp.tool()(check_inventory)
    mcp.tool()(list_low_stock_items)
    mcp.tool()(search_products)
