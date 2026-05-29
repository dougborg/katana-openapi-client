"""Purchase order management tools for Katana MCP Server.

Foundation tools for creating, receiving, and verifying purchase orders.

These tools provide:
- create_purchase_order: Create regular purchase orders with preview/apply pattern
- receive_purchase_order: Receive items from purchase orders with inventory updates
- verify_order_document: Verify supplier documents against POs
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Any, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, ConfigDict, Field

from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools._modification import (
    ConfirmableRequest,
    ModificationResponse,
    WireDatetime,
    compute_field_diff,
    make_response_verifier,
    patch_additional_info,
    to_tool_result,
)
from katana_mcp.tools._modification_dispatch import (
    ActionSpec,
    CacheMerge,
    EntityNaming,
    has_any_subpayload,
    make_delete_apply,
    make_patch_apply,
    make_post_apply,
    plan_creates,
    plan_deletes,
    plan_updates,
    run_delete_plan,
    run_modify_plan,
    safe_fetch_for_diff,
    unset_dict,
)
from katana_mcp.tools.list_coercion import CoercedIntListOpt
from katana_mcp.tools.tool_result_utils import (
    BLOCK_WARNING_PREFIX,
    UI_META,
    PaginationMeta,
    SoftDeletableResponse,
    apply_date_window_filters,
    coerce_enum,
    enum_to_str,
    iso_or_none,
    make_json_result,
    make_tool_result,
    parse_request_dates,
    resolve_entity_name,
)
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_mcp.web_urls import katana_web_url

# Modify/delete API endpoints used by the unified ``modify_purchase_order`` +
# ``delete_purchase_order`` tools. Hoisted out of per-action closures both for
# clarity (declarative dependency list) and consistency with the rest of the
# codebase. These resolve once at import time instead of on every action.
from katana_public_api_client.api.purchase_order import (
    delete_purchase_order as api_delete_purchase_order,
    get_purchase_order as api_get_purchase_order,
    update_purchase_order as api_update_purchase_order,
)
from katana_public_api_client.api.purchase_order_additional_cost_row import (
    create_po_additional_cost_row as api_create_po_additional_cost_row,
    delete_po_additional_cost as api_delete_po_additional_cost,
    get_po_additional_cost_row as api_get_po_additional_cost_row,
    update_additional_cost_row as api_update_additional_cost_row,
)
from katana_public_api_client.api.purchase_order_row import (
    create_purchase_order_row as api_create_purchase_order_row,
    delete_purchase_order_row as api_delete_purchase_order_row,
    get_purchase_order_row as api_get_purchase_order_row,
    update_purchase_order_row as api_update_purchase_order_row,
)
from katana_public_api_client.client_types import UNSET, Unset
from katana_public_api_client.domain.converters import to_unset, unwrap_unset
from katana_public_api_client.models import (
    CostDistributionMethod,
    CreatePurchaseOrderAdditionalCostRowRequest as APICreatePOAdditionalCostRowRequest,
    CreatePurchaseOrderInitialStatus,
    CreatePurchaseOrderRequest as APICreatePurchaseOrderRequest,
    CreatePurchaseOrderRowRequest as APICreatePurchaseOrderRowRequest,
    FindPurchaseOrdersBillingStatus,
    FindPurchaseOrdersStatus,
    PurchaseOrderAdditionalCostRow,
    PurchaseOrderEntityType,
    PurchaseOrderReceiveRow,
    PurchaseOrderReceiveRowBatchTransactionsItem,
    PurchaseOrderRow,
    PurchaseOrderRowRequest,
    PurchaseOrderStatus,
    RegularPurchaseOrder,
    UpdatePurchaseOrderAdditionalCostRowRequest as APIUpdatePOAdditionalCostRowRequest,
    UpdatePurchaseOrderRequest as APIUpdatePurchaseOrderRequest,
    UpdatePurchaseOrderRowRequest as APIUpdatePurchaseOrderRowRequest,
)
from katana_public_api_client.utils import is_success, unwrap, unwrap_as

logger = get_logger(__name__)

# ============================================================================
# Tool 1: create_purchase_order
# ============================================================================


class PurchaseOrderItem(BaseModel):
    """Line item for a purchase order."""

    model_config = ConfigDict(extra="forbid")

    variant_id: int = Field(..., description="Variant ID to purchase")
    quantity: float = Field(..., description="Quantity to order", gt=0)
    price_per_unit: float = Field(..., description="Unit price")
    tax_rate_id: int | None = Field(
        default=None,
        description=("Tax rate ID (optional). Look up via `list_tax_rates`."),
    )
    purchase_uom: str | None = Field(
        default=None, description="Purchase unit of measure"
    )
    purchase_uom_conversion_rate: float | None = Field(
        default=None, description="Conversion rate for purchase UOM"
    )
    arrival_date: WireDatetime | None = Field(
        default=None,
        description=(
            "Expected arrival date — ISO 8601 date or datetime "
            "(e.g. '2026-05-08T14:30:00Z' or '2026-05-08T14:30:00-08:00'). "
            "Naive datetimes (no timezone) are interpreted as UTC."
        ),
    )


class CreatePurchaseOrderRequest(BaseModel):
    """Request to create a purchase order."""

    model_config = ConfigDict(extra="forbid")

    supplier_id: int = Field(
        ...,
        description=("Supplier ID. Look up via `list_suppliers`."),
    )
    location_id: int = Field(
        ...,
        description=(
            "Location ID where items will be received. Look up via `list_locations`."
        ),
    )
    order_number: str = Field(..., description="Purchase order number")
    items: list[PurchaseOrderItem] = Field(..., description="Line items", min_length=1)
    notes: str | None = Field(default=None, description="Order notes (additional_info)")
    currency: str | None = Field(
        default=None, description="Currency code (e.g., USD, EUR)"
    )
    status: Literal["DRAFT", "NOT_RECEIVED"] = Field(
        default="DRAFT",
        description=(
            "Initial status for the new PO. Defaults to 'DRAFT'.\n"
            "- 'DRAFT': an unsent draft you can review and edit before "
            "committing the order to the supplier. This is the safe default "
            "for orders created programmatically that a human hasn't approved "
            "yet.\n"
            "- 'NOT_RECEIVED': the order is already placed/sent to the "
            "supplier and awaiting receipt — use this only when the PO has "
            "genuinely been ordered.\n"
            "The later lifecycle states (PARTIALLY_RECEIVED, RECEIVED) are "
            "reached via receive_purchase_order, not at creation. To move a "
            "PO between DRAFT and NOT_RECEIVED after creation, use "
            "modify_purchase_order."
        ),
    )
    entity_type: PurchaseOrderEntityType | None = Field(
        default=None,
        description=(
            "Type of purchase order. 'regular' (default) buys raw materials or "
            "finished goods from a supplier; 'outsourced' tracks subcontractor "
            "manufacturing — when set to 'outsourced', `tracking_location_id` is "
            "required and identifies where the outsourced work is tracked."
        ),
    )
    order_created_date: WireDatetime | None = Field(
        default=None,
        description=(
            "Date the order was placed. Leave None to let Katana stamp the "
            "current time server-side; supply a value for back-fills (e.g. "
            "importing historical orders) or to reflect the actual placement "
            "date when different from the call time."
        ),
    )
    expected_arrival_date: WireDatetime | None = Field(
        default=None,
        description=(
            "Expected full-arrival date for the order. Distinct from per-row "
            "`arrival_date` — this is the order-level estimate; row-level "
            "values can override per line item."
        ),
    )
    tracking_location_id: int | None = Field(
        default=None,
        description=(
            "Location ID for tracking outsourced orders. Required when "
            "`entity_type='outsourced'`. Look up via `list_locations`."
        ),
    )
    preview: bool = Field(
        default=True,
        description="If true (default), returns preview. If false, creates order.",
    )


class PurchaseOrderResponse(BaseModel):
    """Response from creating a purchase order."""

    id: int | None = None
    order_number: str
    supplier_id: int
    supplier_name: str | None = None
    location_id: int
    location_name: str | None = None
    status: str
    entity_type: str
    total_cost: float | None = None
    currency: str | None = None
    item_count: int | None = None
    notes: str | None = None
    is_preview: bool
    warnings: list[str] = Field(
        default_factory=list,
        description="Operator-facing warnings raised during the operation.",
    )
    next_actions: list[str] = Field(
        default_factory=list,
        description="Suggested follow-up tools to call after this response.",
    )
    message: str
    katana_url: str | None = None


def _po_response_to_tool_result(
    response: PurchaseOrderResponse,
    request: CreatePurchaseOrderRequest,
) -> ToolResult:
    """Convert PurchaseOrderResponse to ToolResult with the appropriate Prefab UI.

    On the preview branch, the rendered UI uses the direct-apply rail
    (Confirm fires ``tools/call`` directly + iframe pushes the structured
    result to the agent via ``ui/update-model-context``). This is the spike
    for the rail described in ADR-0016 (forthcoming, supersedes ADR-0015).
    """
    from katana_mcp.tools.prefab_ui import build_po_create_ui

    ui = build_po_create_ui(
        response.model_dump(mode="json"),
        confirm_request=request,
        confirm_tool="create_purchase_order",
    )

    return make_tool_result(response, ui=ui)


async def _create_purchase_order_impl(
    request: CreatePurchaseOrderRequest, context: Context
) -> PurchaseOrderResponse:
    """Implementation of create_purchase_order tool.

    Args:
        request: Request with purchase order details
        context: Server context with KatanaClient

    Returns:
        Purchase order response with details

    Raises:
        ValueError: If validation fails
        Exception: If API call fails
    """
    logger.info(
        f"{'Previewing' if request.preview else 'Creating'} purchase order {request.order_number}"
    )

    # Calculate preview total
    total_cost = sum(item.price_per_unit * item.quantity for item in request.items)

    services = get_services(context)
    from katana_public_api_client.models_pydantic._generated import (
        CachedLocation,
        CachedSupplier,
    )

    # Resolve supplier/location names from cache for both preview and apply
    # branches so the result card has the same information density either way
    # (#618). Cache-miss warnings are surfaced on whichever branch runs —
    # interactive callers see them on preview, programmatic callers using
    # ``preview=false`` directly see them on the apply response.
    (supplier_name, sup_warn), (location_name, loc_warn) = await asyncio.gather(
        resolve_entity_name(
            services.typed_cache.catalog,
            CachedSupplier,
            request.supplier_id,
            entity_label="Supplier",
        ),
        resolve_entity_name(
            services.typed_cache.catalog,
            CachedLocation,
            request.location_id,
            entity_label="Location",
        ),
    )

    if request.preview:
        logger.info(
            f"Preview mode: PO {request.order_number} would have {len(request.items)} items"
        )

        warnings: list[str] = [w for w in (sup_warn, loc_warn) if w]
        if request.entity_type == "outsourced" and request.tracking_location_id is None:
            warnings.append(
                "BLOCK: entity_type='outsourced' requires tracking_location_id. "
                "Katana will reject the create call without it."
            )

        return PurchaseOrderResponse(
            order_number=request.order_number,
            supplier_id=request.supplier_id,
            supplier_name=supplier_name,
            location_id=request.location_id,
            location_name=location_name,
            status=request.status,
            entity_type=request.entity_type or "regular",
            total_cost=total_cost,
            currency=request.currency,
            item_count=len(request.items),
            notes=request.notes,
            is_preview=True,
            warnings=warnings,
            next_actions=[
                "Review the order details",
                "Set preview=false to create the purchase order",
            ],
            message=f"Preview: Purchase order {request.order_number} with {len(request.items)} items totaling {total_cost:.2f}",
        )

    # Mirror the preview-branch BLOCK warning as a fail-fast check on the
    # apply path — clearer error than waiting for Katana's 422 when callers
    # bypass the preview UI (e.g. programmatic ``preview=false``).
    if (
        request.entity_type == PurchaseOrderEntityType.OUTSOURCED
        and request.tracking_location_id is None
    ):
        raise ValueError(
            "entity_type='outsourced' requires tracking_location_id. "
            "Either supply tracking_location_id or set entity_type='regular'."
        )

    try:
        # Build purchase order rows
        po_rows = []
        for item in request.items:
            row = PurchaseOrderRowRequest(
                variant_id=item.variant_id,
                quantity=item.quantity,
                price_per_unit=item.price_per_unit,
                tax_rate_id=to_unset(item.tax_rate_id),
                purchase_uom=to_unset(item.purchase_uom),
                purchase_uom_conversion_rate=to_unset(
                    item.purchase_uom_conversion_rate
                ),
                arrival_date=to_unset(item.arrival_date),
            )
            po_rows.append(row)

        # Build API request. order_created_date is forwarded from the caller
        # (None => UNSET => Katana server-stamps it). Previously the MCP layer
        # hardcoded datetime.now(UTC), which silently overwrote any caller
        # intent and blocked back-fills (#605).
        entity_type_attr = request.entity_type or PurchaseOrderEntityType.REGULAR
        api_request = APICreatePurchaseOrderRequest(
            order_no=request.order_number,
            supplier_id=request.supplier_id,
            location_id=request.location_id,
            purchase_order_rows=po_rows,
            entity_type=entity_type_attr,
            currency=to_unset(request.currency),
            # Always send status explicitly. The field defaults to DRAFT (see
            # CreatePurchaseOrderRequest.status) — a programmatically created PO
            # that a human hasn't approved is a draft, not an already-placed
            # order — so we never leave it UNSET and inherit Katana's
            # NOT_RECEIVED default.
            status=CreatePurchaseOrderInitialStatus(request.status),
            order_created_date=to_unset(request.order_created_date),
            expected_arrival_date=to_unset(request.expected_arrival_date),
            tracking_location_id=to_unset(request.tracking_location_id),
            additional_info=to_unset(request.notes),
        )

        # Call API
        from katana_public_api_client.api.purchase_order import (
            create_purchase_order as api_create_purchase_order,
        )

        response = await api_create_purchase_order.asyncio_detailed(
            client=services.client, body=api_request
        )

        # unwrap_as() raises typed exceptions on error, returns typed RegularPurchaseOrder
        po = unwrap_as(response, RegularPurchaseOrder)
        logger.info(f"Successfully created purchase order ID {po.id}")

        # Extract values using unwrap_unset for clean UNSET handling
        order_no = unwrap_unset(po.order_no, request.order_number)
        supplier_id = unwrap_unset(po.supplier_id, request.supplier_id)
        location_id = unwrap_unset(po.location_id, request.location_id)
        currency = unwrap_unset(po.currency, None)

        # Echo notes back so callers can visually verify the value persisted
        # — Katana exposes the field on the wire as ``additional_info``; we
        # surface our own ``notes`` request field name for symmetry with the
        # request and preview cards (#618).
        notes_echo = unwrap_unset(po.additional_info, request.notes)

        return PurchaseOrderResponse(
            id=po.id,
            order_number=order_no,
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            location_id=location_id,
            location_name=location_name,
            status=po.status.value if po.status else "UNKNOWN",
            entity_type=entity_type_attr.value,
            total_cost=total_cost,
            currency=currency,
            item_count=len(request.items),
            notes=notes_echo,
            is_preview=False,
            warnings=[w for w in (sup_warn, loc_warn) if w],
            katana_url=katana_web_url("purchase_order", po.id),
            next_actions=[
                f"Purchase order created with ID {po.id}",
                "Use receive_purchase_order to receive items when they arrive",
            ],
            message=f"Successfully created purchase order {order_no} (ID: {po.id})",
        )

    except Exception as e:
        logger.error(f"Failed to create purchase order: {e}")
        raise


@observe_tool
@unpack_pydantic_params
async def create_purchase_order(
    request: Annotated[CreatePurchaseOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Create a purchase order to buy items from a supplier.

    Two-step flow: preview=true (default) to preview totals without creating,
    then preview=false to create. Requires supplier_id,
    location_id, order_number, and at least one line item with variant_id,
    quantity, and price_per_unit. Use get_variant_details to look up variant IDs.

    Status: new POs are created in DRAFT by default — an unsent draft you can
    review and edit before committing it to the supplier. Pass
    status="NOT_RECEIVED" to create an order that's already been placed and is
    awaiting receipt. (The later RECEIVED / PARTIALLY_RECEIVED states are
    reached via receive_purchase_order; flip a PO between DRAFT and
    NOT_RECEIVED after creation with modify_purchase_order.)
    """
    response = await _create_purchase_order_impl(request, context)
    return _po_response_to_tool_result(response, request=request)


