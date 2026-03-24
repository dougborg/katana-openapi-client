"""Inventory management tools for Katana MCP Server.

Foundation tools for checking stock levels, monitoring low stock,
and managing inventory operations.
"""

from __future__ import annotations

import time
from typing import Annotated

from fastmcp import Context, FastMCP
from fastmcp.tools.tool import ToolResult
from pydantic import BaseModel, Field

from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.tool_result_utils import make_tool_result
from katana_mcp.unpack import Unpack, unpack_pydantic_params

logger = get_logger(__name__)

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

    start_time = time.monotonic()
    logger.info("inventory_check_started", sku=request.sku)

    try:
        # Access services using helper
        services = get_services(context)
        product = await services.client.inventory.check_stock(request.sku)

        if not product:
            # Product not found - return zero stock
            stock_info = StockInfo(
                sku=request.sku,
                product_name="",
                available_stock=0,
                in_production=0,
                committed=0,
            )
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            logger.warning(
                "inventory_check_not_found",
                sku=request.sku,
                duration_ms=duration_ms,
            )
            return stock_info

        # Extract stock information from Product attrs model
        # Note: attrs Product model fields may not exist as attributes, so use
        # getattr for stock_information which is conditionally included by the API
        stock = getattr(product, "stock_information", None)
        stock_info = StockInfo(
            sku=request.sku,
            product_name=product.name or "",
            available_stock=getattr(stock, "available", 0) if stock else 0,
            in_production=0,  # Not available in current API
            committed=getattr(stock, "allocated", 0) if stock else 0,
        )

        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.info(
            "inventory_check_completed",
            sku=request.sku,
            product_name=stock_info.product_name,
            available_stock=stock_info.available_stock,
            committed=stock_info.committed,
            duration_ms=duration_ms,
        )
        return stock_info

    except Exception as e:
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.error(
            "inventory_check_failed",
            sku=request.sku,
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=duration_ms,
            exc_info=True,
        )
        raise


@observe_tool
@unpack_pydantic_params
async def check_inventory(
    request: Annotated[CheckInventoryRequest, Unpack()], context: Context
) -> ToolResult:
    """Check current stock levels (available, committed, in production) for a SKU.

    Use before creating orders to verify stock availability. Returns zero stock
    if the SKU is not found (does not raise an error).
    """
    response = await _check_inventory_impl(request, context)
    return make_tool_result(
        response,
        "inventory_check",
        sku=response.sku,
        product_name=response.product_name,
        available_stock=response.available_stock,
        committed=response.committed,
        in_production=response.in_production,
    )


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

    start_time = time.monotonic()
    logger.info(
        "low_stock_search_started",
        threshold=request.threshold,
        limit=request.limit,
    )

    try:
        # Access services using helper
        services = get_services(context)
        products = await services.client.inventory.list_low_stock(
            threshold=request.threshold
        )

        # Limit results
        limited_products = products[: request.limit]

        response = LowStockResponse(
            items=[
                LowStockItem(
                    # attrs Product model has no top-level sku; SKU lives on variants
                    sku=getattr(product, "sku", "") or "",
                    product_name=product.name or "",
                    current_stock=(
                        getattr(
                            getattr(product, "stock_information", None),
                            "in_stock",
                            0,
                        )
                        if getattr(product, "stock_information", None)
                        else 0
                    ),
                    threshold=request.threshold,
                )
                for product in limited_products
            ],
            total_count=len(products),
        )

        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.info(
            "low_stock_search_completed",
            threshold=request.threshold,
            total_count=response.total_count,
            returned_count=len(response.items),
            duration_ms=duration_ms,
        )
        return response

    except Exception as e:
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.error(
            "low_stock_search_failed",
            threshold=request.threshold,
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=duration_ms,
            exc_info=True,
        )
        raise


@observe_tool
@unpack_pydantic_params
async def list_low_stock_items(
    request: Annotated[LowStockRequest, Unpack()], context: Context
) -> ToolResult:
    """List items with stock levels below a threshold — useful for reorder planning.

    Returns items that need replenishment. Follow up with get_variant_details to find
    supplier info, then create_purchase_order to reorder.

    Default threshold is 10 units, default limit is 50 items.
    """
    response = await _list_low_stock_items_impl(request, context)

    if response.items:
        items_table = "\n".join(
            f"- **{item.sku}**: {item.product_name} — {item.current_stock} units"
            for item in response.items
        )
    else:
        items_table = "No items below threshold."

    return make_tool_result(
        response,
        "low_stock_report",
        threshold=request.threshold,
        total_count=response.total_count,
        items_table=items_table,
    )


def register_tools(mcp: FastMCP) -> None:
    """Register all inventory tools with the FastMCP instance.

    Args:
        mcp: FastMCP server instance to register tools with
    """
    from mcp.types import ToolAnnotations

    _read = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )

    mcp.tool(tags={"inventory", "read"}, annotations=_read)(check_inventory)
    mcp.tool(tags={"inventory", "read"}, annotations=_read)(list_low_stock_items)
