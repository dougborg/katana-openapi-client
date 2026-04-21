"""Inventory management tools for Katana MCP Server.

Foundation tools for checking stock levels, monitoring low stock,
and managing inventory operations.
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime
from typing import Annotated, Any

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, Field

from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.schemas import ConfirmationResult, require_confirmation
from katana_mcp.tools.tool_result_utils import (
    format_md_table,
    iso_or_none,
    make_simple_result,
    make_tool_result,
)
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.domain.converters import to_unset, unwrap_unset

logger = get_logger(__name__)

# ============================================================================
# Tool 1: check_inventory
# ============================================================================


class CheckInventoryRequest(BaseModel):
    """Request model for checking inventory.

    Accepts a single sku/variant_id OR a list (skus/variant_ids) for batch lookups.
    """

    sku: str | None = Field(default=None, description="Single SKU to check")
    variant_id: int | None = Field(
        default=None, description="Single variant ID to check"
    )
    skus: list[str] | None = Field(
        default=None, description="Batch: list of SKUs to check"
    )
    variant_ids: list[int] | None = Field(
        default=None, description="Batch: list of variant IDs to check"
    )


class StockInfo(BaseModel):
    """Stock information for a variant."""

    variant_id: int | None = None
    sku: str
    product_name: str
    available_stock: float
    committed: float
    expected: float
    in_stock: float


async def _fetch_stock_for_variant(
    services: Any, variant_id: int, sku: str, product_name: str
) -> StockInfo:
    """Query the inventory endpoint and sum stock across all locations."""
    from katana_public_api_client.api.inventory import get_all_inventory_point
    from katana_public_api_client.domain.converters import unwrap_unset
    from katana_public_api_client.utils import unwrap_data

    response = await get_all_inventory_point.asyncio_detailed(
        client=services.client, variant_id=variant_id
    )
    inventory_items = unwrap_data(response)

    total_in_stock = 0.0
    total_committed = 0.0
    total_expected = 0.0
    for inv in inventory_items:
        total_in_stock += float(unwrap_unset(inv.quantity_in_stock, "0"))
        total_committed += float(unwrap_unset(inv.quantity_committed, "0"))
        total_expected += float(unwrap_unset(inv.quantity_expected, "0"))

    return StockInfo(
        variant_id=variant_id,
        sku=sku,
        product_name=product_name,
        available_stock=total_in_stock - total_committed,
        committed=total_committed,
        expected=total_expected,
        in_stock=total_in_stock,
    )


async def _check_inventory_impl(
    request: CheckInventoryRequest, context: Context
) -> list[StockInfo]:
    """Look up one or more variants by SKU/ID and return their stock info."""
    skus: list[str] = []
    variant_ids: list[int] = []

    if request.sku is not None:
        normalized = request.sku.strip()
        if not normalized:
            raise ValueError("SKU cannot be empty")
        skus.append(normalized)
    if request.skus:
        skus.extend(s.strip() for s in request.skus if s.strip())
    if request.variant_id is not None:
        variant_ids.append(request.variant_id)
    if request.variant_ids:
        variant_ids.extend(request.variant_ids)

    if not skus and not variant_ids:
        raise ValueError(
            "Must provide at least one of: sku, variant_id, skus, variant_ids"
        )

    start_time = time.monotonic()
    logger.info(
        "inventory_check_started",
        sku_count=len(skus),
        variant_id_count=len(variant_ids),
    )

    try:
        services = get_services(context)

        # Phase 1: resolve all SKUs and variant_ids to variant dicts in parallel.
        # For variant_ids, _fetch_variant_by_id falls back to the API on cache miss
        # so a cold cache doesn't silently return empty stock.
        from katana_mcp.tools.foundation.items import _fetch_variant_by_id

        sku_variants, id_variants = await asyncio.gather(
            asyncio.gather(*(services.cache.get_by_sku(sku=s) for s in skus)),
            asyncio.gather(
                *(_fetch_variant_by_id(services, v_id) for v_id in variant_ids)
            ),
        )

        # Phase 2: fetch stock for all resolved variants in parallel
        async def _fetch_for_sku(sku: str, variant: dict | None) -> StockInfo:
            if not variant:
                logger.warning("inventory_check_not_found", sku=sku)
                return StockInfo(
                    sku=sku,
                    product_name="",
                    available_stock=0,
                    committed=0,
                    expected=0,
                    in_stock=0,
                )
            return await _fetch_stock_for_variant(
                services,
                variant["id"],
                sku,
                variant.get("display_name") or variant.get("sku") or "",
            )

        async def _fetch_for_variant_id(
            variant_id: int, variant: dict | None
        ) -> StockInfo:
            if not variant:
                logger.warning("inventory_check_not_found", variant_id=variant_id)
                return StockInfo(
                    variant_id=variant_id,
                    sku="",
                    product_name="",
                    available_stock=0,
                    committed=0,
                    expected=0,
                    in_stock=0,
                )
            sku = variant.get("sku", "")
            product_name = variant.get("display_name") or sku or ""
            return await _fetch_stock_for_variant(
                services, variant_id, sku, product_name
            )

        sku_results, id_results = await asyncio.gather(
            asyncio.gather(
                *(_fetch_for_sku(s, v) for s, v in zip(skus, sku_variants, strict=True))
            ),
            asyncio.gather(
                *(
                    _fetch_for_variant_id(v_id, v)
                    for v_id, v in zip(variant_ids, id_variants, strict=True)
                )
            ),
        )
        results: list[StockInfo] = [*sku_results, *id_results]

        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.info(
            "inventory_check_completed",
            count=len(results),
            duration_ms=duration_ms,
        )
        return results

    except Exception as e:
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.error(
            "inventory_check_failed",
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
    """Check current stock levels for one or more SKUs or variant IDs.

    Accepts a single sku/variant_id or a batch list (skus/variant_ids). Returns
    available, committed, expected, and in_stock quantities summed across all
    locations.

    Use before creating orders to verify stock availability, or with a batch
    list to check multiple ingredients at once (e.g. all EXPECTED items in an
    MO recipe).
    """
    from katana_mcp.tools.prefab_ui import build_inventory_check_ui

    results = await _check_inventory_impl(request, context)

    # Single-variant request: preserve the rich Prefab card output
    is_single = len(results) == 1 and not request.skus and not request.variant_ids
    if is_single:
        response = results[0]
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

    # Batch response: summary table
    from katana_mcp.tools.tool_result_utils import format_md_table, make_simple_result

    table = format_md_table(
        headers=["SKU", "Product", "In Stock", "Committed", "Available", "Expected"],
        rows=[
            [
                r.sku,
                r.product_name[:40],
                r.in_stock,
                r.committed,
                r.available_stock,
                r.expected,
            ]
            for r in results
        ],
    )
    md = f"## Inventory Check ({len(results)} items)\n\n{table}"
    return make_simple_result(
        md,
        structured_data={"items": [r.model_dump() for r in results]},
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
    from katana_mcp.tools.tool_result_utils import format_md_table

    response = await _get_inventory_movements_impl(request, context)

    if response.movements:
        movements_md = format_md_table(
            headers=["Date", "Change", "Balance", "Type", "Order"],
            rows=[
                [
                    m.movement_date,
                    f"{m.quantity_change:+.1f}",
                    f"{m.balance_after:.1f}",
                    m.resource_type,
                    m.caused_by_order_no or "N/A",
                ]
                for m in response.movements
            ],
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

    # Generate a collision-resistant SA number using timestamp
    adj_number = f"SA-{datetime.now(tz=UTC).strftime('%Y%m%d-%H%M%S')}"

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


# ============================================================================
# Tool 5: list_stock_adjustments
# ============================================================================


class PaginationMeta(BaseModel):
    """Pagination metadata extracted from Katana's `x-pagination` response header.

    Populated on list responses only when the caller requested a specific page
    (i.e. passed `page=N`). When auto-pagination is used, this field is `None`
    because there is no single page to describe.
    """

    total_records: int | None = Field(
        default=None, description="Total records across all pages"
    )
    total_pages: int | None = Field(default=None, description="Total number of pages")
    page: int | None = Field(default=None, description="Current page number (1-based)")
    first_page: bool | None = Field(
        default=None, description="True if this is the first page"
    )
    last_page: bool | None = Field(
        default=None, description="True if this is the last page"
    )


def _parse_pagination_header(raw: str | None) -> PaginationMeta | None:
    """Parse Katana's `x-pagination` response header into a PaginationMeta.

    Katana returns this as a JSON string with all fields as strings, e.g.:
    `{"total_records":"2319","total_pages":"2319","offset":"0","page":"1",
      "first_page":"true","last_page":"false"}`.

    Returns `None` when the header is absent or the top-level JSON is invalid
    (non-JSON or not a JSON object). When the header is valid JSON but
    individual fields are missing or malformed, returns a `PaginationMeta`
    with those specific fields set to `None` rather than discarding the
    whole header.
    """
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict):
        return None

    def _as_int(val: Any) -> int | None:
        if val is None:
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            return None

    def _as_bool(val: Any) -> bool | None:
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            lowered = val.strip().lower()
            if lowered == "true":
                return True
            if lowered == "false":
                return False
        return None

    return PaginationMeta(
        total_records=_as_int(data.get("total_records")),
        total_pages=_as_int(data.get("total_pages")),
        page=_as_int(data.get("page")),
        first_page=_as_bool(data.get("first_page")),
        last_page=_as_bool(data.get("last_page")),
    )


class ListStockAdjustmentsRequest(BaseModel):
    """Request to list/filter stock adjustments."""

    limit: int = Field(
        default=50,
        ge=1,
        description=(
            "Max adjustments to return (default 50, min 1). When `page` is set, "
            "acts as the page size for that request."
        ),
    )
    page: int | None = Field(
        default=None,
        description=(
            "Page number (1-based). When set, returns a single page and "
            "disables auto-pagination; `limit` becomes the page size for "
            "that request."
        ),
    )
    location_id: int | None = Field(default=None, description="Filter by location ID")
    variant_id: int | None = Field(
        default=None,
        description=(
            "Filter to adjustments that touch this variant ID (applied "
            "client-side since Katana's list endpoint does not expose it)"
        ),
    )
    reason: str | None = Field(
        default=None,
        description=(
            "Case-insensitive substring match on the `reason` field (applied "
            "client-side since Katana's list endpoint does not expose it)"
        ),
    )
    created_after: str | None = Field(
        default=None,
        description="ISO-8601 datetime lower bound on created_at",
    )
    created_before: str | None = Field(
        default=None,
        description="ISO-8601 datetime upper bound on created_at",
    )
    include_rows: bool = Field(
        default=False,
        description="When true, populate row-level detail on each summary",
    )


class StockAdjustmentRowInfo(BaseModel):
    """Summary of a stock adjustment line item."""

    id: int | None
    variant_id: int
    quantity: float
    cost_per_unit: float | None


class StockAdjustmentSummary(BaseModel):
    """Summary row for a stock adjustment in a list."""

    id: int
    stock_adjustment_number: str
    location_id: int
    stock_adjustment_date: str | None
    created_at: str | None
    updated_at: str | None
    reason: str | None
    additional_info: str | None
    row_count: int
    rows: list[StockAdjustmentRowInfo] | None = None


class ListStockAdjustmentsResponse(BaseModel):
    """Response containing a list of stock adjustments."""

    adjustments: list[StockAdjustmentSummary]
    total_count: int
    pagination: PaginationMeta | None = Field(
        default=None,
        description=(
            "Pagination cursor populated from the API's `x-pagination` header "
            "when the caller requested a specific page. `None` when "
            "auto-paginating."
        ),
    )


def _parse_iso_datetime(value: str | None) -> datetime | None:
    """Parse an ISO-8601 string into a datetime, or return None on failure."""
    if not value:
        return None
    try:
        # datetime.fromisoformat supports "Z" suffix from Python 3.11+
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


async def _list_stock_adjustments_impl(
    request: ListStockAdjustmentsRequest, context: Context
) -> ListStockAdjustmentsResponse:
    """List stock adjustments with filters."""
    from katana_public_api_client.api.stock_adjustment import (
        get_all_stock_adjustments,
    )
    from katana_public_api_client.utils import unwrap_data

    services = get_services(context)

    # Pass through server-side filters Katana supports; variant_id and reason
    # are applied client-side below.
    kwargs: dict[str, Any] = {
        "client": services.client,
        "limit": request.limit,
    }
    if request.location_id is not None:
        kwargs["location_id"] = request.location_id

    created_at_min = _parse_iso_datetime(request.created_after)
    if created_at_min is not None:
        kwargs["created_at_min"] = created_at_min
    created_at_max = _parse_iso_datetime(request.created_before)
    if created_at_max is not None:
        kwargs["created_at_max"] = created_at_max

    # Pagination strategy:
    # - If `page` is set, forward it so PaginationTransport disables
    #   auto-pagination and lets callers walk beyond max_pages.
    # - Otherwise, when `limit` fits in a single Katana page (<=250), pass
    #   page=1 to short-circuit auto-pagination and avoid fetching thousands
    #   of rows. Lower bound is defence-in-depth with `ge=1` on Field.
    if request.page is not None:
        kwargs["page"] = request.page
    elif 1 <= request.limit <= 250:
        kwargs["page"] = 1

    response = await get_all_stock_adjustments.asyncio_detailed(**kwargs)
    attrs_list = unwrap_data(response, default=[])

    # Apply client-side filters that Katana's list endpoint doesn't accept.
    if request.variant_id is not None:
        target_variant = request.variant_id

        def _matches_variant(adj: Any) -> bool:
            rows = unwrap_unset(adj.stock_adjustment_rows, [])
            return any(row.variant_id == target_variant for row in rows)

        attrs_list = [adj for adj in attrs_list if _matches_variant(adj)]

    if request.reason is not None:
        reason_needle = request.reason.strip().lower()
        if reason_needle:

            def _matches_reason(adj: Any) -> bool:
                reason_val = unwrap_unset(adj.reason, None)
                return bool(reason_val and reason_needle in str(reason_val).lower())

            attrs_list = [adj for adj in attrs_list if _matches_reason(adj)]

    # Safety net: cap to request.limit post-pagination/filter so we never
    # return more than the caller asked for.
    attrs_list = attrs_list[: request.limit]

    # Surface pagination metadata from the `x-pagination` header only when
    # the caller is driving paging manually. During auto-pagination the header
    # describes just the final fetched page, which would be misleading.
    pagination: PaginationMeta | None = None
    if request.page is not None:
        headers = getattr(response, "headers", None)
        if headers is not None:
            pagination = _parse_pagination_header(headers.get("x-pagination"))

    adjustments: list[StockAdjustmentSummary] = []
    for adj in attrs_list:
        rows = unwrap_unset(adj.stock_adjustment_rows, [])
        row_infos: list[StockAdjustmentRowInfo] | None = None
        if request.include_rows:
            row_infos = [
                StockAdjustmentRowInfo(
                    id=unwrap_unset(row.id, None),
                    variant_id=row.variant_id,
                    quantity=row.quantity,
                    cost_per_unit=unwrap_unset(row.cost_per_unit, None),
                )
                for row in rows
            ]
        adjustments.append(
            StockAdjustmentSummary(
                id=adj.id,
                stock_adjustment_number=adj.stock_adjustment_number,
                location_id=adj.location_id,
                stock_adjustment_date=iso_or_none(
                    unwrap_unset(adj.stock_adjustment_date, None)
                ),
                created_at=iso_or_none(unwrap_unset(adj.created_at, None)),
                updated_at=iso_or_none(unwrap_unset(adj.updated_at, None)),
                reason=unwrap_unset(adj.reason, None),
                additional_info=unwrap_unset(adj.additional_info, None),
                row_count=len(rows),
                rows=row_infos,
            )
        )

    return ListStockAdjustmentsResponse(
        adjustments=adjustments,
        total_count=len(adjustments),
        pagination=pagination,
    )


@observe_tool
@unpack_pydantic_params
async def list_stock_adjustments(
    request: Annotated[ListStockAdjustmentsRequest, Unpack()], context: Context
) -> ToolResult:
    """List stock adjustments with filters.

    Use for discovery — find recent adjustments at a location, adjustments
    touching a specific variant, or adjustments matching a reason substring.
    Returns summary rows (number, location, dates, reason, row count). Set
    `include_rows=true` to also populate per-row details (variant_id, quantity,
    cost_per_unit).

    **Paging**
    - `limit` caps the number of rows returned (default 50, min 1).
    - Set `page=N` for manual paging; the response includes `pagination`
      metadata parsed from Katana's `x-pagination` header.
    - Otherwise auto-pagination kicks in automatically (bounded by
      `KatanaClient.max_pages`).

    **Filters**
    - `location_id`, `created_after`, `created_before` — server-side.
    - `variant_id`, `reason` — applied client-side; combine with other filters
      to narrow the result set before the client-side pass.
    """
    response = await _list_stock_adjustments_impl(request, context)

    if not response.adjustments:
        md = "No stock adjustments match the given filters."
    else:
        table = format_md_table(
            headers=["ID", "Number", "Location", "Date", "Rows", "Reason"],
            rows=[
                [
                    adj.id,
                    adj.stock_adjustment_number,
                    adj.location_id,
                    adj.stock_adjustment_date or "—",
                    adj.row_count,
                    (adj.reason or "—")[:40],
                ]
                for adj in response.adjustments
            ],
        )
        md = f"## Stock Adjustments ({response.total_count})\n\n{table}"

    return make_simple_result(md, structured_data=response.model_dump())


# ============================================================================
# Tool 6: update_stock_adjustment
# ============================================================================


class UpdateStockAdjustmentParams(BaseModel):
    """Request to update an existing stock adjustment."""

    id: int = Field(..., description="Stock adjustment ID to update")
    stock_adjustment_number: str | None = Field(
        default=None, description="New adjustment number (optional)"
    )
    stock_adjustment_date: datetime | None = Field(
        default=None, description="New adjustment date (ISO-8601, optional)"
    )
    location_id: int | None = Field(
        default=None, description="New location ID (optional)"
    )
    reason: str | None = Field(default=None, description="New reason (optional)")
    additional_info: str | None = Field(
        default=None, description="New additional_info (optional)"
    )
    confirm: bool = Field(
        default=False,
        description="If false, returns a preview. If true, applies the update.",
    )


class UpdateStockAdjustmentResponse(BaseModel):
    """Response from updating a stock adjustment."""

    id: int
    is_preview: bool
    stock_adjustment_number: str | None = None
    location_id: int | None = None
    stock_adjustment_date: str | None = None
    reason: str | None = None
    additional_info: str | None = None
    changes_summary: str
    message: str


def _format_changes_summary(request: UpdateStockAdjustmentParams) -> str:
    """Build a human-readable summary of the fields the update will change."""
    changes: list[str] = []
    if request.stock_adjustment_number is not None:
        changes.append(f"- stock_adjustment_number → {request.stock_adjustment_number}")
    if request.stock_adjustment_date is not None:
        changes.append(
            f"- stock_adjustment_date → {request.stock_adjustment_date.isoformat()}"
        )
    if request.location_id is not None:
        changes.append(f"- location_id → {request.location_id}")
    if request.reason is not None:
        changes.append(f"- reason → {request.reason}")
    if request.additional_info is not None:
        changes.append(f"- additional_info → {request.additional_info}")
    if not changes:
        return "No field changes supplied."
    return "\n".join(changes)


async def _update_stock_adjustment_impl(
    request: UpdateStockAdjustmentParams, context: Context
) -> UpdateStockAdjustmentResponse:
    """Update a stock adjustment with preview/confirm safety pattern."""
    from katana_public_api_client.api.stock_adjustment import (
        update_stock_adjustment as api_update_stock_adjustment,
    )
    from katana_public_api_client.models import (
        UpdateStockAdjustmentRequest as APIUpdateStockAdjustmentRequest,
    )
    from katana_public_api_client.utils import unwrap_as

    changes_summary = _format_changes_summary(request)

    # Fail fast if caller didn't supply any updatable field.
    has_changes = any(
        v is not None
        for v in (
            request.stock_adjustment_number,
            request.stock_adjustment_date,
            request.location_id,
            request.reason,
            request.additional_info,
        )
    )
    if not has_changes:
        raise ValueError(
            "At least one updatable field must be provided "
            "(stock_adjustment_number, stock_adjustment_date, location_id, "
            "reason, additional_info)"
        )

    # Preview mode — no API call.
    if not request.confirm:
        logger.info(
            "stock_adjustment_update_preview",
            id=request.id,
        )
        return UpdateStockAdjustmentResponse(
            id=request.id,
            is_preview=True,
            stock_adjustment_number=request.stock_adjustment_number,
            location_id=request.location_id,
            stock_adjustment_date=request.stock_adjustment_date.isoformat()
            if request.stock_adjustment_date
            else None,
            reason=request.reason,
            additional_info=request.additional_info,
            changes_summary=changes_summary,
            message=(
                f"Preview — call again with confirm=true to update stock "
                f"adjustment {request.id}"
            ),
        )

    # Confirm mode — elicit user confirmation before hitting the API.
    confirm_prompt = (
        f"Apply the supplied field changes to stock adjustment {request.id}?"
    )
    confirmation = await require_confirmation(context, confirm_prompt)
    if confirmation != ConfirmationResult.CONFIRMED:
        logger.info(
            "stock_adjustment_update_declined",
            id=request.id,
            result=str(confirmation),
        )
        return UpdateStockAdjustmentResponse(
            id=request.id,
            is_preview=True,
            stock_adjustment_number=request.stock_adjustment_number,
            location_id=request.location_id,
            stock_adjustment_date=request.stock_adjustment_date.isoformat()
            if request.stock_adjustment_date
            else None,
            reason=request.reason,
            additional_info=request.additional_info,
            changes_summary=changes_summary,
            message=(
                f"Stock adjustment update {confirmation} by user — "
                "call again with confirm=true to retry"
            ),
        )

    services = get_services(context)
    api_request = APIUpdateStockAdjustmentRequest(
        stock_adjustment_number=to_unset(request.stock_adjustment_number),
        stock_adjustment_date=to_unset(request.stock_adjustment_date),
        location_id=to_unset(request.location_id),
        reason=to_unset(request.reason),
        additional_info=to_unset(request.additional_info),
    )

    response = await api_update_stock_adjustment.asyncio_detailed(
        id=request.id, client=services.client, body=api_request
    )

    from katana_public_api_client.models import StockAdjustment

    try:
        updated = unwrap_as(response, StockAdjustment)
    except Exception as e:
        logger.error(
            "stock_adjustment_update_failed",
            id=request.id,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise

    logger.info(
        "stock_adjustment_updated",
        id=updated.id,
    )

    return UpdateStockAdjustmentResponse(
        id=updated.id,
        is_preview=False,
        stock_adjustment_number=updated.stock_adjustment_number,
        location_id=updated.location_id,
        stock_adjustment_date=iso_or_none(
            unwrap_unset(updated.stock_adjustment_date, None)
        ),
        reason=unwrap_unset(updated.reason, None),
        additional_info=unwrap_unset(updated.additional_info, None),
        changes_summary=changes_summary,
        message=f"Stock adjustment {updated.id} updated successfully",
    )


@observe_tool
@unpack_pydantic_params
async def update_stock_adjustment(
    request: Annotated[UpdateStockAdjustmentParams, Unpack()], context: Context
) -> ToolResult:
    """Update an existing stock adjustment's header fields.

    Two-step flow: `confirm=false` returns a preview of the changes, `confirm=true`
    prompts the user for confirmation and applies the update via PATCH. At least
    one updatable field must be supplied (stock_adjustment_number,
    stock_adjustment_date, location_id, reason, additional_info). Row-level
    changes are not supported — create a new adjustment for that.
    """
    response = await _update_stock_adjustment_impl(request, context)
    status = "PREVIEW" if response.is_preview else "UPDATED"
    md = (
        f"## Stock Adjustment {response.id} ({status})\n\n"
        f"{response.message}\n\n"
        f"### Changes\n{response.changes_summary}\n"
    )
    return make_simple_result(md, structured_data=response.model_dump())


# ============================================================================
# Tool 7: delete_stock_adjustment
# ============================================================================


class DeleteStockAdjustmentRequest(BaseModel):
    """Request to delete an existing stock adjustment."""

    id: int = Field(..., description="Stock adjustment ID to delete")
    confirm: bool = Field(
        default=False,
        description="If false, returns a preview. If true, deletes the adjustment.",
    )


class DeleteStockAdjustmentResponse(BaseModel):
    """Response from deleting a stock adjustment."""

    id: int
    is_preview: bool
    stock_adjustment_number: str | None
    location_id: int | None
    row_count: int
    message: str


async def _delete_stock_adjustment_impl(
    request: DeleteStockAdjustmentRequest, context: Context
) -> DeleteStockAdjustmentResponse:
    """Delete a stock adjustment with preview/confirm safety pattern.

    Preview mode fetches the adjustment (via the list endpoint filter) so the
    caller can see what will be removed before confirming. Confirm mode calls
    the API's DELETE endpoint, which reverses the associated inventory changes.
    """
    from katana_public_api_client.api.stock_adjustment import (
        delete_stock_adjustment as api_delete_stock_adjustment,
        get_all_stock_adjustments,
    )
    from katana_public_api_client.utils import is_success, unwrap, unwrap_data

    services = get_services(context)

    # Look up what we're about to delete so preview + final response include
    # enough detail for the user to sanity-check the action. Katana does not
    # expose GET /stock_adjustments/{id}, so we filter the list endpoint by id.
    list_response = await get_all_stock_adjustments.asyncio_detailed(
        client=services.client,
        ids=[request.id],
        limit=1,
    )
    matches = unwrap_data(list_response, default=[])
    existing = next((adj for adj in matches if adj.id == request.id), None)

    if existing is None:
        raise ValueError(f"Stock adjustment {request.id} not found")

    rows = unwrap_unset(existing.stock_adjustment_rows, [])
    row_count = len(rows)
    stock_adjustment_number = existing.stock_adjustment_number
    location_id = existing.location_id

    if not request.confirm:
        logger.info(
            "stock_adjustment_delete_preview",
            id=request.id,
            row_count=row_count,
        )
        return DeleteStockAdjustmentResponse(
            id=request.id,
            is_preview=True,
            stock_adjustment_number=stock_adjustment_number,
            location_id=location_id,
            row_count=row_count,
            message=(
                f"Preview — call again with confirm=true to delete stock "
                f"adjustment {stock_adjustment_number} "
                f"({row_count} row{'s' if row_count != 1 else ''})"
            ),
        )

    confirm_prompt = (
        f"Remove stock adjustment {stock_adjustment_number} "
        f"(id={request.id}, {row_count} rows)? "
        "This reverses the associated inventory movements."
    )
    confirmation = await require_confirmation(context, confirm_prompt)
    if confirmation != ConfirmationResult.CONFIRMED:
        logger.info(
            "stock_adjustment_delete_declined",
            id=request.id,
            result=str(confirmation),
        )
        return DeleteStockAdjustmentResponse(
            id=request.id,
            is_preview=True,
            stock_adjustment_number=stock_adjustment_number,
            location_id=location_id,
            row_count=row_count,
            message=(
                f"Stock adjustment delete {confirmation} by user — "
                "call again with confirm=true to retry"
            ),
        )

    response = await api_delete_stock_adjustment.asyncio_detailed(
        id=request.id, client=services.client
    )

    if not is_success(response):
        # unwrap raises a typed APIError/ValidationError/etc with a clean message.
        unwrap(response)

    logger.info(
        "stock_adjustment_deleted",
        id=request.id,
        stock_adjustment_number=stock_adjustment_number,
    )

    return DeleteStockAdjustmentResponse(
        id=request.id,
        is_preview=False,
        stock_adjustment_number=stock_adjustment_number,
        location_id=location_id,
        row_count=row_count,
        message=(
            f"Stock adjustment {stock_adjustment_number} (id={request.id}) "
            "deleted; associated inventory movements reversed"
        ),
    )


@observe_tool
@unpack_pydantic_params
async def delete_stock_adjustment(
    request: Annotated[DeleteStockAdjustmentRequest, Unpack()], context: Context
) -> ToolResult:
    """Delete a stock adjustment by ID.

    Two-step flow: `confirm=false` returns a preview (including the adjustment
    number, location, and row count that would be affected); `confirm=true`
    prompts the user for confirmation, then calls DELETE. Deleting a stock
    adjustment reverses the associated inventory movements.
    """
    response = await _delete_stock_adjustment_impl(request, context)
    status = "PREVIEW" if response.is_preview else "DELETED"
    md = (
        f"## Stock Adjustment {response.id} ({status})\n\n"
        f"{response.message}\n\n"
        f"- **Number**: {response.stock_adjustment_number or '—'}\n"
        f"- **Location**: {response.location_id or '—'}\n"
        f"- **Rows**: {response.row_count}\n"
    )
    return make_simple_result(md, structured_data=response.model_dump())


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

    _destructive_write = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        openWorldHint=True,
    )

    mcp.tool(tags={"inventory", "read"}, annotations=_read)(check_inventory)
    mcp.tool(tags={"inventory", "read"}, annotations=_read)(list_low_stock_items)
    mcp.tool(tags={"inventory", "read"}, annotations=_read)(get_inventory_movements)
    mcp.tool(tags={"inventory", "read"}, annotations=_read)(list_stock_adjustments)
    mcp.tool(tags={"inventory", "write"}, annotations=_write)(create_stock_adjustment)
    mcp.tool(tags={"inventory", "write"}, annotations=_write)(update_stock_adjustment)
    mcp.tool(tags={"inventory", "write"}, annotations=_destructive_write)(
        delete_stock_adjustment
    )