# ============================================================================
# Tool 2: receive_purchase_order
# ============================================================================


class ReceiveBatchTransaction(BaseModel):
    """Allocate a portion of a received row's quantity to a specific batch.

    Required for batch-tracked materials so receipts land on the right batch
    record. The summed ``quantity`` across an item's batch_transactions
    should equal the row-level ``quantity`` being received.
    """

    model_config = ConfigDict(extra="forbid")

    batch_id: int = Field(..., description="Batch ID to allocate received quantity to")
    quantity: float = Field(..., description="Quantity to allocate to this batch", gt=0)


class ReceiveItemRequest(BaseModel):
    """Item to receive from purchase order."""

    model_config = ConfigDict(extra="forbid")

    purchase_order_row_id: int = Field(..., description="Purchase order row ID")
    quantity: float = Field(..., description="Quantity to receive", gt=0)
    received_date: WireDatetime | None = Field(
        default=None,
        description=(
            "Optional ISO 8601 timestamp for when the items were actually "
            "received. Defaults to the time of the call, which is wrong for "
            "back-dated receives (e.g., re-receiving an old shipment after a "
            "variant correction)."
        ),
    )
    batch_transactions: list[ReceiveBatchTransaction] | None = Field(
        default=None,
        description=(
            "Optional batch allocations for this row. Required when the "
            "underlying material is batch-tracked — without it the receive "
            "either fails or assigns to a default batch. Each entry pairs a "
            "batch_id with the quantity to land on that batch."
        ),
    )


def _convert_receive_batch_transactions(
    items: list[ReceiveBatchTransaction] | None,
) -> list[PurchaseOrderReceiveRowBatchTransactionsItem] | Unset:
    """Map MCP ``ReceiveBatchTransaction`` payloads to the attrs API model.

    Returns ``UNSET`` when the caller didn't supply any transactions, so
    the wire body skips the key (Katana treats absent as 'no batch
    tracking required for this row')."""
    if not items:
        return UNSET
    return [
        PurchaseOrderReceiveRowBatchTransactionsItem(
            batch_id=bt.batch_id, quantity=bt.quantity
        )
        for bt in items
    ]


class ReceivePurchaseOrderRequest(BaseModel):
    """Request to receive items from a purchase order."""

    model_config = ConfigDict(extra="forbid")

    order_id: int = Field(..., description="Purchase order ID")
    items: list[ReceiveItemRequest] = Field(
        ..., description="Items to receive", min_length=1
    )
    preview: bool = Field(
        default=True,
        description="If true (default), returns preview. If false, receives items.",
    )


class ReceivedItemInfo(BaseModel):
    """Per-row receipt detail surfaced on the receipt card (#556).

    Pairs the row identity (variant SKU + display_name, looked up from the
    typed cache) with the receive payload (quantity, received_date, batch
    allocations) so the agent can verify *what* is being received before
    confirming — replacing the prior items_received *count*-only summary
    that left the agent reading the raw ``items=[...]`` blob below the card.
    """

    purchase_order_row_id: int
    variant_id: int | None = None
    sku: str | None = None
    display_name: str | None = None
    quantity: float
    quantity_ordered: float | None = Field(
        default=None,
        description=(
            "Total quantity on this PO row, lifted from the PO. Lets the "
            "card show 'receiving X of Y' for partial receives."
        ),
    )
    received_date: str | None = Field(
        default=None,
        description="ISO 8601 received timestamp (caller-supplied or default).",
    )
    batch_summary: str | None = Field(
        default=None,
        description=(
            "Pre-formatted batch allocations (e.g., 'batch 42x30, batch 51x22') "
            "for batch-tracked materials. None when the row carries no batch "
            "transactions."
        ),
    )
    price_per_unit: float | None = None
    row_total: float | None = Field(
        default=None,
        description="quantity * price_per_unit in the PO currency.",
    )
    currency: str | None = None


class ReceivePurchaseOrderResponse(BaseModel):
    """Response from receiving purchase order items."""

    order_id: int
    order_number: str
    status: str | None = None
    supplier_id: int | None = None
    supplier_name: str | None = None
    location_id: int | None = Field(
        default=None,
        description=(
            "Receiving location — where the received inventory physically "
            "lands. Pulled off the PO header for the receipt card so the "
            "operator confirming a receipt sees the destination at a glance "
            "(post-#card-ux Tier-3 reference data)."
        ),
    )
    location_name: str | None = Field(
        default=None,
        description=(
            "Resolved receiving-location display name (via ``resolve_entity_name`` "
            "on ``CachedLocation``). ``None`` falls back to ``'Location ID: <id>'`` "
            "on the card and surfaces a non-fatal warning."
        ),
    )
    currency: str | None = None
    total_cost: float | None = None
    items_received: int = 0
    received_items: list[ReceivedItemInfo] = Field(
        default_factory=list,
        description=(
            "Per-row breakdown of what's being received — variant identity, "
            "quantity, received_date, batch allocations. Drives the Tier 3 "
            "DataTable on the receipt card."
        ),
    )
    is_preview: bool = True
    warnings: list[str] = Field(
        default_factory=list,
        description="Operator-facing warnings raised during the operation.",
    )
    next_actions: list[str] = Field(
        default_factory=list,
        description="Suggested follow-up tools to call after this response.",
    )
    message: str


def _receive_response_to_tool_result(
    response: ReceivePurchaseOrderResponse,
    request: ReceivePurchaseOrderRequest | None = None,
) -> ToolResult:
    """Convert ReceivePurchaseOrderResponse to ToolResult with JSON content + Prefab UI.

    On the preview branch, ``request`` is plumbed into the UI so the
    "Confirm Receipt" button can re-invoke ``receive_purchase_order``
    directly with ``preview=False`` and the original items[].
    """
    from katana_mcp.tools.prefab_ui import build_receipt_ui

    # confirm_request/confirm_tool are only used by the preview-mode
    # Confirm Receipt button. Skip them on the non-preview render to keep
    # the structured UI payload trim.
    if response.is_preview and request is not None:
        ui = build_receipt_ui(
            response.model_dump(),
            confirm_request=request,
            confirm_tool="receive_purchase_order",
        )
    else:
        ui = build_receipt_ui(response.model_dump())
    return make_tool_result(response, ui=ui)


async def _enrich_received_items(
    services: Any,
    request_items: list[ReceiveItemRequest],
    po: Any,
    *,
    currency: str | None,
    default_received_date: datetime | None,
) -> list[ReceivedItemInfo]:
    """Build per-row ``ReceivedItemInfo`` entries for the receipt card.

    Joins three sources of data so the rendered table can show variant
    identity alongside the receive payload without forcing the agent to
    parse the raw ``items=[...]`` blob:

    - **The PO row** (matched by ``purchase_order_row_id``) for ordered
      qty + price_per_unit + variant_id.
    - **The typed cache** (one batched ``get_many_by_ids`` over the row
      variants) for SKU + canonical ``display_name``.
    - **The request** itself for quantity / received_date / batch
      transactions — what the user is asking to land.

    ``default_received_date`` is the fallback used by the confirm path when
    the request omitted ``received_date``. Pass ``None`` on the preview
    path so the rendered cell shows '—' instead of misrepresenting a
    timestamp the API hasn't actually assigned yet.
    """
    raw_rows = unwrap_unset(po.purchase_order_rows, None) or []
    po_rows_by_id: dict[int, Any] = {}
    for r in raw_rows:
        rid = unwrap_unset(getattr(r, "id", None), None)
        if rid is not None:
            po_rows_by_id[int(rid)] = r

    variant_ids: set[int] = set()
    for item in request_items:
        po_row = po_rows_by_id.get(item.purchase_order_row_id)
        if po_row is not None:
            vid = unwrap_unset(po_row.variant_id, None)
            if vid is not None:
                variant_ids.add(int(vid))

    from katana_public_api_client.models_pydantic._generated import CachedVariant

    variants_by_id: dict[int, Any] = (
        await services.typed_cache.catalog.get_many_by_ids(
            CachedVariant, variant_ids, include_deleted=True
        )
        if variant_ids
        else {}
    )

    received: list[ReceivedItemInfo] = []
    for item in request_items:
        po_row = po_rows_by_id.get(item.purchase_order_row_id)
        vid = unwrap_unset(po_row.variant_id, None) if po_row is not None else None
        variant = variants_by_id.get(int(vid)) if vid is not None else None

        ppu: float | None = (
            unwrap_unset(po_row.price_per_unit, None) if po_row is not None else None
        )
        ordered: float | None = (
            unwrap_unset(po_row.quantity, None) if po_row is not None else None
        )

        batch_summary: str | None = None
        if item.batch_transactions:
            # ASCII "x" so ruff's RUF001 (ambiguous-unicode) stays clean;
            # rendered card text reads naturally as "batch 42x30".
            batch_summary = ", ".join(
                f"batch {bt.batch_id}x{bt.quantity:g}" for bt in item.batch_transactions
            )

        # Preview: leave received_date as ``None`` when the caller didn't
        # supply one — the card renders '—'. Confirm: substitute the
        # default the API wire body will use so the rendered timestamp
        # matches what actually lands.
        effective_received: datetime | None = (
            item.received_date or default_received_date
        )

        received.append(
            ReceivedItemInfo(
                purchase_order_row_id=item.purchase_order_row_id,
                variant_id=int(vid) if vid is not None else None,
                sku=getattr(variant, "sku", None) if variant is not None else None,
                display_name=(
                    getattr(variant, "display_name", None)
                    if variant is not None
                    else None
                ),
                quantity=item.quantity,
                quantity_ordered=ordered,
                received_date=_iso_optional(effective_received),
                batch_summary=batch_summary,
                price_per_unit=ppu,
                row_total=(ppu * item.quantity) if ppu is not None else None,
                currency=currency,
            )
        )
    return received


