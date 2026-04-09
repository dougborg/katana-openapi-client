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
    """Stock information for a variant."""

    sku: str
    product_name: str
    available_stock: float
    committed: float
    expected: float
    in_stock: float


async def _check_inventory_impl(
    request: CheckInventoryRequest, context: Context
) -> StockInfo:
    """Look up variant by SKU via cache, then query the inventory endpoint."""
    from katana_public_api_client.api.inventory import get_all_inventory_point
    from katana_public_api_client.domain.converters import unwrap_unset
    from katana_public_api_client.utils import unwrap_data

    if not request.sku or not request.sku.strip():
        raise ValueError("SKU cannot be empty")

    start_time = time.monotonic()
    logger.info("inventory_check_started", sku=request.sku)

    try:
        services = get_services(context)

        # 1. Resolve SKU → variant_id via the cached catalog
        variant = await services.cache.get_by_sku(sku=request.sku)
        if not variant:
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            logger.warning(
                "inventory_check_not_found", sku=request.sku, duration_ms=duration_ms
            )
            return StockInfo(
                sku=request.sku,
                product_name="",
                available_stock=0,
                committed=0,
                expected=0,
                in_stock=0,
            )

        variant_id = variant["id"]
        product_name = variant.get("display_name") or variant.get("sku") or ""

        # 2. Query the inventory endpoint filtered by variant_id
        response = await get_all_inventory_point.asyncio_detailed(
            client=services.client, variant_id=variant_id
        )
        inventory_items = unwrap_data(response)

        # 3. Sum across all locations
        total_in_stock = 0.0
        total_committed = 0.0
        total_expected = 0.0

        for inv in inventory_items:
            total_in_stock += float(unwrap_unset(inv.quantity_in_stock, "0"))
            total_committed += float(unwrap_unset(inv.quantity_committed, "0"))
            total_expected += float(unwrap_unset(inv.quantity_expected, "0"))

        available = total_in_stock - total_committed

        stock_info = StockInfo(
            sku=request.sku,
            product_name=product_name,
            available_stock=available,
            committed=total_committed,
            expected=total_expected,
            in_stock=total_in_stock,
        )

        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.info(
            "inventory_check_completed",
            sku=request.sku,
            product_name=stock_info.product_name,
            in_stock=stock_info.in_stock,
            committed=stock_info.committed,
            expected=stock_info.expected,
            available_stock=stock_info.available_stock,
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
    from katana_mcp.tools.prefab_ui import build_inventory_check_ui

    response = await _check_inventory_impl(request, context)
    ui = build_inventory_check_ui(response.model_dump())

    return make_tool_result(
        response,
        "inventory_check",
        ui=ui,
        sku=response.sku,
        product_name=response.product_name,
        in_stock=response.in_stock,
        available_stock=response.available_stock,
        committed=response.committed,
        expected=response.expected,
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
    from katana_mcp.tools.prefab_ui import build_low_stock_ui

    response = await _list_low_stock_items_impl(request, context)

    if response.items:
        items_table = "\n".join(
            f"- **{item.sku}**: {item.product_name} — {item.current_stock} units"
            for item in response.items
        )
    else:
        items_table = "No items below threshold."

    items_dicts = [item.model_dump() for item in response.items]
    ui = build_low_stock_ui(items_dicts, request.threshold, response.total_count)

    return make_tool_result(
        response,
        "low_stock_report",
        ui=ui,
        threshold=request.threshold,
        total_count=response.total_count,
        items_table=items_table,
    )


# ============================================================================
# Tool 3: get_inventory_movements
# ============================================================================


class GetInventoryMovementsRequest(BaseModel):
    """Request model for querying inventory movements."""

    sku: str = Field(..., description="SKU to get movements for")
    limit: int = Field(default=50, description="Maximum movements to return")


class MovementInfo(BaseModel):
    """A single inventory movement record."""

    movement_date: str
    quantity_change: float
    balance_after: float
    resource_type: str
    caused_by_order_no: str | None
    value_per_unit: float


class InventoryMovementsResponse(BaseModel):
    """Response containing inventory movements."""

    sku: str
    product_name: str
    movements: list[MovementInfo]
    total_count: int


async def _get_inventory_movements_impl(
    request: GetInventoryMovementsRequest, context: Context
) -> InventoryMovementsResponse:
    """Look up variant by SKU via cache, then query inventory movements."""
    from katana_public_api_client.api.inventory_movements import (
        get_all_inventory_movements,
    )
    from katana_public_api_client.domain.converters import unwrap_unset
    from katana_public_api_client.utils import unwrap_data

    if not request.sku or not request.sku.strip():
        raise ValueError("SKU cannot be empty")
    if request.limit <= 0:
        raise ValueError("Limit must be positive")

    start_time = time.monotonic()
    logger.info("inventory_movements_started", sku=request.sku)

    try:
        services = get_services(context)

        # Resolve SKU → variant_id via the cached catalog
        variant = await services.cache.get_by_sku(sku=request.sku)
        if not variant:
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            logger.warning(
                "inventory_movements_not_found",
                sku=request.sku,
                duration_ms=duration_ms,
            )
            return InventoryMovementsResponse(
                sku=request.sku,
                product_name="",
                movements=[],
                total_count=0,
            )

        variant_id = variant["id"]
        product_name = variant.get("display_name") or variant.get("sku") or ""

        # Query inventory movements filtered by variant_id
        response = await get_all_inventory_movements.asyncio_detailed(
            client=services.client,
            variant_ids=[variant_id],
            limit=request.limit,
        )
        attrs_list = unwrap_data(response)

        movements = [
            MovementInfo(
                movement_date=m.movement_date.isoformat()
                if hasattr(m.movement_date, "isoformat")
                else str(m.movement_date),
                quantity_change=m.quantity_change,
                balance_after=m.balance_after,
                resource_type=m.resource_type.value
                if hasattr(m.resource_type, "value")
                else str(m.resource_type),
                caused_by_order_no=unwrap_unset(m.caused_by_order_no, None),
                value_per_unit=m.value_per_unit,
            )
            for m in attrs_list
        ]

        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.info(
            "inventory_movements_completed",
            sku=request.sku,
            count=len(movements),
            duration_ms=duration_ms,
        )
        return InventoryMovementsResponse(
            sku=request.sku,
            product_name=product_name,
            movements=movements,
            total_count=len(movements),
        )

    except Exception as e:
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.error(
            "inventory_movements_failed",
            sku=request.sku,
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=duration_ms,
            exc_info=True,
        )
        raise


@observe_tool
@unpack_pydantic_params
async def get_inventory_movements(
    request: Annotated[GetInventoryMovementsRequest, Unpack()], context: Context
) -> ToolResult:
    """Get inventory movement history for a SKU — shows every stock change with dates,
    quantities, and what caused each movement (sales, purchases, manufacturing, adjustments).

    Use to investigate stock discrepancies or trace how inventory levels changed over time.
    Default limit is 50 movements, ordered most recent first.
    """
    response = await _get_inventory_movements_impl(request, context)

    if response.movements:
        movements_table = "\n".join(
            f"| {m.movement_date} | {m.quantity_change:+.1f} | {m.balance_after:.1f}"
            f" | {m.resource_type} | {m.caused_by_order_no or 'N/A'} |"
            for m in response.movements
        )
        movements_md = (
            "| Date | Change | Balance | Type | Order |\n"
            "|------|--------|---------|------|-------|\n"
            f"{movements_table}"
        )
    else:
        movements_md = "No movements found."

    return make_tool_result(
        response,
        "inventory_movements",
        sku=response.sku,
        product_name=response.product_name,
        total_count=response.total_count,
        movements_table=movements_md,
    )


# ============================================================================
# Tool 4: create_stock_adjustment
# ============================================================================


class StockAdjustmentRow(BaseModel):
    """A single line item in a stock adjustment."""

    sku: str = Field(..., description="SKU to adjust")
    quantity: float = Field(
        ..., description="Quantity change (positive to add, negative to remove)"
    )
    cost_per_unit: float | None = Field(
        default=None, description="Cost per unit (optional)"
    )


class CreateStockAdjustmentRequest(BaseModel):
    """Request to create a stock adjustment."""

    location_id: int = Field(..., description="Location ID for the adjustment")
    rows: list[StockAdjustmentRow] = Field(..., description="Line items to adjust")
    reason: str | None = Field(
        default=None, description="Reason for adjustment (e.g., 'Sample received')"
    )
    additional_info: str | None = Field(default=None, description="Additional notes")
    confirm: bool = Field(
        default=False,
        description="Set false to preview, true to create (prompts for confirmation)",
    )


class StockAdjustmentResponse(BaseModel):
    """Response from stock adjustment creation."""

    id: int | None
    is_preview: bool
    message: str
    rows_summary: str


async def _create_stock_adjustment_impl(
    request: CreateStockAdjustmentRequest, context: Context
) -> StockAdjustmentResponse:
    """Create a stock adjustment, resolving SKUs to variant IDs."""
    from datetime import UTC, datetime

    from katana_public_api_client.api.stock_adjustment import create_stock_adjustment
    from katana_public_api_client.domain.converters import to_unset
    from katana_public_api_client.models import (
        CreateStockAdjustmentRequest as APICreateStockAdjustmentRequest,
    )
    from katana_public_api_client.models.create_stock_adjustment_request_stock_adjustment_rows_item import (
        CreateStockAdjustmentRequestStockAdjustmentRowsItem,
    )

    if not request.rows:
        raise ValueError("At least one adjustment row is required")

    services = get_services(context)

    # Resolve SKUs to variant IDs
    api_rows = []
    rows_summary_parts = []
    for row in request.rows:
        variant = await services.cache.get_by_sku(sku=row.sku)
        if not variant:
            raise ValueError(f"SKU '{row.sku}' not found")
        display_name = variant.get("display_name") or row.sku
        api_rows.append(
            CreateStockAdjustmentRequestStockAdjustmentRowsItem(
                variant_id=variant["id"],
                quantity=row.quantity,
                cost_per_unit=to_unset(row.cost_per_unit),
            )
        )
        rows_summary_parts.append(f"- {row.sku} ({display_name}): {row.quantity:+.1f}")

    rows_summary = "\n".join(rows_summary_parts)

    # Preview mode
    if not request.confirm:
        return StockAdjustmentResponse(
            id=None,
            is_preview=True,
            message="Preview — call again with confirm=true to create",
            rows_summary=rows_summary,
        )

    # Generate next SA number by scanning existing adjustments for max SA-{N}
    import re

    from katana_public_api_client.api.stock_adjustment import (
        get_all_stock_adjustments,
    )
    from katana_public_api_client.utils import unwrap_data

    sa_response = await get_all_stock_adjustments.asyncio_detailed(
        client=services.client, limit=200
    )
    existing = unwrap_data(sa_response, default=[])

    sa_pattern = re.compile(r"^SA-(\d+)$")
    max_num = 0
    for sa in existing:
        match = sa_pattern.match(sa.stock_adjustment_number)
        if match:
            max_num = max(max_num, int(match.group(1)))
    adj_number = f"SA-{max_num + 1}"

    api_request = APICreateStockAdjustmentRequest(
        location_id=request.location_id,
        stock_adjustment_rows=api_rows,
        stock_adjustment_number=adj_number,
        stock_adjustment_date=datetime.now(tz=UTC),
        reason=to_unset(request.reason),
        additional_info=to_unset(request.additional_info),
    )

    response = await create_stock_adjustment.asyncio_detailed(
        client=services.client, body=api_request
    )

    # unwrap raises ValidationError (422), APIError, etc. with formatted messages
    from katana_public_api_client.utils import APIError, unwrap

    try:
        result = unwrap(response)
    except APIError as e:
        # Log the raw response for debugging
        logger.error(
            "stock_adjustment_api_error",
            status_code=response.status_code,
            raw_body=response.content.decode() if response.content else "",
            parsed=str(response.parsed),
        )
        raise ValueError(str(e)) from e

    adj_id = getattr(result, "id", None) if result else None
    return StockAdjustmentResponse(
        id=adj_id,
        is_preview=False,
        message="Stock adjustment created successfully",
        rows_summary=rows_summary,
    )


@observe_tool
@unpack_pydantic_params
async def create_stock_adjustment(
    request: Annotated[CreateStockAdjustmentRequest, Unpack()], context: Context
) -> ToolResult:
    """Create a stock adjustment to correct inventory levels.

    Two-step flow: confirm=false to preview, confirm=true to create (prompts
    for confirmation). Resolves SKUs to variant IDs automatically.

    Use positive quantities to add stock, negative to remove.
    """
    from katana_mcp.tools.tool_result_utils import make_simple_result

    response = await _create_stock_adjustment_impl(request, context)

    status = "PREVIEW" if response.is_preview else "CREATED"
    md = (
        f"## Stock Adjustment ({status})\n\n"
        f"{response.message}\n\n"
        f"### Items\n{response.rows_summary}\n"
    )
    if response.id:
        md += f"\n**Adjustment ID**: {response.id}\n"

    return make_simple_result(
        md,
        structured_data=response.model_dump(),
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

    _write = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        openWorldHint=True,
    )

    mcp.tool(tags={"inventory", "read"}, annotations=_read)(check_inventory)
    mcp.tool(tags={"inventory", "read"}, annotations=_read)(list_low_stock_items)
    mcp.tool(tags={"inventory", "read"}, annotations=_read)(get_inventory_movements)
    mcp.tool(tags={"inventory", "write"}, annotations=_write)(create_stock_adjustment)
