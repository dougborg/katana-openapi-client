"""Inventory management tools for Katana MCP Server.

Foundation tools for checking stock levels, monitoring low stock,
and managing inventory operations.
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime
from typing import Annotated, Any, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, Field

from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.schemas import ConfirmationResult, require_confirmation
from katana_mcp.tools.tool_result_utils import (
    UI_META,
    PaginationMeta,
    format_md_table,
    iso_or_none,
    make_simple_result,
    make_tool_result,
    parse_request_dates,
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
    format: Literal["markdown", "json"] = Field(
        default="markdown",
        description=(
            "Output format: 'markdown' (default) for human-readable tables; "
            "'json' for structured data consumable by downstream tools/aggregations."
        ),
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

    if request.format == "json":
        payload = {"items": [r.model_dump() for r in results]}
        return ToolResult(
            content=json.dumps(payload, indent=2, default=str),
            structured_content=payload,
        )

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
    format: Literal["markdown", "json"] = Field(
        default="markdown",
        description=(
            "Output format: 'markdown' (default) for human-readable tables; "
            "'json' for structured data consumable by downstream tools/aggregations."
        ),
    )


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

    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2),
            structured_content=response.model_dump(),
        )

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
    format: Literal["markdown", "json"] = Field(
        default="markdown",
        description=(
            "Output format: 'markdown' (default) for human-readable tables; "
            "'json' for structured data consumable by downstream tools/aggregations."
        ),
    )


class MovementInfo(BaseModel):
    """A single inventory movement record.

    Exhaustive — every field Katana's ``InventoryMovement`` attrs model exposes
    is surfaced here (identity, location, resource pointers, valuation fields,
    timestamps, and rank) so callers don't need a follow-up lookup for standard
    fields. Field names match the canonical Pydantic/Katana names verbatim so
    LLM consumers can't confuse a rendered column header with a different
    field.
    """

    id: int
    variant_id: int
    location_id: int
    resource_type: str
    resource_id: int | None = None
    caused_by_order_no: str | None = None
    caused_by_resource_id: int | None = None
    movement_date: str
    quantity_change: float
    balance_after: float
    value_per_unit: float
    value_in_stock_after: float
    average_cost_after: float
    rank: int | None = None
    # created_at / updated_at are required on the generated InventoryMovement
    # attrs model. Typing them optional would mask real API/unwrap issues and
    # weaken the "exhaustive" contract we're pinning.
    created_at: str
    updated_at: str


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

        def _iso(val: Any) -> str:
            return val.isoformat() if hasattr(val, "isoformat") else str(val)

        def _iso_opt(val: Any) -> str | None:
            if val is None:
                return None
            return val.isoformat() if hasattr(val, "isoformat") else str(val)

        movements = [
            MovementInfo(
                id=m.id,
                variant_id=m.variant_id,
                location_id=m.location_id,
                resource_type=m.resource_type.value
                if hasattr(m.resource_type, "value")
                else str(m.resource_type),
                resource_id=unwrap_unset(m.resource_id, None),
                caused_by_order_no=unwrap_unset(m.caused_by_order_no, None),
                caused_by_resource_id=unwrap_unset(m.caused_by_resource_id, None),
                movement_date=_iso(m.movement_date),
                quantity_change=m.quantity_change,
                balance_after=m.balance_after,
                value_per_unit=m.value_per_unit,
                value_in_stock_after=m.value_in_stock_after,
                average_cost_after=m.average_cost_after,
                rank=unwrap_unset(m.rank, None),
                created_at=_iso(m.created_at),
                updated_at=_iso(m.updated_at),
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
    """Get inventory movement history for a SKU — every stock change with dates,
    quantities, valuation (value_per_unit, value_in_stock_after, average_cost_after),
    and what caused each movement (sales, purchases, manufacturing, adjustments).

    Exhaustive — every field Katana exposes on ``InventoryMovement`` is surfaced
    (identity, variant/location pointers, resource pointers, valuation fields,
    timestamps, rank) so callers don't need follow-up lookups for standard
    fields. Use to investigate stock discrepancies or trace how inventory levels
    changed over time. Default limit is 50 movements, ordered most recent first.
    """
    response = await _get_inventory_movements_impl(request, context)

    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2),
            structured_content=response.model_dump(),
        )

    # Column headers use the canonical Pydantic field names so LLM consumers
    # can't confuse a rendered header with a different field (see #346 follow-on).
    if response.movements:
        movements_md = format_md_table(
            headers=[
                "id",
                "movement_date",
                "variant_id",
                "location_id",
                "resource_type",
                "resource_id",
                "caused_by_order_no",
                "caused_by_resource_id",
                "quantity_change",
                "balance_after",
                "value_per_unit",
                "value_in_stock_after",
                "average_cost_after",
                "rank",
                "created_at",
                "updated_at",
            ],
            rows=[
                [
                    m.id,
                    m.movement_date,
                    m.variant_id,
                    m.location_id,
                    m.resource_type,
                    m.resource_id if m.resource_id is not None else "—",
                    m.caused_by_order_no or "—",
                    m.caused_by_resource_id
                    if m.caused_by_resource_id is not None
                    else "—",
                    f"{m.quantity_change:+.4f}",
                    f"{m.balance_after:.4f}",
                    f"{m.value_per_unit:.4f}",
                    f"{m.value_in_stock_after:.4f}",
                    f"{m.average_cost_after:.4f}",
                    m.rank if m.rank is not None else "—",
                    m.created_at or "—",
                    m.updated_at or "—",
                ]
                for m in response.movements
            ],
        )
    else:
        movements_md = "No movements found."

    md = (
        f"## Inventory Movements\n\n"
        f"**sku**: {response.sku}\n"
        f"**product_name**: {response.product_name}\n"
        f"**total_count**: {response.total_count}\n\n"
        f"{movements_md}"
    )
    return make_simple_result(md, structured_data=response.model_dump())


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


class ListStockAdjustmentsRequest(BaseModel):
    """Request to list/filter stock adjustments."""

    limit: int = Field(
        default=50,
        ge=1,
        le=250,
        description=(
            "Max adjustments to return (default 50, min 1, max 250). When "
            "`page` is set, acts as the page size for that request."
        ),
    )
    page: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Page number (1-based). When set, the response includes "
            "pagination metadata describing total records and pages. "
            "Invalid pages (0, negative) are rejected at the schema boundary."
        ),
    )
    location_id: int | None = Field(default=None, description="Filter by location ID")
    ids: list[int] | None = Field(
        default=None,
        description="Restrict to a specific set of stock adjustment IDs",
    )
    stock_adjustment_number: str | None = Field(
        default=None, description="Exact match on the stock adjustment number"
    )
    created_after: str | None = Field(
        default=None,
        description="ISO-8601 datetime lower bound on created_at",
    )
    created_before: str | None = Field(
        default=None,
        description="ISO-8601 datetime upper bound on created_at",
    )
    updated_after: str | None = Field(
        default=None,
        description="ISO-8601 datetime lower bound on updated_at (useful for sync)",
    )
    updated_before: str | None = Field(
        default=None,
        description="ISO-8601 datetime upper bound on updated_at",
    )
    include_deleted: bool = Field(
        default=False,
        description="Include soft-deleted adjustments in the result",
    )

    variant_id: int | None = Field(
        default=None,
        description="Filter to adjustments that touch this variant ID",
    )
    reason: str | None = Field(
        default=None,
        description="Case-insensitive substring match on the `reason` field",
    )

    include_rows: bool = Field(
        default=False,
        description="When true, populate row-level detail on each summary",
    )

    format: Literal["markdown", "json"] = Field(
        default="markdown",
        description=(
            "Output format: 'markdown' (default) for human-readable tables; "
            "'json' for structured data consumable by downstream tools/aggregations."
        ),
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
            "Pagination metadata — populated when the caller requests a "
            "specific `page`; `None` otherwise."
        ),
    )


_STOCK_ADJUSTMENT_DATE_FIELDS = (
    "created_after",
    "created_before",
    "updated_after",
    "updated_before",
)


def _apply_stock_adjustment_filters(
    stmt: Any,
    request: ListStockAdjustmentsRequest,
    parsed_dates: dict[str, datetime | None],
) -> Any:
    """Translate request filters into WHERE clauses on a CachedStockAdjustment query.

    Shared by the data SELECT and the COUNT SELECT so pagination totals
    reflect exactly the same filter set as the data rows. ``parsed_dates``
    must come from :func:`parse_request_dates` — keeping parsing out of
    this function lets the paginated path avoid re-parsing on the COUNT
    query.
    """
    from sqlmodel import exists, select

    from katana_public_api_client.models_pydantic._generated import (
        CachedStockAdjustment,
        CachedStockAdjustmentRow,
    )

    if request.location_id is not None:
        stmt = stmt.where(CachedStockAdjustment.location_id == request.location_id)
    if request.ids is not None:
        stmt = stmt.where(CachedStockAdjustment.id.in_(request.ids))
    if request.stock_adjustment_number is not None:
        stmt = stmt.where(
            CachedStockAdjustment.stock_adjustment_number
            == request.stock_adjustment_number
        )
    if not request.include_deleted:
        stmt = stmt.where(CachedStockAdjustment.deleted_at.is_(None))

    # variant_id is a row-level field — closes the filter-breadth bug
    # flagged in #342: previously this ran client-side after fetching one
    # page, so an adjustment touching variant 42 on page 7 would be missed.
    # As an EXISTS subquery it scans the indexed FK column directly.
    if request.variant_id is not None:
        row_filter = (
            select(CachedStockAdjustmentRow.id)
            .where(
                CachedStockAdjustmentRow.stock_adjustment_id
                == CachedStockAdjustment.id,
                CachedStockAdjustmentRow.variant_id == request.variant_id,
            )
            .correlate(CachedStockAdjustment)
        )
        stmt = stmt.where(exists(row_filter))

    if request.reason is not None:
        # Case-insensitive substring match. SQLite's ``LIKE`` is
        # case-insensitive for ASCII by default; ``ilike`` makes the
        # intent explicit and works across SQLAlchemy dialects.
        needle = request.reason.strip()
        if needle:
            stmt = stmt.where(CachedStockAdjustment.reason.ilike(f"%{needle}%"))

    # Date windows — all indexed SQL range queries. Iterate the field
    # tuple so adding new bounds later is one-line work.
    date_columns: list[tuple[str, Any, str]] = [
        ("created_after", CachedStockAdjustment.created_at, ">="),
        ("created_before", CachedStockAdjustment.created_at, "<="),
        ("updated_after", CachedStockAdjustment.updated_at, ">="),
        ("updated_before", CachedStockAdjustment.updated_at, "<="),
    ]
    for name, col, comp in date_columns:
        dt = parsed_dates[name]
        if dt is None:
            continue
        stmt = stmt.where(col >= dt if comp == ">=" else col <= dt)

    return stmt


async def _list_stock_adjustments_impl(
    request: ListStockAdjustmentsRequest, context: Context
) -> ListStockAdjustmentsResponse:
    """List stock adjustments with filters (cache-backed).

    Reads from the SQLModel typed cache instead of the live API.
    ``ensure_stock_adjustments_synced`` runs an incremental
    ``updated_at_min`` delta on every call (near-zero cost steady-state;
    cold-start pulls full history once); the query then translates request
    filters into indexed SQL and returns results directly — no pagination
    dance, no post-fetch client-side filtering. ``variant_id`` runs as an
    EXISTS subquery against the row table, closing the filter-breadth bug
    where adjustments touching the variant on a later page were missed.
    See ADR-0018 and #342.
    """
    from sqlalchemy.orm import selectinload
    from sqlmodel import func, select

    from katana_mcp.typed_cache import ensure_stock_adjustments_synced
    from katana_public_api_client.models_pydantic._generated import (
        CachedStockAdjustment,
        CachedStockAdjustmentRow,
    )

    services = get_services(context)

    # 1. Refresh the cache (incremental — near-zero cost steady state).
    await ensure_stock_adjustments_synced(services.client, services.typed_cache)

    # 2. Parse date filters once so the data SELECT and the (optional)
    # COUNT SELECT don't each re-parse the same ISO-8601 strings.
    parsed_dates = parse_request_dates(request, _STOCK_ADJUSTMENT_DATE_FIELDS)

    # 3. Build the data query. Pair each row with a scalar-subquery
    # ``row_count`` so the common ``include_rows=False`` case doesn't pay
    # the selectinload cost of materializing every line item just to
    # report counts.
    row_count_subq = (
        select(func.count(CachedStockAdjustmentRow.id))
        .where(CachedStockAdjustmentRow.stock_adjustment_id == CachedStockAdjustment.id)
        .correlate(CachedStockAdjustment)
        .scalar_subquery()
        .label("row_count")
    )
    stmt = select(CachedStockAdjustment, row_count_subq)
    if request.include_rows:
        stmt = stmt.options(selectinload(CachedStockAdjustment.stock_adjustment_rows))
    stmt = _apply_stock_adjustment_filters(stmt, request, parsed_dates)
    stmt = stmt.order_by(
        CachedStockAdjustment.created_at.desc(), CachedStockAdjustment.id.desc()
    )
    if request.page is not None:
        stmt = stmt.offset((request.page - 1) * request.limit).limit(request.limit)
    else:
        stmt = stmt.limit(request.limit)

    # 4. Execute data query and (when paginating) a separate COUNT for meta.
    async with services.typed_cache.session() as session:
        data_result = await session.exec(stmt)
        adjustments_with_counts: list[tuple[CachedStockAdjustment, int]] = (
            data_result.all()
        )

        pagination: PaginationMeta | None = None
        if request.page is not None:
            count_stmt = _apply_stock_adjustment_filters(
                select(func.count()).select_from(CachedStockAdjustment),
                request,
                parsed_dates,
            )
            total_records = (await session.exec(count_stmt)).one()
            total_pages = (total_records + request.limit - 1) // request.limit
            pagination = PaginationMeta(
                total_records=total_records,
                total_pages=total_pages,
                page=request.page,
                first_page=request.page == 1,
                last_page=request.page >= total_pages,
            )

    # 5. Materialize summaries.
    adjustments: list[StockAdjustmentSummary] = []
    for adj, row_count in adjustments_with_counts:
        row_infos: list[StockAdjustmentRowInfo] | None = None
        if request.include_rows:
            row_infos = [
                StockAdjustmentRowInfo(
                    id=row.id,
                    variant_id=row.variant_id,
                    quantity=row.quantity,
                    cost_per_unit=row.cost_per_unit,
                )
                for row in adj.stock_adjustment_rows
            ]
        adjustments.append(
            StockAdjustmentSummary(
                id=adj.id,
                stock_adjustment_number=adj.stock_adjustment_number,
                location_id=adj.location_id,
                stock_adjustment_date=iso_or_none(adj.stock_adjustment_date),
                created_at=iso_or_none(adj.created_at),
                updated_at=iso_or_none(adj.updated_at),
                reason=adj.reason,
                additional_info=adj.additional_info,
                row_count=row_count,
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
    """List stock adjustments with filters (cache-backed).

    Use for discovery — find recent adjustments at a location, adjustments
    touching a specific variant, or adjustments matching a reason substring.
    Returns summary rows (number, location, dates, reason, row count). Set
    `include_rows=true` to also populate per-row details (variant_id, quantity,
    cost_per_unit).

    **Paging**
    - `limit` caps the number of rows returned (default 50, min 1).
    - Set `page=N` for explicit paging; the response includes `pagination`
      metadata (total_records, total_pages, first/last flags) computed from
      a SQL COUNT against the same filter predicate.
    - Otherwise the response returns up to `limit` rows ordered by created_at
      desc with no pagination metadata.

    **Filters** all run as indexed SQL against the typed cache:
    - `location_id`, `ids`, `stock_adjustment_number`, `include_deleted` —
      direct column filters.
    - `variant_id` — EXISTS subquery on the rows table (no page-bound
      truncation; an adjustment touching the variant is found regardless
      of how many other adjustments precede it).
    - `reason` — case-insensitive `ILIKE %needle%`.
    - `created_after`/`before`, `updated_after`/`before` — date-range
      bounds on the corresponding columns.
    """
    response = await _list_stock_adjustments_impl(request, context)

    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2),
            structured_content=response.model_dump(),
        )

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
        page=1,  # Explicit page disables auto-pagination — one HTTP call suffices.
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

    mcp.tool(tags={"inventory", "read"}, annotations=_read, meta=UI_META)(
        check_inventory
    )
    mcp.tool(tags={"inventory", "read"}, annotations=_read, meta=UI_META)(
        list_low_stock_items
    )
    mcp.tool(tags={"inventory", "read"}, annotations=_read)(get_inventory_movements)
    mcp.tool(tags={"inventory", "read"}, annotations=_read)(list_stock_adjustments)
    mcp.tool(tags={"inventory", "write"}, annotations=_write)(create_stock_adjustment)
    mcp.tool(tags={"inventory", "write"}, annotations=_write)(update_stock_adjustment)
    mcp.tool(tags={"inventory", "write"}, annotations=_destructive_write)(
        delete_stock_adjustment
    )