async def _receive_purchase_order_impl(
    request: ReceivePurchaseOrderRequest, context: Context
) -> ReceivePurchaseOrderResponse:
    """Implementation of receive_purchase_order tool.

    Args:
        request: Request with purchase order ID and items to receive
        context: Server context with KatanaClient

    Returns:
        Receive response with details

    Raises:
        ValueError: If validation fails
        Exception: If API call fails
    """
    logger.info(
        f"{'Previewing' if request.preview else 'Receiving'} items for PO {request.order_id}"
    )

    try:
        services = get_services(context)

        # First, fetch the PO to get its details for validation and preview
        from katana_public_api_client.api.purchase_order import (
            get_purchase_order as api_get_purchase_order,
        )

        po_response = await api_get_purchase_order.asyncio_detailed(
            id=request.order_id, client=services.client
        )

        # unwrap_as() raises typed exceptions on error, returns typed RegularPurchaseOrder
        po = unwrap_as(po_response, RegularPurchaseOrder)

        order_no = unwrap_unset(po.order_no, f"PO-{request.order_id}")
        po_status = enum_to_str(unwrap_unset(po.status, None))
        supplier_id = unwrap_unset(po.supplier_id, None)
        location_id = unwrap_unset(po.location_id, None)
        currency = unwrap_unset(po.currency, None)
        total_cost = unwrap_unset(po.total, None)

        # Resolve supplier + location names up front so all return paths
        # (preview / refusal / success) carry the same Tier-3 reference
        # block (#card-ux). Pre-#card-ux only the preview path resolved
        # supplier_name (and never location_name) — the success card
        # silently dropped both, leaving the operator without the names
        # they needed to confirm what they'd just committed inventory to.
        supplier_name: str | None = None
        location_name: str | None = None
        resolution_warnings: list[str] = []
        if supplier_id is not None:
            from katana_public_api_client.models_pydantic._generated import (
                CachedSupplier,
            )

            supplier_name, sup_warn = await resolve_entity_name(
                services.typed_cache.catalog,
                CachedSupplier,
                supplier_id,
                entity_label="Supplier",
            )
            if sup_warn:
                resolution_warnings.append(sup_warn)
        if location_id is not None:
            from katana_public_api_client.models_pydantic._generated import (
                CachedLocation,
            )

            location_name, loc_warn = await resolve_entity_name(
                services.typed_cache.catalog,
                CachedLocation,
                location_id,
                entity_label="Location",
            )
            if loc_warn:
                resolution_warnings.append(loc_warn)

        if request.preview:
            logger.info(
                f"Preview mode: Would receive {len(request.items)} items for PO {order_no}"
            )

            warnings: list[str] = list(resolution_warnings)

            next_actions = [
                "Review the items to receive",
                "Set preview=false to receive the items and update inventory",
            ]
            if po_status == "RECEIVED":
                warnings.append(
                    f"{BLOCK_WARNING_PREFIX} Purchase order {order_no} is already "
                    "RECEIVED. Receiving more items would create duplicate inventory."
                )
                next_actions = ["No action needed — order is already fully received."]

            # Preview path: pass ``default_received_date=None`` so missing
            # ``received_date`` renders as '—' instead of misrepresenting a
            # timestamp the API hasn't actually assigned yet.
            received_items_info = await _enrich_received_items(
                services,
                request.items,
                po,
                currency=currency,
                default_received_date=None,
            )

            return ReceivePurchaseOrderResponse(
                order_id=request.order_id,
                order_number=order_no,
                status=po_status,
                supplier_id=supplier_id,
                supplier_name=supplier_name,
                location_id=location_id,
                location_name=location_name,
                currency=currency,
                total_cost=total_cost,
                items_received=len(request.items),
                received_items=received_items_info,
                is_preview=True,
                warnings=warnings,
                next_actions=next_actions,
                message=f"Preview: Receive {len(request.items)} items for PO {order_no}",
            )

        # Confirm-path defense-in-depth: a direct caller skipping the preview
        # would otherwise be able to receive items against an already-fully-
        # received PO and create duplicate inventory.
        if po_status == "RECEIVED":
            # Refusal carries the cache-miss advisories alongside the
            # BLOCK warning so the operator sees both "why we refused"
            # AND "why these names didn't resolve" — review item #11.
            # Pre-fix this branch hard-coded a single-string list and
            # silently dropped ``resolution_warnings``.
            return ReceivePurchaseOrderResponse(
                order_id=request.order_id,
                order_number=order_no,
                status=po_status,
                supplier_id=supplier_id,
                supplier_name=supplier_name,
                location_id=location_id,
                location_name=location_name,
                currency=currency,
                total_cost=total_cost,
                items_received=0,
                is_preview=False,
                warnings=[
                    f"{BLOCK_WARNING_PREFIX} Purchase order {order_no} is already "
                    "RECEIVED. No items were received.",
                    *resolution_warnings,
                ],
                next_actions=["No action needed — order is already fully received."],
                message=(
                    f"Refused: PO {order_no} is already RECEIVED; "
                    "no duplicate inventory created."
                ),
            )

        from katana_public_api_client.api.purchase_order import (
            receive_purchase_order as api_receive_purchase_order,
        )

        # Caller-supplied received_date wins; fall back to "now" so callers
        # who don't care still get a sensible timestamp. Without this branch
        # back-dated re-receives (variant fixes, late paperwork) silently
        # land on the call time — see #505.
        default_received_date = datetime.now(UTC)
        receive_rows = [
            PurchaseOrderReceiveRow(
                purchase_order_row_id=item.purchase_order_row_id,
                quantity=item.quantity,
                received_date=item.received_date or default_received_date,
                batch_transactions=_convert_receive_batch_transactions(
                    item.batch_transactions
                ),
            )
            for item in request.items
        ]

        response = await api_receive_purchase_order.asyncio_detailed(
            client=services.client, body=receive_rows
        )

        # Use is_success for 204 No Content response
        if not is_success(response):
            # unwrap will raise with appropriate error details
            unwrap(response)

        logger.info(
            f"Successfully received {len(request.items)} items for PO {order_no}"
        )
        # Confirm path: same per-row enrichment, but pass the effective
        # ``default_received_date`` we just wrote to the wire body so the
        # rendered timestamp matches what actually landed.
        received_items_info = await _enrich_received_items(
            services,
            request.items,
            po,
            currency=currency,
            default_received_date=default_received_date,
        )
        return ReceivePurchaseOrderResponse(
            order_id=request.order_id,
            order_number=order_no,
            status=po_status,
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            location_id=location_id,
            location_name=location_name,
            currency=currency,
            total_cost=total_cost,
            items_received=len(request.items),
            received_items=received_items_info,
            is_preview=False,
            warnings=resolution_warnings,
            next_actions=[
                f"Received {len(request.items)} items",
                "Inventory has been updated",
                "To apportion landed costs (customs, freight, duties) to this "
                "receipt, call modify_purchase_order(add_additional_costs="
                "[{additional_cost_id, price, tax_rate_id, distribution_method, "
                "group_id}]) — look up additional_cost_id via "
                "list_additional_costs and target the receipt's group_id (find "
                "it on the PO via get_purchase_order).",
            ],
            message=f"Successfully received {len(request.items)} items for PO {order_no}",
        )

    except Exception as e:
        logger.error(f"Failed to receive purchase order: {e}")
        raise


@observe_tool
@unpack_pydantic_params
async def receive_purchase_order(
    request: Annotated[ReceivePurchaseOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Receive delivered items from a purchase order and update inventory.

    Two-step flow: preview=true (default) to preview, preview=false to receive.
    Use verify_order_document first to validate a supplier document against the
    PO before receiving. Requires the PO ID and row IDs. Each item may include
    an optional ISO 8601 ``received_date`` for back-dated receives — without it,
    rows land on the call time.

    Landed costs (customs, freight, duties) are *not* set here. After
    receiving, apportion them with
    ``modify_purchase_order(add_additional_costs=[{additional_cost_id, price,
    tax_rate_id, distribution_method, group_id}])`` — ``add_additional_costs``
    can target a specific receipt group via ``group_id``. Look up
    ``additional_cost_id`` via ``list_additional_costs``. This is an MCP-native
    path; it does not require the Katana UI.
    """
    response = await _receive_purchase_order_impl(request, context)
    return _receive_response_to_tool_result(response, request=request)


# ============================================================================
# Tool: get_purchase_order
#
# Defined before ``verify_order_document`` so the verification tool can embed
# the same exhaustive ``GetPurchaseOrderResponse`` shape on its response
# (avoids a forward-reference + ``model_rebuild`` dance).
# ============================================================================


class GetPurchaseOrderRequest(BaseModel):
    """Request to look up a purchase order by number or ID."""

    model_config = ConfigDict(extra="forbid")

    order_no: str | None = Field(
        default=None, description="Purchase order number (e.g., 'PO-1022')"
    )
    order_id: int | None = Field(default=None, description="Purchase order ID")


class PurchaseOrderRowInfo(SoftDeletableResponse):
    """Full purchase order line item — every field Katana exposes on
    ``PurchaseOrderRow`` is surfaced so callers don't need follow-up lookups
    for standard row fields (UOM conversion, currency, landed_cost, etc.).
    """

    id: int
    created_at: str | None = None
    updated_at: str | None = None
    quantity: float | None = None
    variant_id: int | None = None
    sku: str | None = None
    """SKU lifted from the typed cache via the row's ``variant_id``. Adds no
    cost over the existing variant lookup ``_get_purchase_order_impl`` already
    does for ``display_name``.
    """
    display_name: str | None = None
    """Katana-UI-format human-readable name for this row's variant.

    Lifted from the typed-cache ``CachedVariant.display_name`` column.
    ``None`` when the variant can't be resolved (rare — deleted variant).
    """
    tax_rate_id: int | None = None
    price_per_unit: float | None = None
    price_per_unit_in_base_currency: float | None = None
    purchase_uom_conversion_rate: float | None = None
    purchase_uom: str | None = None
    currency: str | None = None
    conversion_rate: float | None = None
    total: float | None = None
    total_in_base_currency: float | None = None
    conversion_date: str | None = None
    received_date: str | None = None
    arrival_date: str | None = None
    purchase_order_id: int | None = None
    landed_cost: float | str | None = None
    group_id: int | None = None
    batch_transactions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Batch allocations for this row's received quantity.",
    )


class PurchaseOrderAdditionalCostRowInfo(SoftDeletableResponse):
    """Full additional cost row — every field Katana exposes on
    ``PurchaseOrderAdditionalCostRow`` (shipping, duties, handling, etc.).
    """

    id: int
    created_at: str | None = None
    updated_at: str | None = None
    additional_cost_id: int | None = None
    group_id: int | None = None
    name: str | None = None
    distribution_method: str | None = None
    tax_rate_id: int | None = None
    tax_rate: float | None = None
    price: float | None = None
    price_in_base: float | None = None
    currency: str | None = None
    currency_conversion_rate: float | None = None
    currency_conversion_rate_fix_date: str | None = None


class PurchaseOrderAccountingMetadataInfo(BaseModel):
    """Full accounting-integration metadata — every field Katana exposes on
    ``PurchaseOrderAccountingMetadata`` (bill IDs, integration type, etc.).
    """

    id: int
    purchase_order_id: int
    received_items_group_id: int | None = None
    integration_type: str | None = None
    bill_id: str | None = None
    created_at: str | None = None


class SupplierInfo(SoftDeletableResponse):
    """Embedded supplier details — every field Katana exposes on
    ``Supplier`` when the PO payload includes the inline supplier record.
    """

    id: int
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    currency: str | None = None
    comment: str | None = None
    default_address_id: int | None = None
    addresses: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Supplier address records (billing/shipping).",
    )
    created_at: str | None = None
    updated_at: str | None = None


class GetPurchaseOrderResponse(SoftDeletableResponse):
    """Full purchase-order details. Exhaustive — every field Katana exposes
    on ``RegularPurchaseOrder`` is surfaced, plus nested inline rows and
    fetched-on-demand additional cost rows and accounting metadata. Callers
    don't need follow-up lookups for standard PO data.
    """

    id: int
    katana_url: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    status: str | None = None
    order_no: str | None = None
    entity_type: str | None = None
    default_group_id: int | None = None
    supplier_id: int | None = None
    supplier: SupplierInfo | None = None
    currency: str | None = None
    expected_arrival_date: str | None = None
    order_created_date: str | None = None
    additional_info: str | None = None
    location_id: int | None = None
    total: float | None = None
    total_in_base_currency: float | None = None
    billing_status: str | None = None
    last_document_status: str | None = None
    tracking_location_id: int | None = None
    purchase_order_rows: list[PurchaseOrderRowInfo] = Field(
        default_factory=list,
        description="Line items on the purchase order.",
    )
    additional_cost_rows: list[PurchaseOrderAdditionalCostRowInfo] = Field(
        default_factory=list,
        description="Additional cost rows (shipping, duties, handling fees).",
    )
    accounting_metadata: list[PurchaseOrderAccountingMetadataInfo] = Field(
        default_factory=list,
        description="Accounting integration metadata (bill IDs, integration type).",
    )


def _iso_optional(value: datetime | str | None) -> str | None:
    """Return an ISO-8601 string for a datetime-or-str value, else None.

    Callers must pre-unwrap UNSET via ``unwrap_unset(..., None)`` — this
    helper only handles ``None``, a ``datetime``, or an already-formatted
    string. Typed ``datetime | str | None`` so pyright catches misuse.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _po_row_info(
    row: Any,
    *,
    sku: str | None = None,
    display_name: str | None = None,
) -> PurchaseOrderRowInfo:
    """Extract full row info from an attrs ``PurchaseOrderRow``.

    ``sku`` and ``display_name`` are looked up upstream in
    ``_get_purchase_order_impl`` from the typed cache (one batched read for
    every row's variant); pass them in so each rendered row carries the
    canonical name without an extra API call per row.
    """
    # batch_transactions items are attrs models — serialize them to dicts so
    # Pydantic can validate the list shape without cross-model coupling.
    raw_batch = unwrap_unset(row.batch_transactions, None) or []
    batch_dicts: list[dict[str, Any]] = []
    for bt in raw_batch:
        if hasattr(bt, "to_dict"):
            batch_dicts.append(bt.to_dict())
        elif isinstance(bt, dict):
            batch_dicts.append(bt)

    return PurchaseOrderRowInfo(
        id=row.id,
        created_at=_iso_optional(unwrap_unset(row.created_at, None)),
        updated_at=_iso_optional(unwrap_unset(row.updated_at, None)),
        deleted_at=_iso_optional(unwrap_unset(row.deleted_at, None)),
        quantity=unwrap_unset(row.quantity, None),
        variant_id=unwrap_unset(row.variant_id, None),
        sku=sku,
        display_name=display_name,
        tax_rate_id=unwrap_unset(row.tax_rate_id, None),
        price_per_unit=unwrap_unset(row.price_per_unit, None),
        price_per_unit_in_base_currency=unwrap_unset(
            row.price_per_unit_in_base_currency, None
        ),
        purchase_uom_conversion_rate=unwrap_unset(
            row.purchase_uom_conversion_rate, None
        ),
        purchase_uom=unwrap_unset(row.purchase_uom, None),
        currency=unwrap_unset(row.currency, None),
        conversion_rate=unwrap_unset(row.conversion_rate, None),
        total=unwrap_unset(row.total, None),
        total_in_base_currency=unwrap_unset(row.total_in_base_currency, None),
        conversion_date=_iso_optional(unwrap_unset(row.conversion_date, None)),
        received_date=_iso_optional(unwrap_unset(row.received_date, None)),
        arrival_date=_iso_optional(unwrap_unset(row.arrival_date, None)),
        purchase_order_id=unwrap_unset(row.purchase_order_id, None),
        landed_cost=unwrap_unset(row.landed_cost, None),
        group_id=unwrap_unset(row.group_id, None),
        batch_transactions=batch_dicts,
    )


def _po_additional_cost_row_info(row: Any) -> PurchaseOrderAdditionalCostRowInfo:
    """Extract full info from an attrs ``PurchaseOrderAdditionalCostRow``."""
    return PurchaseOrderAdditionalCostRowInfo(
        id=row.id,
        created_at=_iso_optional(unwrap_unset(row.created_at, None)),
        updated_at=_iso_optional(unwrap_unset(row.updated_at, None)),
        deleted_at=_iso_optional(unwrap_unset(row.deleted_at, None)),
        additional_cost_id=unwrap_unset(row.additional_cost_id, None),
        group_id=unwrap_unset(row.group_id, None),
        name=unwrap_unset(row.name, None),
        distribution_method=enum_to_str(unwrap_unset(row.distribution_method, None)),
        tax_rate_id=unwrap_unset(row.tax_rate_id, None),
        tax_rate=unwrap_unset(row.tax_rate, None),
        price=unwrap_unset(row.price, None),
        price_in_base=unwrap_unset(row.price_in_base, None),
        currency=unwrap_unset(row.currency, None),
        currency_conversion_rate=unwrap_unset(row.currency_conversion_rate, None),
        currency_conversion_rate_fix_date=_iso_optional(
            unwrap_unset(row.currency_conversion_rate_fix_date, None)
        ),
    )


def _po_accounting_metadata_info(row: Any) -> PurchaseOrderAccountingMetadataInfo:
    """Extract full info from an attrs ``PurchaseOrderAccountingMetadata``."""
    return PurchaseOrderAccountingMetadataInfo(
        id=row.id,
        purchase_order_id=row.purchase_order_id,
        received_items_group_id=unwrap_unset(row.received_items_group_id, None),
        integration_type=unwrap_unset(row.integration_type, None),
        bill_id=unwrap_unset(row.bill_id, None),
        created_at=_iso_optional(unwrap_unset(row.created_at, None)),
    )


def _supplier_info(supplier: Any) -> SupplierInfo | None:
    """Extract full info from an embedded attrs ``Supplier`` record.

    Returns ``None`` when the PO payload doesn't include an inline supplier
    (Katana only embeds the supplier on some endpoints — the exhaustive
    response surfaces it when it's there so callers don't need a follow-up
    lookup).
    """
    if supplier is None:
        return None
    # Addresses are attrs models — serialize to plain dicts so Pydantic can
    # validate the list shape without cross-model coupling.
    raw_addresses = unwrap_unset(supplier.addresses, None) or []
    address_dicts: list[dict[str, Any]] = []
    for addr in raw_addresses:
        if hasattr(addr, "to_dict"):
            address_dicts.append(addr.to_dict())
        elif isinstance(addr, dict):
            address_dicts.append(addr)

    return SupplierInfo(
        id=supplier.id,
        name=unwrap_unset(supplier.name, None),
        email=unwrap_unset(supplier.email, None),
        phone=unwrap_unset(supplier.phone, None),
        currency=unwrap_unset(supplier.currency, None),
        comment=unwrap_unset(supplier.comment, None),
        default_address_id=unwrap_unset(supplier.default_address_id, None),
        addresses=address_dicts,
        created_at=_iso_optional(unwrap_unset(supplier.created_at, None)),
        updated_at=_iso_optional(unwrap_unset(supplier.updated_at, None)),
        deleted_at=_iso_optional(unwrap_unset(supplier.deleted_at, None)),
    )


async def _fetch_po_additional_cost_rows(
    services: Any, group_id: int | None
) -> list[PurchaseOrderAdditionalCostRowInfo]:
    """Fetch additional cost rows for a PO via its ``default_group_id``.

    The ``/po_additional_cost_rows`` list endpoint filters by ``group_id``,
    which for the PO-scope is the PO's ``default_group_id``. Returns an
    empty list when no ``group_id`` is available (the PO has no group).
    """
    if group_id is None:
        return []

    import httpx

    from katana_public_api_client.api.purchase_order_additional_cost_row import (
        get_purchase_order_additional_cost_rows,
    )
    from katana_public_api_client.errors import UnexpectedStatus
    from katana_public_api_client.utils import unwrap_data

    # Best-effort: transport errors (httpx timeouts/connection) and unexpected
    # statuses degrade to []. `unwrap_data(default=[])` alone only handles
    # non-200 parsed responses, not errors raised before the response lands.
    try:
        # The generated client types `group_id` as float for historical spec
        # reasons; cast at the boundary like `list_purchase_orders` does.
        response = await get_purchase_order_additional_cost_rows.asyncio_detailed(
            client=services.client,
            group_id=float(group_id),
            limit=250,
        )
    except (httpx.HTTPError, UnexpectedStatus):
        return []
    rows = unwrap_data(response, default=[], raise_on_error=False)
    return [_po_additional_cost_row_info(r) for r in rows]


async def _fetch_po_accounting_metadata(
    services: Any, purchase_order_id: int
) -> list[PurchaseOrderAccountingMetadataInfo]:
    """Fetch accounting metadata entries for a PO.

    The ``/purchase_order_accounting_metadata`` list endpoint filters by
    ``purchase_order_id``. Returns an empty list when the PO has no
    accounting-integration rows.
    """
    import httpx

    from katana_public_api_client.api.purchase_order_accounting_metadata import (
        get_all_purchase_order_accounting_metadata,
    )
    from katana_public_api_client.errors import UnexpectedStatus
    from katana_public_api_client.utils import unwrap_data

    # Best-effort: same pattern as _fetch_po_additional_cost_rows — transport
    # errors don't take down get_purchase_order when the core PO was fine.
    try:
        # Generated client types `purchase_order_id` as float; cast at boundary.
        response = await get_all_purchase_order_accounting_metadata.asyncio_detailed(
            client=services.client,
            purchase_order_id=float(purchase_order_id),
            limit=250,
        )
    except (httpx.HTTPError, UnexpectedStatus):
        return []
    rows = unwrap_data(response, default=[], raise_on_error=False)
    return [_po_accounting_metadata_info(r) for r in rows]


def _build_get_purchase_order_response(
    po: Any,
    *,
    additional_cost_rows: list[PurchaseOrderAdditionalCostRowInfo],
    accounting_metadata: list[PurchaseOrderAccountingMetadataInfo],
    variants_by_id: dict[int, Any] | None = None,
) -> GetPurchaseOrderResponse:
    """Build an exhaustive response from an attrs PO plus fetched side data.

    ``variants_by_id`` is the result of a batched typed-cache lookup for
    every row's variant — passing it in lets each ``PurchaseOrderRowInfo``
    carry the canonical SKU and Katana-UI ``display_name`` without any
    extra API calls per row. Optional for callers that don't need the
    enrichment (legacy code paths, fixture-driven tests); rows then surface
    ``sku=None`` / ``display_name=None``.
    """
    variants_by_id = variants_by_id or {}

    def _attr_or_none(v: Any, name: str) -> Any:
        if v is None:
            return None
        if isinstance(v, dict):
            return v.get(name)
        return getattr(v, name, None)

    def _variant_for(row: Any) -> Any:
        # ``variant_id`` may be ``None`` on stub rows; the typed-cache map
        # only ever stores int keys, so guard against ``None`` lookups to
        # keep ty/pyright satisfied (``dict.get(None)`` widens the value
        # type and silently shadows hits).
        vid = unwrap_unset(row.variant_id, None)
        return variants_by_id.get(vid) if vid is not None else None

    raw_rows = unwrap_unset(po.purchase_order_rows, None) or []
    rows = [
        _po_row_info(
            r,
            sku=_attr_or_none(_variant_for(r), "sku"),
            display_name=_attr_or_none(_variant_for(r), "display_name"),
        )
        for r in raw_rows
    ]
    supplier = _supplier_info(unwrap_unset(po.supplier, None))

    return GetPurchaseOrderResponse(
        id=po.id,
        katana_url=katana_web_url("purchase_order", po.id),
        created_at=_iso_optional(unwrap_unset(po.created_at, None)),
        updated_at=_iso_optional(unwrap_unset(po.updated_at, None)),
        deleted_at=_iso_optional(unwrap_unset(po.deleted_at, None)),
        status=enum_to_str(unwrap_unset(po.status, None)),
        order_no=unwrap_unset(po.order_no, None),
        entity_type=enum_to_str(unwrap_unset(po.entity_type, None)),
        default_group_id=unwrap_unset(po.default_group_id, None),
        supplier_id=unwrap_unset(po.supplier_id, None),
        supplier=supplier,
        currency=unwrap_unset(po.currency, None),
        expected_arrival_date=_iso_optional(
            unwrap_unset(po.expected_arrival_date, None)
        ),
        order_created_date=_iso_optional(unwrap_unset(po.order_created_date, None)),
        additional_info=unwrap_unset(po.additional_info, None),
        location_id=unwrap_unset(po.location_id, None),
        total=unwrap_unset(po.total, None),
        total_in_base_currency=unwrap_unset(po.total_in_base_currency, None),
        billing_status=enum_to_str(unwrap_unset(po.billing_status, None)),
        last_document_status=enum_to_str(unwrap_unset(po.last_document_status, None)),
        tracking_location_id=unwrap_unset(po.tracking_location_id, None),
        purchase_order_rows=rows,
        additional_cost_rows=additional_cost_rows,
        accounting_metadata=accounting_metadata,
    )


async def _get_purchase_order_impl(
    request: GetPurchaseOrderRequest, context: Context
) -> GetPurchaseOrderResponse:
    """Look up a PO by order_no or ID and return exhaustive details.

    Additional cost rows and accounting metadata are fetched on demand from
    separate endpoints — two extra HTTP calls per ``get_purchase_order``.
    """
    from katana_public_api_client.api.purchase_order import (
        find_purchase_orders,
        get_purchase_order as api_get_purchase_order,
    )
    from katana_public_api_client.models import ErrorResponse
    from katana_public_api_client.utils import unwrap_data

    # Explicit ``is None`` checks so valid-but-falsy values (``order_id=0``,
    # ``order_no=""``) don't silently route to the wrong branch or error.
    # Empty-string ``order_no`` is rejected up front as obviously invalid.
    if request.order_id is None and request.order_no is None:
        raise ValueError("Either order_no or order_id must be provided")
    if request.order_no is not None and request.order_no == "":
        raise ValueError("order_no must not be empty")

    services = get_services(context)

    if request.order_id is not None:
        response = await api_get_purchase_order.asyncio_detailed(
            id=request.order_id, client=services.client
        )
        # raise_on_error=False turns 404s and ErrorResponse payloads into None
        # so we can raise a user-friendly ValueError instead of a raw APIError.
        po_result = unwrap(response, raise_on_error=False)
        if po_result is None or isinstance(po_result, ErrorResponse):
            raise ValueError(f"Purchase order ID {request.order_id} not found")
        po = po_result
    else:
        # ``order_no`` is guaranteed non-None/non-empty by the guards above.
        assert request.order_no is not None
        list_response = await find_purchase_orders.asyncio_detailed(
            client=services.client, order_no=request.order_no, limit=1
        )
        orders = unwrap_data(list_response, default=[])
        if not orders:
            raise ValueError(f"Purchase order '{request.order_no}' not found")
        po = orders[0]

    # Fetch the two side-data resources concurrently — they're independent
    # network calls (cost rows filter by group_id, accounting metadata by
    # purchase_order_id), so gather avoids doubling end-to-end latency.
    default_group_id = unwrap_unset(po.default_group_id, None)
    additional_cost_rows, accounting_metadata = await asyncio.gather(
        _fetch_po_additional_cost_rows(services, default_group_id),
        _fetch_po_accounting_metadata(services, po.id),
    )

    # Enrich each row with its variant's SKU + canonical display_name from
    # the typed cache — one batched IN-clause read instead of an API call
    # per row. Cache misses simply yield ``None`` for both fields
    # (consistent with the surface convention).
    raw_rows = unwrap_unset(po.purchase_order_rows, None) or []
    variant_ids: set[int] = {
        vid
        for vid in (unwrap_unset(r.variant_id, None) for r in raw_rows)
        if vid is not None
    }
    from katana_public_api_client.models_pydantic._generated import CachedVariant

    variants_by_id: dict[int, Any] = (
        await services.typed_cache.catalog.get_many_by_ids(
            CachedVariant, variant_ids, include_deleted=True
        )
        if variant_ids
        else {}
    )

    return _build_get_purchase_order_response(
        po,
        additional_cost_rows=additional_cost_rows,
        accounting_metadata=accounting_metadata,
        variants_by_id=variants_by_id,
    )


# ----------------------------------------------------------------------------
@observe_tool
@unpack_pydantic_params
async def get_purchase_order(
    request: Annotated[GetPurchaseOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Look up a purchase order by order number or ID — exhaustive detail.

    For multiple purchase orders at once, use ``list_purchase_orders(ids=[...])`` —
    it returns a summary table and supports all the same filters.

    Returns every field Katana exposes on the PO record: status, billing
    status, supplier, location, totals (including base-currency total),
    timestamps, document status, tracking location, additional_info, plus
    the full list of line items with every row field (UOM, conversion
    rates, landed_cost, batch_transactions), the full list of additional
    cost rows (shipping, duties, handling), and accounting-integration
    metadata (bill IDs).

    Two extra HTTP calls are made on top of the PO fetch — one for
    additional cost rows, one for accounting metadata — so callers don't
    need follow-up lookups for standard PO data. Use this tool whenever
    full detail is needed; use ``list_purchase_orders`` for discovery.

    Provide either order_no (e.g., 'PO-1022') or order_id.
    """
    response = await _get_purchase_order_impl(request, context)
    return make_json_result(response)


# ============================================================================
# Tool: verify_order_document
# ============================================================================


class DocumentItem(BaseModel):
    """Item from a supplier document to verify."""

    model_config = ConfigDict(extra="forbid")

    sku: str = Field(..., description="Item SKU from document")
    quantity: float = Field(..., description="Quantity from document")
    unit_price: float | None = Field(default=None, description="Price from document")


class MatchResult(BaseModel):
    """Result of matching a document item to a PO line.

    Carries both the **document-side** values (``quantity``, ``unit_price``)
    and the **PO-side** values (``expected_quantity``, ``expected_unit_price``)
    so the verification card can render side-by-side comparison columns
    without rummaging through the embedded ``purchase_order`` for the PO
    row. On a ``"perfect"`` status the document-side and PO-side
    quantities are equal **only when both sides provided a quantity** —
    when ``expected_quantity`` is ``None`` (the underlying
    ``PurchaseOrderRow.quantity`` was ``Unset``) the quantity check is
    skipped (status can still be ``"perfect"``). The same rule applies
    to prices: they are equal **only when both sides provided a
    price** — when either ``unit_price`` or ``expected_unit_price`` is
    ``None`` the price check is skipped (status can still be
    ``"perfect"``). PO-side fields propagate ``None`` when the
    underlying ``PurchaseOrderRow`` value is ``Unset``; the card
    renders these as empty cells rather than misleading ``0.00``
    placeholders. The pairs diverge on the other statuses
    (``quantity_diff`` / ``price_diff`` / ``both_diff``).
    """

    sku: str = Field(..., description="Item SKU")
    display_name: str = Field(
        default="",
        description=(
            "Katana-UI-format human-readable name "
            "(``{parent_name} / {config1} / ...``) — built via "
            ":func:`build_variant_display_name` from the PO row's variant + "
            "parent product/material lookup so the verification card shows "
            "the same canonical name as every other variant-displaying "
            "surface. Empty string when the variant can't be resolved "
            "(rare — would mean the PO row references a deleted variant)."
        ),
    )
    quantity: float = Field(..., description="Document-side quantity")
    unit_price: float | None = Field(
        default=None, description="Document-side unit price"
    )
    expected_quantity: float | None = Field(
        default=None,
        description=(
            "PO-side quantity copied from the matched ``PurchaseOrderRow`` "
            "so the verification card can render a Qty (doc) vs Qty (PO) "
            "side-by-side column without rummaging through the embedded "
            "``purchase_order``."
        ),
    )
    expected_unit_price: float | None = Field(
        default=None,
        description=(
            "PO-side unit price copied from the matched "
            "``PurchaseOrderRow.price_per_unit`` so the verification card "
            "can render a Price (doc) vs Price (PO) side-by-side column "
            "without rummaging through the embedded ``purchase_order``."
        ),
    )
    status: str = Field(
        ...,
        description="Match status (perfect, quantity_diff, price_diff, both_diff)",
    )


class DiscrepancyType(StrEnum):
    """Types of discrepancies found during order document verification."""

    QUANTITY_MISMATCH = "quantity_mismatch"
    PRICE_MISMATCH = "price_mismatch"
    MISSING_IN_PO = "missing_in_po"


class Discrepancy(BaseModel):
    """A discrepancy found during verification."""

    sku: str = Field(..., description="Item SKU")
    display_name: str = Field(
        default="",
        description=(
            "Katana-UI-format human-readable name "
            "(``{parent_name} / {config1} / ...``). Empty string for "
            "``MISSING_IN_PO`` discrepancies (the document item's SKU "
            "didn't match any PO row, so there's no variant to resolve "
            "against)."
        ),
    )
    type: DiscrepancyType = Field(..., description="Type of discrepancy")
    expected: float | None = Field(default=None, description="Expected value (from PO)")
    actual: float | None = Field(
        default=None, description="Actual value (from document)"
    )
    message: str = Field(..., description="Human-readable description")


class VerifyOrderDocumentRequest(BaseModel):
    """Request to verify a document against a purchase order."""

    model_config = ConfigDict(extra="forbid")

    order_id: int = Field(..., description="Purchase order ID")
    document_items: list[DocumentItem] = Field(
        ..., description="Items from the document to verify", min_length=1
    )


class VerifyOrderDocumentResponse(BaseModel):
    """Response from verifying an order document.

    Successful responses include the full ``purchase_order`` in the same
    exhaustive shape as ``get_purchase_order`` so callers don't need a
    follow-up lookup to see what was compared against. The field is typed
    ``Optional`` only because the model is constructed before the PO
    payload is assigned during ``_verify_order_document_impl``; in
    practice consumers only observe successful responses (errors on the
    PO fetch propagate as exceptions), so ``purchase_order`` is present
    on every response a caller receives.
    """

    order_id: int
    purchase_order: GetPurchaseOrderResponse | None = None
    matches: list[MatchResult] = Field(
        default_factory=list,
        description="Line items where the document agrees with the PO.",
    )
    discrepancies: list[Discrepancy] = Field(
        default_factory=list,
        description="Differences detected between the document and the PO.",
    )
    suggested_actions: list[str] = Field(
        default_factory=list,
        description="Recommended follow-up tool calls to resolve discrepancies.",
    )
    overall_status: str = Field(..., description="match, partial_match, or no_match")
    message: str


def _verify_response_to_tool_result(
    response: VerifyOrderDocumentResponse,
) -> ToolResult:
    """Convert VerifyOrderDocumentResponse to ToolResult.

    content carries the raw response as JSON for the LLM (no UI tree noise);
    structured_content carries the Prefab envelope rendered in the iframe on
    UI-capable hosts (per MCP Apps spec, #422).
    """
    from katana_mcp.tools.prefab_ui import build_verification_ui

    ui = build_verification_ui(response.model_dump())
    return ToolResult(
        content=response.model_dump_json(),
        structured_content=ui,
    )


async def _verify_order_document_impl(
    request: VerifyOrderDocumentRequest, context: Context
) -> VerifyOrderDocumentResponse:
    """Implementation of verify_order_document tool.

    Args:
        request: Request with order ID and document items
        context: Server context with KatanaClient

    Returns:
        Verification response with matches and discrepancies

    Raises:
        Exception: If API call fails
    """
    logger.info(
        f"Verifying document with {len(request.document_items)} items against PO {request.order_id}"
    )

    try:
        services = get_services(context)

        # Fetch the PO to get its details
        from katana_public_api_client.api.purchase_order import (
            get_purchase_order as api_get_purchase_order,
        )

        po_response = await api_get_purchase_order.asyncio_detailed(
            id=request.order_id, client=services.client
        )

        # unwrap_as() raises typed exceptions on error, returns typed RegularPurchaseOrder
        po = unwrap_as(po_response, RegularPurchaseOrder)

        # Build the exhaustive PO structured view — same shape as
        # get_purchase_order — so callers have full context on what was
        # compared against. Side-data fetches run concurrently via gather
        # to avoid doubling latency on the verify path. ``variants_by_id``
        # is plumbed in below (built right after we have ``po_rows``) so
        # each row in the embedded ``purchase_order`` response carries the
        # canonical SKU + display_name from the same cache read the verify
        # path already does.
        default_group_id = unwrap_unset(po.default_group_id, None)
        additional_cost_rows, accounting_metadata = await asyncio.gather(
            _fetch_po_additional_cost_rows(services, default_group_id),
            _fetch_po_accounting_metadata(services, po.id),
        )

        # Extract order number safely using unwrap_unset
        order_no = unwrap_unset(po.order_no, f"PO-{request.order_id}")

        # Get PO rows - use unwrap_unset for UNSET check
        po_rows_raw = unwrap_unset(po.purchase_order_rows, None)
        po_rows = po_rows_raw or []

        # Collect variant IDs and resolve SKU + canonical display_name in
        # one batched cache read instead of an API call per row. The typed
        # cache pre-computes ``CachedVariant.display_name`` via the variant
        # postprocess hook (same Katana-UI formula used by every other
        # surface — see ``build_variant_display_name``). API fallback covers
        # cold-cache gaps so a fresh install doesn't silently lose
        # verification rows. ``cached_variants`` also flows into
        # ``_build_get_purchase_order_response`` so the embedded
        # ``purchase_order`` response carries the same canonical names.
        from katana_mcp.tools.foundation.items import _fetch_variant_by_id
        from katana_public_api_client.domain.variant import (
            build_variant_display_name,
        )
        from katana_public_api_client.models_pydantic._generated import (
            CachedMaterial,
            CachedProduct,
            CachedVariant,
        )

        variant_ids: list[int] = [
            vid
            for vid in (unwrap_unset(row.variant_id, None) for row in po_rows)
            if vid is not None
        ]

        cached_variants: dict[
            int, Any
        ] = await services.typed_cache.catalog.get_many_by_ids(
            CachedVariant, set(variant_ids), include_deleted=True
        )

        # Cold-cache fallback: any variant_id not in the cache gets a
        # fresh API fetch. Dedup first (a PO can reference the same
        # variant on multiple rows) and fire all fetches in parallel —
        # the previous serial-await pattern added avoidable latency on
        # POs with many cache misses.
        missing_ids = list({vid for vid in variant_ids if vid not in cached_variants})
        if missing_ids:
            fallback_variants = await asyncio.gather(
                *(_fetch_variant_by_id(services, vid) for vid in missing_ids)
            )
            # API-fallback ``Variant`` attrs don't carry the
            # ``display_name`` field (the typed-cache postprocess
            # computes it during sync, but cold-cache paths skip that).
            # Bulk-resolve parents from the cache so each fallback can
            # get a canonical display_name via the same helper every
            # other surface uses — keeps verification rows readable
            # without re-fetching at render time.
            present_fallbacks = [v for v in fallback_variants if v is not None]
            parent_product_ids = {
                pid
                for v in present_fallbacks
                if (pid := unwrap_unset(getattr(v, "product_id", None), None))
            }
            parent_material_ids = {
                mid
                for v in present_fallbacks
                if (mid := unwrap_unset(getattr(v, "material_id", None), None))
            }
            products_by_id, materials_by_id = await asyncio.gather(
                services.typed_cache.catalog.get_many_by_ids(
                    CachedProduct,
                    parent_product_ids,
                    include_archived=True,
                    include_deleted=True,
                ),
                services.typed_cache.catalog.get_many_by_ids(
                    CachedMaterial,
                    parent_material_ids,
                    include_archived=True,
                    include_deleted=True,
                ),
            )
            for vid, fallback in zip(missing_ids, fallback_variants, strict=True):
                if fallback is None:
                    continue
                pid = unwrap_unset(getattr(fallback, "product_id", None), None)
                mid = unwrap_unset(getattr(fallback, "material_id", None), None)
                parent = None
                if pid is not None:
                    parent = products_by_id.get(pid)
                elif mid is not None:
                    parent = materials_by_id.get(mid)
                parent_name = (
                    getattr(parent, "name", None) if parent is not None else None
                )
                sku_value = unwrap_unset(getattr(fallback, "sku", None), None)
                config_attrs = unwrap_unset(
                    getattr(fallback, "config_attributes", None), []
                )
                display_name = build_variant_display_name(
                    parent_name, config_attrs, sku_value
                )
                # Normalize to a dict so ``_sku_of`` / ``_display_name_of``
                # below read uniformly — they already key off the
                # ``isinstance(v, dict)`` branch for the cache-miss case.
                cached_variants[vid] = {
                    "sku": sku_value,
                    "display_name": display_name,
                    "product_id": pid,
                    "material_id": mid,
                }

        exhaustive_po = _build_get_purchase_order_response(
            po,
            additional_cost_rows=additional_cost_rows,
            accounting_metadata=accounting_metadata,
            variants_by_id=cached_variants,
        )

        if not po_rows_raw:
            return VerifyOrderDocumentResponse(
                order_id=request.order_id,
                purchase_order=exhaustive_po,
                matches=[],
                discrepancies=[],
                suggested_actions=["Verify purchase order data in Katana"],
                overall_status="no_match",
                message=f"Purchase order {order_no} has no line items",
            )

        def _sku_of(v: Any) -> str | None:
            if v is None:
                return None
            if isinstance(v, dict):
                return v.get("sku")
            return getattr(v, "sku", None)

        def _display_name_of(v: Any) -> str | None:
            if v is None:
                return None
            if isinstance(v, dict):
                return v.get("display_name")
            return getattr(v, "display_name", None)

        # Build a map of SKU -> (PO row, display_name) for matching. The
        # display_name is cached alongside the row so each MatchResult /
        # Discrepancy can surface the canonical name without re-resolving.
        sku_to_row: dict[str, tuple[Any, str]] = {}
        for row in po_rows:
            variant_id = unwrap_unset(row.variant_id, None)
            if variant_id is None:
                continue
            variant = cached_variants.get(variant_id)
            sku = _sku_of(variant)
            if sku:
                sku_to_row[sku] = (row, _display_name_of(variant) or "")

        # Now match document items to PO rows
        matches: list[MatchResult] = []
        discrepancies: list[Discrepancy] = []

        for doc_item in request.document_items:
            # Check if SKU exists in PO
            if doc_item.sku not in sku_to_row:
                discrepancies.append(
                    Discrepancy(
                        sku=doc_item.sku,
                        # MISSING_IN_PO has no variant to resolve against
                        # — leave display_name empty (the model default).
                        type=DiscrepancyType.MISSING_IN_PO,
                        expected=None,
                        actual=doc_item.quantity,
                        message=f"SKU {doc_item.sku}: Not found in purchase order {order_no}",
                    )
                )
                continue

            row, display_name = sku_to_row[doc_item.sku]
            # PO row's ``quantity`` / ``price_per_unit`` are optional in the
            # OpenAPI schema (``Unset`` in the generated model). Preserve
            # ``None`` rather than coercing missing-to-zero — propagating
            # ``0.0`` would (1) silently misrepresent "unknown" as zero in
            # the new ``expected_*`` response fields the card renders, and
            # (2) generate false QUANTITY_MISMATCH discrepancies against
            # non-zero document quantities. Comparisons skip when the PO
            # side is missing, mirroring how the doc-side price check skips
            # when ``doc_item.unit_price is None``.
            row_qty: float | None = unwrap_unset(row.quantity, None)
            row_price: float | None = unwrap_unset(row.price_per_unit, None)

            # Track match status and discrepancies
            has_qty_mismatch = False
            has_price_mismatch = False

            # Check quantity match — skip when PO row has no quantity.
            if (
                row_qty is not None and abs(doc_item.quantity - row_qty) > 0.01
            ):  # Small tolerance for float comparison
                has_qty_mismatch = True
                discrepancies.append(
                    Discrepancy(
                        sku=doc_item.sku,
                        display_name=display_name,
                        type=DiscrepancyType.QUANTITY_MISMATCH,
                        expected=row_qty,
                        actual=doc_item.quantity,
                        message=f"SKU {doc_item.sku}: Quantity mismatch (Document: {doc_item.quantity}, PO: {row_qty})",
                    )
                )

            # Check price match — skip when either side is missing.
            if (
                doc_item.unit_price is not None
                and row_price is not None
                and abs(doc_item.unit_price - row_price) > 0.01
            ):
                has_price_mismatch = True
                discrepancies.append(
                    Discrepancy(
                        sku=doc_item.sku,
                        display_name=display_name,
                        type=DiscrepancyType.PRICE_MISMATCH,
                        expected=row_price,
                        actual=doc_item.unit_price,
                        message=f"SKU {doc_item.sku}: Price mismatch (Document: {doc_item.unit_price}, PO: {row_price})",
                    )
                )

            # Determine match status
            if has_qty_mismatch and has_price_mismatch:
                status = "both_diff"
            elif has_qty_mismatch:
                status = "quantity_diff"
            elif has_price_mismatch:
                status = "price_diff"
            else:
                status = "perfect"

            # Create match result. ``quantity`` / ``unit_price`` are the
            # document-side values; ``expected_quantity`` /
            # ``expected_unit_price`` are the PO-side values from the matched
            # row. The card renders these as side-by-side columns so the
            # operator sees the delta without re-resolving against the
            # embedded purchase_order (#554).
            matches.append(
                MatchResult(
                    sku=doc_item.sku,
                    display_name=display_name,
                    quantity=doc_item.quantity,
                    unit_price=doc_item.unit_price,
                    expected_quantity=row_qty,
                    expected_unit_price=row_price,
                    status=status,
                )
            )

        # Determine overall status
        if len(matches) == 0:
            overall_status = "no_match"
        elif len(discrepancies) == 0:
            overall_status = "match"
        else:
            overall_status = "partial_match"

        # Build suggested actions
        suggested_actions = []
        if discrepancies:
            suggested_actions.append("Review discrepancies before receiving")
            suggested_actions.append(
                "Contact supplier if quantities or prices don't match"
            )
        else:
            suggested_actions.append(
                "All items verified successfully - proceed with receiving"
            )

        message = (
            f"Verified {len(request.document_items)} items: {len(matches)} matches, "
            f"{len(discrepancies)} discrepancies"
        )

        return VerifyOrderDocumentResponse(
            order_id=request.order_id,
            purchase_order=exhaustive_po,
            matches=matches,
            discrepancies=discrepancies,
            suggested_actions=suggested_actions,
            overall_status=overall_status,
            message=message,
        )

    except Exception as e:
        logger.error(f"Failed to verify order document: {e}")
        raise


@observe_tool
@unpack_pydantic_params
async def verify_order_document(
    request: Annotated[VerifyOrderDocumentRequest, Unpack()], context: Context
) -> ToolResult:
    """Verify a supplier document (invoice, packing slip) against a purchase order.

    Read-only check: compares SKUs, quantities, and prices from the document against
    the PO and reports matches and discrepancies. Use this BEFORE receive_purchase_order
    to validate a delivery. No changes are made to orders or inventory.
    """
    response = await _verify_order_document_impl(request, context)
    return _verify_response_to_tool_result(response)


# ============================================================================
# Tool: list_purchase_orders (list-tool pattern v2)
# ============================================================================


class ListPurchaseOrdersRequest(BaseModel):
    """Request to list/filter purchase orders (list-tool pattern v2)."""

    model_config = ConfigDict(extra="forbid")

    # Paging
    limit: int = Field(
        default=50,
        ge=1,
        le=250,
        description=(
            "Max rows to return (default 50, min 1, max 250). When `page` "
            "is set, acts as the page size for that request."
        ),
    )
    page: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Page number (1-based). When set, the response includes "
            "`pagination` metadata (total_records, total_pages) computed "
            "via SQL COUNT against the same filter predicate."
        ),
    )

    # Domain filters
    ids: CoercedIntListOpt = Field(
        default=None,
        description=(
            "Filter by explicit list of purchase order IDs. "
            "JSON array of integers, e.g. [101, 202, 303]."
        ),
    )
    order_no: str | None = Field(default=None, description="Filter by exact order_no")
    entity_type: PurchaseOrderEntityType | None = Field(
        default=None,
        description=(
            "Filter by entity_type: 'regular' (materials) or 'outsourced' "
            "(subcontracted)."
        ),
    )
    status: FindPurchaseOrdersStatus | None = Field(
        default=None,
        description=(
            "Filter by PO status: DRAFT, NOT_RECEIVED, PARTIALLY_RECEIVED, RECEIVED."
        ),
    )
    billing_status: FindPurchaseOrdersBillingStatus | None = Field(
        default=None,
        description="Filter by billing status: BILLED, NOT_BILLED, PARTIALLY_BILLED.",
    )
    currency: str | None = Field(
        default=None, description="Filter by currency code (e.g. 'USD')"
    )
    location_id: int | None = Field(
        default=None,
        description=("Filter by receiving location ID. Look up via `list_locations`."),
    )
    tracking_location_id: int | None = Field(
        default=None,
        description=(
            "Filter by tracking location ID (outsourced POs). The cache "
            "stores this as a hoisted column on every row; regular POs "
            "match only when ``None`` is filtered, which doesn't apply "
            "here — pair with ``entity_type='outsourced'`` to scope. "
            "Look up via `list_locations`."
        ),
    )
    supplier_id: int | None = Field(
        default=None,
        description=("Filter by supplier ID. Look up via `list_suppliers`."),
    )
    include_deleted: bool | None = Field(
        default=None, description="When true, include soft-deleted purchase orders."
    )

    # Time-window filters (all run as indexed SQL date-range queries)
    created_after: str | None = Field(
        default=None, description="ISO-8601 datetime lower bound on created_at."
    )
    created_before: str | None = Field(
        default=None, description="ISO-8601 datetime upper bound on created_at."
    )
    updated_after: str | None = Field(
        default=None, description="ISO-8601 datetime lower bound on updated_at."
    )
    updated_before: str | None = Field(
        default=None, description="ISO-8601 datetime upper bound on updated_at."
    )
    expected_arrival_after: str | None = Field(
        default=None,
        description=(
            "ISO-8601 datetime lower bound on expected_arrival_date — "
            "indexed SQL range filter against the cache."
        ),
    )
    expected_arrival_before: str | None = Field(
        default=None,
        description=(
            "ISO-8601 datetime upper bound on expected_arrival_date — "
            "indexed SQL range filter against the cache."
        ),
    )

    # Row inclusion
    include_rows: bool = Field(
        default=False,
        description=(
            "When true, populate row-level detail (variant_id, quantity, "
            "price, arrival date) on each summary."
        ),
    )


class PurchaseOrderRowSummary(BaseModel):
    """Summary of a purchase order line item (used when include_rows=True)."""

    id: int | None = None
    variant_id: int | None = None
    sku: str | None = None
    """SKU from the variant, populated when the typed cache resolves the
    row's ``variant_id``. ``None`` on cache miss — matches the convention
    used by ``SalesOrderRowInfo``.
    """
    display_name: str | None = None
    """Katana-UI-format human-readable name. Like ``sku``, lifted from
    the typed cache when the row's variant is present. ``None`` on cache
    miss. The list-tool path uses ``ensure_purchase_orders_synced`` so
    these are typically populated in steady state; cold-cache callers may
    see ``None`` until the next variant sync runs.
    """
    quantity: float | None = None
    price_per_unit: float | None = None
    arrival_date: str | None = None
    received_date: str | None = None
    total: float | None = None


class PurchaseOrderSummary(BaseModel):
    """Summary row for a purchase order in a list."""

    id: int
    order_no: str | None
    status: str | None
    billing_status: str | None
    entity_type: str | None
    supplier_id: int | None
    location_id: int | None
    currency: str | None
    created_date: str | None
    expected_arrival_date: str | None
    total: float | None
    row_count: int
    rows: list[PurchaseOrderRowSummary] | None = None
    katana_url: str | None = None


class ListPurchaseOrdersResponse(BaseModel):
    """Response containing a list of purchase orders."""

    orders: list[PurchaseOrderSummary]
    total_count: int
    pagination: PaginationMeta | None = None


_PURCHASE_ORDER_DATE_FIELDS = (
    "created_after",
    "created_before",
    "updated_after",
    "updated_before",
    "expected_arrival_after",
    "expected_arrival_before",
)


def _apply_purchase_order_filters(
    stmt: Any,
    request: ListPurchaseOrdersRequest,
    parsed_dates: dict[str, datetime | None],
) -> Any:
    """Translate request filters into WHERE clauses on a CachedPurchaseOrder query.

    Shared by the data SELECT and the COUNT SELECT so pagination totals
    reflect exactly the same filter set as the data rows.
    """

    from katana_public_api_client.models_pydantic._generated import (
        CachedPurchaseOrder,
        PurchaseOrderBillingStatus,
        PurchaseOrderEntityType,
        PurchaseOrderStatus,
    )

    if request.ids is not None:
        stmt = stmt.where(CachedPurchaseOrder.id.in_(request.ids))
    if request.order_no is not None:
        stmt = stmt.where(CachedPurchaseOrder.order_no == request.order_no)
    if request.entity_type is not None:
        stmt = stmt.where(
            CachedPurchaseOrder.entity_type
            == coerce_enum(request.entity_type, PurchaseOrderEntityType, "entity_type")
        )
    if request.status is not None:
        stmt = stmt.where(
            CachedPurchaseOrder.status
            == coerce_enum(request.status, PurchaseOrderStatus, "status")
        )
    if request.billing_status is not None:
        stmt = stmt.where(
            CachedPurchaseOrder.billing_status
            == coerce_enum(
                request.billing_status, PurchaseOrderBillingStatus, "billing_status"
            )
        )
    if request.currency is not None:
        stmt = stmt.where(CachedPurchaseOrder.currency == request.currency)
    if request.location_id is not None:
        stmt = stmt.where(CachedPurchaseOrder.location_id == request.location_id)
    if request.tracking_location_id is not None:
        # Cache-only column hoisted from OutsourcedPurchaseOrder; regular
        # POs always carry None here, so this filter implies outsourced.
        stmt = stmt.where(
            CachedPurchaseOrder.tracking_location_id == request.tracking_location_id
        )
    if request.supplier_id is not None:
        stmt = stmt.where(CachedPurchaseOrder.supplier_id == request.supplier_id)
    if not request.include_deleted:
        stmt = stmt.where(CachedPurchaseOrder.deleted_at.is_(None))

    return apply_date_window_filters(
        stmt,
        parsed_dates,
        ge_pairs={
            "created_after": CachedPurchaseOrder.created_at,
            "updated_after": CachedPurchaseOrder.updated_at,
            "expected_arrival_after": CachedPurchaseOrder.expected_arrival_date,
        },
        le_pairs={
            "created_before": CachedPurchaseOrder.created_at,
            "updated_before": CachedPurchaseOrder.updated_at,
            "expected_arrival_before": CachedPurchaseOrder.expected_arrival_date,
        },
    )


async def _list_purchase_orders_impl(
    request: ListPurchaseOrdersRequest, context: Context
) -> ListPurchaseOrdersResponse:
    """List purchase orders with filters via the typed cache.

    ``ensure_purchase_orders_synced`` runs an incremental
    ``updated_at_min`` delta (debounced — see :data:`_SYNC_DEBOUNCE`).
    Filters (including ``expected_arrival_date`` and the hoisted
    outsourced-only ``tracking_location_id``) translate to indexed SQL.
    See ADR-0018.
    """
    from sqlalchemy.orm import selectinload
    from sqlmodel import func, select

    from katana_mcp.typed_cache import ensure_purchase_orders_synced
    from katana_public_api_client.models_pydantic._generated import (
        CachedPurchaseOrder,
        CachedPurchaseOrderRow,
    )

    services = get_services(context)

    await ensure_purchase_orders_synced(services.client, services.typed_cache)

    parsed_dates = parse_request_dates(request, _PURCHASE_ORDER_DATE_FIELDS)

    # When ``include_rows`` is set, ``selectinload`` eager-loads the
    # children, so ``len(po.purchase_order_rows)`` is free at materialization
    # time and we skip the correlated COUNT subquery. Both paths filter
    # ``deleted_at IS NULL`` so soft-deleted rows never surface (see #803).
    if request.include_rows:
        stmt = select(CachedPurchaseOrder).options(
            selectinload(
                CachedPurchaseOrder.purchase_order_rows.and_(
                    CachedPurchaseOrderRow.deleted_at.is_(None)
                )
            )
        )
    else:
        row_count_subq = (
            select(func.count(CachedPurchaseOrderRow.id))
            .where(CachedPurchaseOrderRow.purchase_order_id == CachedPurchaseOrder.id)
            .where(CachedPurchaseOrderRow.deleted_at.is_(None))
            .correlate(CachedPurchaseOrder)
            .scalar_subquery()
            .label("row_count")
        )
        stmt = select(CachedPurchaseOrder, row_count_subq)
    stmt = _apply_purchase_order_filters(stmt, request, parsed_dates)
    stmt = stmt.order_by(
        CachedPurchaseOrder.created_at.desc(),
        CachedPurchaseOrder.id.desc(),
    )
    if request.page is not None:
        stmt = stmt.offset((request.page - 1) * request.limit).limit(request.limit)
    else:
        stmt = stmt.limit(request.limit)

    async with services.typed_cache.session() as session:
        data_result = await session.exec(stmt)
        if request.include_rows:
            cached_orders = list(data_result.all())
            orders_with_counts: list[tuple[CachedPurchaseOrder, int]] = [
                (po, len(po.purchase_order_rows)) for po in cached_orders
            ]
        else:
            orders_with_counts = data_result.all()

        pagination: PaginationMeta | None = None
        if request.page is not None:
            count_stmt = _apply_purchase_order_filters(
                select(func.count()).select_from(CachedPurchaseOrder),
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

    # When ``include_rows`` is set, collect every row's variant_id and do
    # one batched cache read to lift SKU + canonical display_name onto each
    # row summary. Adds one extra IN-clause read regardless of result-set
    # size — much cheaper than the per-row API fallback the get path uses
    # (the list path explicitly stays cache-only by design to keep the
    # ``ensure_purchase_orders_synced`` + single-query win intact).
    variant_lookup: dict[int, Any] = {}
    if request.include_rows:
        from katana_public_api_client.models_pydantic._generated import CachedVariant

        variant_ids = {
            r.variant_id
            for po, _ in orders_with_counts
            for r in po.purchase_order_rows
            if r.variant_id is not None
        }
        if variant_ids:
            variant_lookup = await services.typed_cache.catalog.get_many_by_ids(
                CachedVariant, variant_ids, include_deleted=True
            )

    def _row_attr(v: Any, name: str) -> Any:
        if v is None:
            return None
        if isinstance(v, dict):
            return v.get(name)
        return getattr(v, name, None)

    def _variant_for_row(row: Any) -> Any:
        # Guard ``None`` lookups so the dict-get type stays narrow and
        # ``CachedVariant`` rows without a variant_id don't silently shadow
        # the empty-map default.
        vid = row.variant_id
        return variant_lookup.get(vid) if vid is not None else None

    summaries: list[PurchaseOrderSummary] = []
    for po, row_count in orders_with_counts:
        rows: list[PurchaseOrderRowSummary] | None = None
        if request.include_rows:
            rows = [
                PurchaseOrderRowSummary(
                    id=r.id,
                    variant_id=r.variant_id,
                    sku=_row_attr(_variant_for_row(r), "sku"),
                    display_name=_row_attr(_variant_for_row(r), "display_name"),
                    quantity=r.quantity,
                    price_per_unit=r.price_per_unit,
                    arrival_date=iso_or_none(r.arrival_date),
                    received_date=iso_or_none(r.received_date),
                    total=r.total,
                )
                for r in po.purchase_order_rows
            ]
        summaries.append(
            PurchaseOrderSummary(
                id=po.id,
                order_no=po.order_no,
                status=enum_to_str(po.status),
                billing_status=enum_to_str(po.billing_status),
                entity_type=enum_to_str(po.entity_type),
                supplier_id=po.supplier_id,
                location_id=po.location_id,
                currency=po.currency,
                created_date=iso_or_none(po.order_created_date),
                expected_arrival_date=iso_or_none(po.expected_arrival_date),
                total=po.total,
                row_count=row_count,
                rows=rows,
                katana_url=katana_web_url("purchase_order", po.id),
            )
        )

    return ListPurchaseOrdersResponse(
        orders=summaries, total_count=len(summaries), pagination=pagination
    )


@observe_tool
@unpack_pydantic_params
async def list_purchase_orders(
    request: Annotated[ListPurchaseOrdersRequest, Unpack()], context: Context
) -> ToolResult:
    """List purchase orders with filters — pass `ids=[1,2,3]` to fetch a specific batch by ID (cache-backed).

    Use this for discovery workflows — find POs by supplier, status, location,
    or within a date window. Returns summary info (order_no, status, supplier,
    total, expected arrival, row_count).

    **Common filters:**
    - `status="NOT_RECEIVED"` — open POs awaiting delivery
    - `supplier_id=N` — POs for a specific supplier
    - `billing_status="NOT_BILLED"` — unbilled POs
    - `entity_type="outsourced"` — outsourced POs only
    - `tracking_location_id=N` — outsourced POs at a tracking location

    **Time windows** (all run as indexed SQL date-range queries):
    - `created_after` / `created_before` — bounds on `created_at`
    - `updated_after` / `updated_before` — bounds on `updated_at`
    - `expected_arrival_after` / `expected_arrival_before` — bounds on
      `expected_arrival_date` (was a client-side post-fetch filter
      pre-cache; now indexed SQL)

    **Paging:**
    - `limit` caps the number of rows (default 50, min 1).
    - `page=N` returns a single page; the response includes `pagination`
      metadata (total_records, total_pages, first/last flags) computed
      via SQL COUNT against the same filter predicate.

    Pass `include_rows=True` to populate per-PO line item details.
    For full details on a specific PO, use `get_purchase_order`.
    """
    response = await _list_purchase_orders_impl(request, context)
    return make_json_result(response)


# ============================================================================
# Tool: modify_purchase_order — unified modification surface
# ============================================================================


class POOperation(StrEnum):
    """Operation names that ``modify_purchase_order`` /
    ``delete_purchase_order`` plan builders emit on their ActionSpecs.

    Used as the ``operation`` field on each :class:`ActionResult` in the
    response — values are the canonical strings the rendering layer and
    LLM consumers see.
    """

    UPDATE_HEADER = "update_header"
    DELETE = "delete"
    ADD_ROW = "add_row"
    UPDATE_ROW = "update_row"
    DELETE_ROW = "delete_row"
    ADD_ADDITIONAL_COST = "add_additional_cost"
    UPDATE_ADDITIONAL_COST = "update_additional_cost"
    DELETE_ADDITIONAL_COST = "delete_additional_cost"
    # Receipt-replay step emitted by ``correct_purchase_order`` — POSTs
    # one ``PurchaseOrderReceiveRow`` batch to ``/purchase_order_receive``
    # to restore the captured close-state after edits land. Distinct from
    # ``UPDATE_HEADER`` so the replay step is identifiable in
    # ``ActionResult`` lists.
    RECEIVE = "receive"


# Tool-facing uppercase status literal — values match the API StrEnum's
# ``.value`` directly, so ``PurchaseOrderStatus(literal)`` resolves the
# enum without a lookup table.
PurchaseOrderStatusLiteral = Literal[
    "DRAFT", "NOT_RECEIVED", "PARTIALLY_RECEIVED", "RECEIVED"
]
CostDistributionMethodLiteral = Literal["BY_VALUE", "NON_DISTRIBUTED"]


async def _fetch_purchase_order_attrs(
    services: Any, po_id: int
) -> RegularPurchaseOrder | None:
    """Fetch the PO for diff context. Returns None on failure."""
    return await safe_fetch_for_diff(
        api_get_purchase_order,
        services,
        po_id,
        return_type=RegularPurchaseOrder,
        label="PO",
    )


async def _fetch_purchase_order_row(
    services: Any, row_id: int
) -> PurchaseOrderRow | None:
    """Fetch a PO row for diff context. Returns None on failure."""
    return await safe_fetch_for_diff(
        api_get_purchase_order_row,
        services,
        row_id,
        return_type=PurchaseOrderRow,
        label="PO row",
    )


async def _fetch_po_row_attrs_for_merge(
    services: Any, purchase_order_id: int
) -> list[Any]:
    """Return raw attrs ``PurchaseOrderRow`` list for the cache merge fan-out.

    The PO parent fetch (PATCH or GET /purchase_orders/{id}) returns
    rows embedded in ``purchase_order_rows`` — but Katana hides
    soft-deleted rows from that nested view even with
    ``include_deleted=true`` at the parent level (the flag only affects
    top-level inclusion). The sibling endpoint ``/purchase_order_rows``
    exposes ``include_deleted`` for its own scope, so the typed-cache
    schema syncs rows independently to catch tombstones. Mirror that
    here for post-apply merge: a ``delete_row_id`` action would
    otherwise land at Katana but leave the cached row as a ghost until
    the next watermark sync.
    """
    from katana_public_api_client.api.purchase_order_row import (
        get_all_purchase_order_rows,
    )
    from katana_public_api_client.utils import unwrap_data

    response = await get_all_purchase_order_rows.asyncio_detailed(
        client=services.client,
        purchase_order_id=purchase_order_id,
        include_deleted=True,
        limit=250,
    )
    return unwrap_data(response, default=[])


async def _fetch_po_additional_cost_row(
    services: Any, row_id: int
) -> PurchaseOrderAdditionalCostRow | None:
    """Fetch a PO additional-cost row for diff context. Returns None on failure."""
    return await safe_fetch_for_diff(
        api_get_po_additional_cost_row,
        services,
        row_id,
        return_type=PurchaseOrderAdditionalCostRow,
        label="additional-cost row",
    )


# ----------------------------------------------------------------------------
# Sub-payload models
# ----------------------------------------------------------------------------


class POHeaderPatch(BaseModel):
    """Optional fields to patch on the PO header. Status is included here —
    Katana's PATCH /purchase_orders/{id} accepts it as a regular field, so
    no separate status sub-payload is needed."""

    model_config = ConfigDict(extra="forbid")

    order_no: str | None = Field(default=None, description="New PO number")
    supplier_id: int | None = Field(
        default=None,
        description=("New supplier ID. Look up via `list_suppliers`."),
    )
    currency: str | None = Field(default=None, description="New currency code")
    location_id: int | None = Field(
        default=None,
        description=("New receiving location ID. Look up via `list_locations`."),
    )
    tracking_location_id: int | None = Field(
        default=None,
        description=("New tracking location ID. Look up via `list_locations`."),
    )
    status: PurchaseOrderStatusLiteral | None = Field(
        default=None,
        description=(
            "New status — DRAFT / NOT_RECEIVED / PARTIALLY_RECEIVED / RECEIVED. "
            "Use receive_purchase_order to flip to RECEIVED with inventory updates."
        ),
    )
    expected_arrival_date: WireDatetime | None = Field(
        default=None,
        description=(
            "New expected arrival date — ISO 8601 date or datetime "
            "(e.g. '2026-05-08T14:30:00Z' or '2026-05-08T14:30:00-08:00'). "
            "Naive datetimes (no timezone) are interpreted as UTC. "
            "WARNING: Katana cascades this header value server-side onto the "
            "row-level `arrival_date` of line items. If you need specific "
            "rows to keep different dates, include them in `update_rows` in "
            "the SAME modify_purchase_order call. Conversely, updating a "
            "single row's `arrival_date` bumps the header to the latest row "
            "date if applicable, but does not affect other rows."
        ),
    )
    order_created_date: WireDatetime | None = Field(
        default=None,
        description=(
            "New order created date — ISO 8601 date or datetime "
            "(e.g. '2026-05-08T14:30:00Z' or '2026-05-08T14:30:00-08:00'). "
            "Naive datetimes (no timezone) are interpreted as UTC."
        ),
    )
    additional_info: str | None = Field(
        default=None, description="New notes / additional info"
    )


class PORowAdd(BaseModel):
    """A new line item to add to the PO."""

    model_config = ConfigDict(extra="forbid")

    variant_id: int = Field(..., description="Variant ID")
    quantity: float = Field(..., description="Quantity", gt=0)
    price_per_unit: float = Field(..., description="Unit price")
    tax_rate_id: int | None = Field(
        default=None,
        description=("Tax rate ID. Look up via `list_tax_rates`."),
    )
    tax_name: str | None = Field(default=None, description="Tax name")
    tax_rate: str | None = Field(default=None, description="Tax rate value")
    currency: str | None = Field(default=None, description="Currency code")
    purchase_uom: str | None = Field(default=None, description="Purchase UOM")
    purchase_uom_conversion_rate: float | None = Field(
        default=None, description="UOM conversion rate"
    )
    arrival_date: WireDatetime | None = Field(
        default=None,
        description=(
            "Expected arrival date for this row — ISO 8601 date or datetime "
            "(e.g. '2026-05-08T14:30:00Z' or '2026-05-08T14:30:00-08:00'). "
            "Naive datetimes (no timezone) are interpreted as UTC."
        ),
    )


class PORowUpdate(BaseModel):
    """Patch to an existing PO row. Carries the row id plus optional fields."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Row ID to update")
    quantity: float | None = Field(default=None, description="New quantity", gt=0)
    variant_id: int | None = Field(default=None, description="New variant ID")
    tax_rate_id: int | None = Field(
        default=None,
        description=("New tax rate ID. Look up via `list_tax_rates`."),
    )
    tax_name: str | None = Field(default=None, description="New tax name")
    tax_rate: str | None = Field(default=None, description="New tax rate value")
    price_per_unit: float | None = Field(default=None, description="New unit price")
    purchase_uom_conversion_rate: float | None = Field(
        default=None, description="New UOM conversion rate"
    )
    purchase_uom: str | None = Field(default=None, description="New purchase UOM")
    received_date: WireDatetime | None = Field(
        default=None,
        description=(
            "New received date — ISO 8601 date or datetime "
            "(e.g. '2026-05-08T14:30:00Z' or '2026-05-08T14:30:00-08:00'). "
            "Naive datetimes (no timezone) are interpreted as UTC."
        ),
    )
    arrival_date: WireDatetime | None = Field(
        default=None,
        description=(
            "New row-level arrival date — ISO 8601 date or datetime "
            "(e.g. '2026-05-08T14:30:00Z' or '2026-05-08T14:30:00-08:00'). "
            "Naive datetimes (no timezone) are interpreted as UTC."
        ),
    )


class POAdditionalCostAdd(BaseModel):
    """A new additional-cost row (freight, duties, handling fees).

    Either ``group_id`` or ``purchase_order_id`` (carried at the top-level
    request) is needed; if neither is set on the row, the dispatcher
    resolves the parent PO's ``default_group_id`` automatically.
    """

    model_config = ConfigDict(extra="forbid")

    additional_cost_id: int = Field(
        ...,
        description=(
            "Additional-cost catalog entry ID. Look up via `list_additional_costs`."
        ),
    )
    tax_rate_id: int = Field(
        ...,
        description=("Tax rate ID. Look up via `list_tax_rates`."),
    )
    price: float = Field(..., description="Cost amount")
    distribution_method: CostDistributionMethodLiteral | None = Field(
        default=None,
        description="Cost allocation method (BY_VALUE / NON_DISTRIBUTED)",
    )
    group_id: int | None = Field(
        default=None,
        description=(
            "Cost group ID. When omitted, the dispatcher resolves the parent "
            "PO's ``default_group_id``."
        ),
    )


class POAdditionalCostUpdate(BaseModel):
    """Patch to an existing additional-cost row."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Cost row ID to update")
    additional_cost_id: int | None = Field(
        default=None,
        description=("New catalog entry ID. Look up via `list_additional_costs`."),
    )
    tax_rate_id: int | None = Field(
        default=None,
        description=("New tax rate ID. Look up via `list_tax_rates`."),
    )
    price: float | None = Field(default=None, description="New price")
    distribution_method: CostDistributionMethodLiteral | None = Field(
        default=None, description="New distribution method"
    )


class ModifyPurchaseOrderRequest(ConfirmableRequest):
    """Unified modification request for a purchase order (non-destructive).

    Each sub-payload slot maps to one or more API operations on the PO or
    its sub-resources. Multiple slots can be combined in a single call —
    actions execute sequentially in canonical order (header → row adds →
    row updates → row deletes → cost adds → cost updates → cost deletes).
    Fail-fast on first error; the response carries per-action result blocks
    plus a ``prior_state`` snapshot for manual revert.

    Some fields on PO rows are derived (e.g. ``landed_cost``,
    ``total_in_base_currency``) — Katana computes them server-side and
    rejects them on update. Set those values indirectly via
    ``add_additional_costs`` (group-level distribution with ``BY_VALUE``).
    See ``katana://help/tools`` for the full list of derived fields.

    To remove a PO entirely, use the sibling ``delete_purchase_order`` tool.
    """

    id: int = Field(..., description="Purchase order ID")
    update_header: POHeaderPatch | None = Field(
        default=None,
        description=(
            "Header-level patch. Fields: order_no, supplier_id, currency, "
            "location_id, tracking_location_id, status (DRAFT/NOT_RECEIVED/"
            "PARTIALLY_RECEIVED/RECEIVED), expected_arrival_date, "
            "order_created_date, additional_info. To flip status to RECEIVED "
            "with inventory updates, use the receive_purchase_order tool."
        ),
    )
    add_rows: list[PORowAdd] | None = Field(
        default=None,
        description=(
            "New line items. Each row: variant_id (int, required), quantity "
            "(float, required, >0), price_per_unit (float, required), "
            "tax_rate_id (int — see `list_tax_rates`), tax_name, tax_rate, "
            "currency, purchase_uom, purchase_uom_conversion_rate, "
            "arrival_date."
        ),
    )
    update_rows: list[PORowUpdate] | None = Field(
        default=None,
        description=(
            "Patches to existing line items. Each entry: id (int, required) + "
            "any subset of quantity, variant_id, tax_rate_id, tax_name, "
            "tax_rate, price_per_unit, purchase_uom, "
            "purchase_uom_conversion_rate, received_date, arrival_date. "
            "Derived fields (landed_cost, total_in_base_currency, etc.) are "
            "rejected — distribute landed cost via add_additional_costs."
        ),
    )
    delete_row_ids: list[int] | None = Field(
        default=None,
        description="Row IDs to delete from the PO.",
    )
    add_additional_costs: list[POAdditionalCostAdd] | None = Field(
        default=None,
        description=(
            "New additional-cost rows (freight, duties, handling). Each row: "
            "additional_cost_id (int, required — see `list_additional_costs`), "
            "tax_rate_id (int, required — see `list_tax_rates`), price "
            "(float, required), distribution_method (BY_VALUE | "
            "NON_DISTRIBUTED — controls how the cost spreads across line "
            "items), group_id (int, optional — defaults to the PO's "
            "default_group_id)."
        ),
    )
    update_additional_costs: list[POAdditionalCostUpdate] | None = Field(
        default=None,
        description=(
            "Patches to existing additional-cost rows. Each entry: id (int, "
            "required) + any subset of additional_cost_id, tax_rate_id, "
            "price, distribution_method."
        ),
    )
    delete_additional_cost_ids: list[int] | None = Field(
        default=None,
        description="Additional-cost row IDs to delete from the PO.",
    )


class DeletePurchaseOrderRequest(ConfirmableRequest):
    """Delete an entire purchase order. Destructive — the order is removed."""

    id: int = Field(..., description="Purchase order ID to delete")


# ----------------------------------------------------------------------------
# Plan builders — one per sub-payload kind
# ----------------------------------------------------------------------------


def _build_update_header_request(
    patch: POHeaderPatch,
    existing_po: RegularPurchaseOrder | None = None,
) -> APIUpdatePurchaseOrderRequest:
    """Build the PATCH body for ``PATCH /purchase_orders/{id}``.

    ``additional_info`` is echoed via :func:`patch_additional_info` so
    Katana's wipe-on-omit doesn't destroy PO notes during a header
    rename (see its docstring for the full workaround story).
    """
    kwargs = unset_dict(patch, transforms={"status": PurchaseOrderStatus})
    kwargs["additional_info"] = patch_additional_info(
        patch.additional_info,
        existing_po.additional_info if existing_po is not None else UNSET,
    )
    return APIUpdatePurchaseOrderRequest(**kwargs)


def _build_create_row_request(
    po_id: int, row: PORowAdd
) -> APICreatePurchaseOrderRowRequest:
    return APICreatePurchaseOrderRowRequest(purchase_order_id=po_id, **unset_dict(row))


def _build_update_row_request(
    patch: PORowUpdate,
) -> APIUpdatePurchaseOrderRowRequest:
    return APIUpdatePurchaseOrderRowRequest(**unset_dict(patch, exclude=("id",)))


def _build_create_cost_request(
    cost: POAdditionalCostAdd, group_id: int
) -> APICreatePOAdditionalCostRowRequest:
    # ``cost.group_id`` is dropped — the resolved ``group_id`` parameter
    # (from PO ``default_group_id`` or the user's row-level override) wins.
    return APICreatePOAdditionalCostRowRequest(
        group_id=group_id,
        **unset_dict(
            cost,
            exclude=("group_id",),
            transforms={"distribution_method": CostDistributionMethod},
        ),
    )


def _build_update_cost_request(
    patch: POAdditionalCostUpdate,
) -> APIUpdatePOAdditionalCostRowRequest:
    return APIUpdatePOAdditionalCostRowRequest(
        **unset_dict(
            patch,
            exclude=("id",),
            transforms={"distribution_method": CostDistributionMethod},
        )
    )


async def _modify_purchase_order_impl(
    request: ModifyPurchaseOrderRequest, context: Context
) -> ModificationResponse:
    """Build the action plan from the request's sub-payloads and either
    preview or execute based on ``preview``."""
    services = get_services(context)

    if not has_any_subpayload(request):
        raise ValueError(
            "At least one sub-payload must be set: update_header, add_rows, "
            "update_rows, delete_row_ids, add_additional_costs, "
            "update_additional_costs, or delete_additional_cost_ids. "
            "To remove the PO entirely, use delete_purchase_order."
        )

    existing_po = await _fetch_purchase_order_attrs(services, request.id)

    # Resolve default_group_id once for any add_additional_costs entries that
    # didn't supply group_id explicitly. Reads from the already-fetched PO so
    # we don't re-issue a GET.
    default_group_id = (
        unwrap_unset(existing_po.default_group_id, None)
        if existing_po is not None
        else None
    )

    def _enrich_cost(cost: POAdditionalCostAdd) -> APICreatePOAdditionalCostRowRequest:
        group_id = cost.group_id or default_group_id
        if group_id is None:
            raise ValueError(
                f"Cannot resolve group_id for additional-cost row "
                f"(additional_cost_id={cost.additional_cost_id}): no "
                f"default_group_id on PO {request.id} and none provided."
            )
        return _build_create_cost_request(cost, group_id)

    plan: list[ActionSpec] = []

    if request.update_header is not None:
        diff = compute_field_diff(
            existing_po, request.update_header, unknown_prior=existing_po is None
        )
        plan.append(
            ActionSpec(
                operation=POOperation.UPDATE_HEADER,
                target_id=request.id,
                diff=diff,
                apply=make_patch_apply(
                    api_update_purchase_order,
                    services,
                    request.id,
                    _build_update_header_request(request.update_header, existing_po),
                    return_type=RegularPurchaseOrder,
                ),
                verify=make_response_verifier(diff),
            )
        )

    plan.extend(
        plan_creates(
            request.add_rows,
            POOperation.ADD_ROW,
            lambda row: _build_create_row_request(request.id, row),
            lambda body: make_post_apply(
                api_create_purchase_order_row,
                services,
                body,
                return_type=PurchaseOrderRow,
            ),
        )
    )
    plan.extend(
        await plan_updates(
            request.update_rows,
            POOperation.UPDATE_ROW,
            lambda rid: _fetch_purchase_order_row(services, rid),
            _build_update_row_request,
            lambda rid, body: make_patch_apply(
                api_update_purchase_order_row,
                services,
                rid,
                body,
                return_type=PurchaseOrderRow,
            ),
        )
    )
    plan.extend(
        plan_deletes(
            request.delete_row_ids,
            POOperation.DELETE_ROW,
            lambda rid: make_delete_apply(api_delete_purchase_order_row, services, rid),
        )
    )
    plan.extend(
        plan_creates(
            request.add_additional_costs,
            POOperation.ADD_ADDITIONAL_COST,
            _enrich_cost,
            lambda body: make_post_apply(
                api_create_po_additional_cost_row,
                services,
                body,
                return_type=PurchaseOrderAdditionalCostRow,
            ),
        )
    )
    plan.extend(
        await plan_updates(
            request.update_additional_costs,
            POOperation.UPDATE_ADDITIONAL_COST,
            lambda rid: _fetch_po_additional_cost_row(services, rid),
            _build_update_cost_request,
            lambda rid, body: make_patch_apply(
                api_update_additional_cost_row,
                services,
                rid,
                body,
                return_type=PurchaseOrderAdditionalCostRow,
            ),
        )
    )
    plan.extend(
        plan_deletes(
            request.delete_additional_cost_ids,
            POOperation.DELETE_ADDITIONAL_COST,
            lambda rid: make_delete_apply(api_delete_po_additional_cost, services, rid),
        )
    )

    return await run_modify_plan(
        request=request,
        naming=EntityNaming(
            entity_type="purchase_order",
            entity_label=f"purchase order {request.id}",
            tool_name="modify_purchase_order",
        ),
        web_url_kind="purchase_order",
        existing=existing_po,
        plan=plan,
        cache_merge=CacheMerge(
            cache=services.typed_cache,
            refetch_for_merge=lambda eid: _fetch_purchase_order_attrs(services, eid),
            # Soft-deleted rows are hidden from the parent fetch even
            # when ``include_deleted=true`` is set on the PO endpoint
            # (the flag only controls top-level inclusion). Fan out to
            # the sibling ``/purchase_order_rows`` endpoint to capture
            # tombstones — mirrors the typed-cache row-watermark
            # rationale documented on ``_PURCHASE_ORDER_ROW_SPEC``.
            refetch_related=(
                (
                    "purchase_order_row",
                    lambda eid: _fetch_po_row_attrs_for_merge(services, eid),
                ),
            ),
        ),
    )


@observe_tool
@unpack_pydantic_params
async def modify_purchase_order(
    request: Annotated[ModifyPurchaseOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Modify a purchase order — unified surface across header, rows, and additional costs.

    Sub-payloads (any subset, all optional):

    - ``update_header`` — patch header fields (incl. status)
    - ``add_rows`` / ``update_rows`` / ``delete_row_ids`` — line item CRUD
    - ``add_additional_costs`` / ``update_additional_costs`` /
      ``delete_additional_cost_ids`` — freight/duty/handling cost rows

    To remove a PO entirely, use the sibling ``delete_purchase_order`` tool.

    Two-step flow: ``preview=true`` (default) returns a per-action preview with
    diffs; ``preview=false`` executes the plan in canonical order (header → row
    adds → row updates → row deletes → cost adds → cost updates → cost deletes).

    **Caveats** (Katana's API is not transactional):

    - Actions apply sequentially. The first failure halts execution
      (fail-fast); earlier actions stay applied server-side.
    - Each action is verified post-execution by reading the API response
      body. Verification mismatch surfaces as ``verified=False`` on the
      action result without raising.
    - The response carries a ``prior_state`` snapshot of the
      pre-modification PO so callers can compose a revert call manually.
    """
    response = await _modify_purchase_order_impl(request, context)
    return to_tool_result(
        response, confirm_request=request, confirm_tool="modify_purchase_order"
    )


# ============================================================================
# Tool: delete_purchase_order
# ============================================================================


async def _delete_purchase_order_impl(
    request: DeletePurchaseOrderRequest, context: Context
) -> ModificationResponse:
    """One-action plan that removes the PO. Katana cascades child rows +
    additional cost rows server-side."""
    return await run_delete_plan(
        request=request,
        services=get_services(context),
        entity_type="purchase_order",
        entity_label=f"purchase order {request.id}",
        web_url_kind="purchase_order",
        fetcher=_fetch_purchase_order_attrs,
        delete_endpoint=api_delete_purchase_order,
        operation=POOperation.DELETE,
    )


@observe_tool
@unpack_pydantic_params
async def delete_purchase_order(
    request: Annotated[DeletePurchaseOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Delete a purchase order. Destructive — the order record is removed.

    Two-step flow: ``preview=true`` (default) returns a preview,
    ``preview=false`` deletes the PO. The response carries a ``prior_state``
    snapshot of the pre-delete PO so callers can recreate it manually if needed.
    """
    response = await _delete_purchase_order_impl(request, context)
    return to_tool_result(
        response, confirm_request=request, confirm_tool="delete_purchase_order"
    )


def register_tools(mcp: FastMCP) -> None:
    """Register all purchase order tools with the FastMCP instance.

    Args:
        mcp: FastMCP server instance to register tools with
    """
    from mcp.types import ToolAnnotations

    from katana_mcp.tools.prefab_ui import register_preview_tool

    _create = ToolAnnotations(
        readOnlyHint=False, destructiveHint=False, openWorldHint=True
    )
    _read = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )
    _destructive = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
        openWorldHint=True,
    )
    _receive = _destructive
    _modify = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
        openWorldHint=True,
    )

    register_preview_tool(
        mcp,
        create_purchase_order,
        tags={"orders", "purchasing", "write"},
        annotations=_create,
        meta=UI_META,
    )
    register_preview_tool(
        mcp,
        receive_purchase_order,
        tags={"orders", "purchasing", "write"},
        annotations=_receive,
        meta=UI_META,
    )
    mcp.tool(
        tags={"orders", "purchasing", "read"},
        annotations=_read,
        meta=UI_META,
    )(verify_order_document)
    mcp.tool(tags={"orders", "purchasing", "read"}, annotations=_read)(
        list_purchase_orders
    )
    mcp.tool(tags={"orders", "purchasing", "read"}, annotations=_read)(
        get_purchase_order
    )
    register_preview_tool(
        mcp,
        modify_purchase_order,
        tags={"orders", "purchasing", "write"},
        annotations=_modify,
        meta=UI_META,
    )
    register_preview_tool(
        mcp,
        delete_purchase_order,
        tags={"orders", "purchasing", "write", "destructive"},
        annotations=_destructive,
        meta=UI_META,
    )
