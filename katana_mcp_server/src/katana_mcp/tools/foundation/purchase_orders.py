"""Purchase order management tools for Katana MCP Server.

Foundation tools for creating, receiving, and verifying purchase orders.

These tools provide:
- create_purchase_order: Create regular purchase orders with preview/confirm pattern
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
from pydantic import BaseModel, Field

from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.list_coercion import CoercedIntListOpt
from katana_mcp.tools.schemas import ConfirmationResult, require_confirmation
from katana_mcp.tools.tool_result_utils import (
    UI_META,
    PaginationMeta,
    apply_date_window_filters,
    coerce_enum,
    enum_to_str,
    format_md_table,
    iso_or_none,
    make_simple_result,
    make_tool_result,
    parse_request_dates,
)
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.client_types import UNSET
from katana_public_api_client.domain.converters import to_unset, unwrap_unset
from katana_public_api_client.models import (
    CreatePurchaseOrderInitialStatus,
    CreatePurchaseOrderRequest as APICreatePurchaseOrderRequest,
    FindPurchaseOrdersBillingStatus,
    FindPurchaseOrdersStatus,
    PurchaseOrderEntityType,
    PurchaseOrderRowRequest,
    RegularPurchaseOrder,
)
from katana_public_api_client.utils import is_success, unwrap, unwrap_as

logger = get_logger(__name__)

# ============================================================================
# Tool 1: create_purchase_order
# ============================================================================


class PurchaseOrderItem(BaseModel):
    """Line item for a purchase order."""

    variant_id: int = Field(..., description="Variant ID to purchase")
    quantity: float = Field(..., description="Quantity to order", gt=0)
    price_per_unit: float = Field(..., description="Unit price")
    tax_rate_id: int | None = Field(None, description="Tax rate ID (optional)")
    purchase_uom: str | None = Field(None, description="Purchase unit of measure")
    purchase_uom_conversion_rate: float | None = Field(
        None, description="Conversion rate for purchase UOM"
    )
    arrival_date: datetime | None = Field(None, description="Expected arrival date")


class CreatePurchaseOrderRequest(BaseModel):
    """Request to create a purchase order."""

    supplier_id: int = Field(..., description="Supplier ID")
    location_id: int = Field(
        ..., description="Location ID where items will be received"
    )
    order_number: str = Field(..., description="Purchase order number")
    items: list[PurchaseOrderItem] = Field(..., description="Line items", min_length=1)
    notes: str | None = Field(None, description="Order notes (additional_info)")
    currency: str | None = Field(None, description="Currency code (e.g., USD, EUR)")
    status: Literal["DRAFT", "NOT_RECEIVED"] | None = Field(
        None,
        description="Initial status — 'DRAFT' or 'NOT_RECEIVED' (default: NOT_RECEIVED)",
    )
    confirm: bool = Field(
        False, description="If false, returns preview. If true, creates order."
    )


class PurchaseOrderResponse(BaseModel):
    """Response from creating a purchase order."""

    id: int | None = None
    order_number: str
    supplier_id: int
    location_id: int
    status: str
    entity_type: str
    total_cost: float | None = None
    currency: str | None = None
    is_preview: bool
    warnings: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    message: str


def _po_response_to_tool_result(response: PurchaseOrderResponse) -> ToolResult:
    """Convert PurchaseOrderResponse to ToolResult with the appropriate Prefab UI."""
    from katana_mcp.tools.prefab_ui import (
        build_order_created_ui,
        build_order_preview_ui,
    )

    order_dict = response.model_dump()
    if response.is_preview:
        ui = build_order_preview_ui(order_dict, "Purchase Order")
    else:
        ui = build_order_created_ui(order_dict, "Purchase Order")

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
        f"{'Previewing' if not request.confirm else 'Creating'} purchase order {request.order_number}"
    )

    # Calculate preview total
    total_cost = sum(item.price_per_unit * item.quantity for item in request.items)

    # Preview mode - just return calculations without API call
    if not request.confirm:
        logger.info(
            f"Preview mode: PO {request.order_number} would have {len(request.items)} items"
        )
        return PurchaseOrderResponse(
            order_number=request.order_number,
            supplier_id=request.supplier_id,
            location_id=request.location_id,
            status=request.status or "NOT_RECEIVED",
            entity_type="regular",
            total_cost=total_cost,
            currency=request.currency,
            is_preview=True,
            next_actions=[
                "Review the order details",
                "Set confirm=true to create the purchase order",
            ],
            message=f"Preview: Purchase order {request.order_number} with {len(request.items)} items totaling {total_cost:.2f}",
        )

    # Confirm mode - use elicitation to get user confirmation before creating
    confirmation = await require_confirmation(
        context,
        f"Place purchase order {request.order_number} with {len(request.items)} items totaling {total_cost:.2f}?",
    )

    if confirmation != ConfirmationResult.CONFIRMED:
        logger.info(f"User did not confirm creation of PO {request.order_number}")
        return PurchaseOrderResponse(
            order_number=request.order_number,
            supplier_id=request.supplier_id,
            location_id=request.location_id,
            status=request.status or "NOT_RECEIVED",
            entity_type="regular",
            total_cost=total_cost,
            currency=request.currency,
            is_preview=True,
            message=f"Purchase order creation {confirmation} by user",
            next_actions=["Review the order details and try again with confirm=true"],
        )

    # User confirmed - create the purchase order via API
    try:
        services = get_services(context)

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

        # Build API request
        api_request = APICreatePurchaseOrderRequest(
            order_no=request.order_number,
            supplier_id=request.supplier_id,
            location_id=request.location_id,
            purchase_order_rows=po_rows,
            entity_type=PurchaseOrderEntityType.REGULAR,
            currency=to_unset(request.currency),
            status=CreatePurchaseOrderInitialStatus(request.status)
            if request.status is not None
            else UNSET,
            order_created_date=datetime.now(UTC),
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

        return PurchaseOrderResponse(
            id=po.id,
            order_number=order_no,
            supplier_id=supplier_id,
            location_id=location_id,
            status=po.status.value if po.status else "UNKNOWN",
            entity_type="regular",
            total_cost=total_cost,
            currency=currency,
            is_preview=False,
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

    Two-step flow: set confirm=false to preview totals without creating, then
    confirm=true to create (prompts for confirmation). Requires supplier_id,
    location_id, order_number, and at least one line item with variant_id,
    quantity, and price_per_unit. Use get_variant_details to look up variant IDs.
    """
    response = await _create_purchase_order_impl(request, context)
    return _po_response_to_tool_result(response)


# ============================================================================
# Tool 2: receive_purchase_order
# ============================================================================


class ReceiveItemRequest(BaseModel):
    """Item to receive from purchase order."""

    purchase_order_row_id: int = Field(..., description="Purchase order row ID")
    quantity: float = Field(..., description="Quantity to receive", gt=0)


class ReceivePurchaseOrderRequest(BaseModel):
    """Request to receive items from a purchase order."""

    order_id: int = Field(..., description="Purchase order ID")
    items: list[ReceiveItemRequest] = Field(
        ..., description="Items to receive", min_length=1
    )
    confirm: bool = Field(
        False, description="If false, returns preview. If true, receives items."
    )


class ReceivePurchaseOrderResponse(BaseModel):
    """Response from receiving purchase order items."""

    order_id: int
    order_number: str
    items_received: int = 0
    is_preview: bool = True
    warnings: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    message: str


def _receive_response_to_tool_result(
    response: ReceivePurchaseOrderResponse,
) -> ToolResult:
    """Convert ReceivePurchaseOrderResponse to ToolResult with JSON content + Prefab UI."""
    from katana_mcp.tools.prefab_ui import build_receipt_ui

    ui = build_receipt_ui(response.model_dump())

    return make_tool_result(response, ui=ui)


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
        f"{'Previewing' if not request.confirm else 'Receiving'} items for PO {request.order_id}"
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

        # Extract order number safely using unwrap_unset
        order_no = unwrap_unset(po.order_no, f"PO-{request.order_id}")

        # Preview mode - return summary without API call
        if not request.confirm:
            logger.info(
                f"Preview mode: Would receive {len(request.items)} items for PO {order_no}"
            )
            return ReceivePurchaseOrderResponse(
                order_id=request.order_id,
                order_number=order_no,
                items_received=len(request.items),
                is_preview=True,
                next_actions=[
                    "Review the items to receive",
                    "Set confirm=true to receive the items and update inventory",
                ],
                message=f"Preview: Receive {len(request.items)} items for PO {order_no}",
            )

        # Confirm mode - use elicitation to get user confirmation before receiving
        confirmation = await require_confirmation(
            context,
            f"Receive {len(request.items)} items for purchase order {order_no} and update inventory?",
        )

        if confirmation != ConfirmationResult.CONFIRMED:
            logger.info(f"User did not confirm receiving items for PO {order_no}")
            return ReceivePurchaseOrderResponse(
                order_id=request.order_id,
                order_number=order_no,
                items_received=0,
                is_preview=True,
                message=f"Item receipt {confirmation} by user",
                next_actions=["Review the items and try again with confirm=true"],
            )

        # User confirmed - receive items via API
        from katana_public_api_client.api.purchase_order import (
            receive_purchase_order as api_receive_purchase_order,
        )
        from katana_public_api_client.models import PurchaseOrderReceiveRow

        # Build receive rows
        receive_rows = []
        for item in request.items:
            row = PurchaseOrderReceiveRow(
                purchase_order_row_id=item.purchase_order_row_id,
                quantity=item.quantity,
                received_date=datetime.now(UTC),
            )
            receive_rows.append(row)

        # Call API
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
        return ReceivePurchaseOrderResponse(
            order_id=request.order_id,
            order_number=order_no,
            items_received=len(request.items),
            is_preview=False,
            next_actions=[
                f"Received {len(request.items)} items",
                "Inventory has been updated",
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

    Two-step flow: confirm=false to preview, confirm=true to receive (prompts
    for confirmation). Use verify_order_document first to validate a supplier
    document against the PO before receiving. Requires the PO ID and row IDs.
    """
    response = await _receive_purchase_order_impl(request, context)
    return _receive_response_to_tool_result(response)


# ============================================================================
# Tool: get_purchase_order
#
# Defined before ``verify_order_document`` so the verification tool can embed
# the same exhaustive ``GetPurchaseOrderResponse`` shape on its response
# (avoids a forward-reference + ``model_rebuild`` dance).
# ============================================================================


class GetPurchaseOrderRequest(BaseModel):
    """Request to look up a purchase order by number or ID."""

    order_no: str | None = Field(
        default=None, description="Purchase order number (e.g., 'PO-1022')"
    )
    order_id: int | None = Field(default=None, description="Purchase order ID")
    format: Literal["markdown", "json"] = Field(
        default="markdown",
        description=(
            "Output format: 'markdown' (default) for human-readable tables; "
            "'json' for structured data consumable by downstream tools/aggregations."
        ),
    )


class PurchaseOrderRowInfo(BaseModel):
    """Full purchase order line item — every field Katana exposes on
    ``PurchaseOrderRow`` is surfaced so callers don't need follow-up lookups
    for standard row fields (UOM conversion, currency, landed_cost, etc.).
    """

    id: int
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None
    quantity: float | None = None
    variant_id: int | None = None
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
    batch_transactions: list[dict[str, Any]] = Field(default_factory=list)


class PurchaseOrderAdditionalCostRowInfo(BaseModel):
    """Full additional cost row — every field Katana exposes on
    ``PurchaseOrderAdditionalCostRow`` (shipping, duties, handling, etc.).
    """

    id: int
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None
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


class SupplierInfo(BaseModel):
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
    addresses: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None


class GetPurchaseOrderResponse(BaseModel):
    """Full purchase-order details. Exhaustive — every field Katana exposes
    on ``RegularPurchaseOrder`` is surfaced, plus nested inline rows and
    fetched-on-demand additional cost rows and accounting metadata. Callers
    don't need follow-up lookups for standard PO data.
    """

    id: int
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None
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
    purchase_order_rows: list[PurchaseOrderRowInfo] = Field(default_factory=list)
    additional_cost_rows: list[PurchaseOrderAdditionalCostRowInfo] = Field(
        default_factory=list
    )
    accounting_metadata: list[PurchaseOrderAccountingMetadataInfo] = Field(
        default_factory=list
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


def _po_row_info(row: Any) -> PurchaseOrderRowInfo:
    """Extract full row info from an attrs ``PurchaseOrderRow``."""
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
) -> GetPurchaseOrderResponse:
    """Build an exhaustive response from an attrs PO plus fetched side data."""
    raw_rows = unwrap_unset(po.purchase_order_rows, None) or []
    rows = [_po_row_info(r) for r in raw_rows]
    supplier = _supplier_info(unwrap_unset(po.supplier, None))

    return GetPurchaseOrderResponse(
        id=po.id,
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

    return _build_get_purchase_order_response(
        po,
        additional_cost_rows=additional_cost_rows,
        accounting_metadata=accounting_metadata,
    )


# ----------------------------------------------------------------------------
# Markdown rendering — canonical Pydantic field names as labels so an LLM
# consumer can't misread a section header as a differently-named field
# (motivation: #346 follow-on).
# ----------------------------------------------------------------------------

_PO_SCALAR_FIELDS: tuple[str, ...] = (
    "id",
    "order_no",
    "status",
    "billing_status",
    "entity_type",
    "supplier_id",
    "location_id",
    "tracking_location_id",
    "default_group_id",
    "currency",
    "total",
    "total_in_base_currency",
    "expected_arrival_date",
    "order_created_date",
    "last_document_status",
    "additional_info",
    "created_at",
    "updated_at",
    "deleted_at",
)

_PO_ROW_FIELDS: tuple[str, ...] = (
    "id",
    "variant_id",
    "quantity",
    "price_per_unit",
    "price_per_unit_in_base_currency",
    "total",
    "total_in_base_currency",
    "purchase_uom",
    "purchase_uom_conversion_rate",
    "tax_rate_id",
    "currency",
    "conversion_rate",
    "conversion_date",
    "arrival_date",
    "received_date",
    "purchase_order_id",
    "landed_cost",
    "group_id",
    "created_at",
    "updated_at",
    "deleted_at",
)

_PO_ADDITIONAL_COST_FIELDS: tuple[str, ...] = (
    "id",
    "additional_cost_id",
    "group_id",
    "name",
    "distribution_method",
    "price",
    "price_in_base",
    "currency",
    "currency_conversion_rate",
    "currency_conversion_rate_fix_date",
    "tax_rate_id",
    "tax_rate",
    "created_at",
    "updated_at",
    "deleted_at",
)

_PO_ACCOUNTING_META_FIELDS: tuple[str, ...] = (
    "id",
    "purchase_order_id",
    "received_items_group_id",
    "integration_type",
    "bill_id",
    "created_at",
)


def _render_po_row_md(row: PurchaseOrderRowInfo) -> list[str]:
    """Render a PO row as a multi-line block under ``purchase_order_rows``."""
    lines = [f"  - **id**: {row.id}"]
    for fname in _PO_ROW_FIELDS:
        if fname == "id":
            continue
        val = getattr(row, fname, None)
        if val is None or val == "":
            continue
        lines.append(f"    **{fname}**: {val}")
    if row.batch_transactions:
        lines.append(
            f"    **batch_transactions** ({len(row.batch_transactions)}): "
            f"{row.batch_transactions}"
        )
    else:
        lines.append("    **batch_transactions**: []")
    return lines


def _render_po_additional_cost_row_md(
    row: PurchaseOrderAdditionalCostRowInfo,
) -> list[str]:
    """Render an additional cost row under ``additional_cost_rows``."""
    lines = [f"  - **id**: {row.id}"]
    for fname in _PO_ADDITIONAL_COST_FIELDS:
        if fname == "id":
            continue
        val = getattr(row, fname, None)
        if val is None or val == "":
            continue
        lines.append(f"    **{fname}**: {val}")
    return lines


def _render_po_accounting_metadata_md(
    meta: PurchaseOrderAccountingMetadataInfo,
) -> list[str]:
    """Render an accounting metadata entry under ``accounting_metadata``."""
    lines = [f"  - **id**: {meta.id}"]
    for fname in _PO_ACCOUNTING_META_FIELDS:
        if fname == "id":
            continue
        val = getattr(meta, fname, None)
        if val is None or val == "":
            continue
        lines.append(f"    **{fname}**: {val}")
    return lines


_SUPPLIER_FIELDS: tuple[str, ...] = (
    "id",
    "name",
    "email",
    "phone",
    "currency",
    "comment",
    "default_address_id",
    "created_at",
    "updated_at",
    "deleted_at",
)


def _render_supplier_md(supplier: SupplierInfo) -> list[str]:
    """Render an embedded supplier under ``**supplier**:`` using canonical
    field names, matching the scheme used for rows and accounting metadata.
    """
    lines: list[str] = []
    for fname in _SUPPLIER_FIELDS:
        val = getattr(supplier, fname, None)
        if val is None or val == "":
            continue
        lines.append(f"  **{fname}**: {val}")
    if supplier.addresses:
        lines.append(
            f"  **addresses** ({len(supplier.addresses)}): {supplier.addresses}"
        )
    else:
        lines.append("  **addresses**: []")
    return lines


def _render_get_purchase_order_md(
    response: GetPurchaseOrderResponse, *, embed: bool = False
) -> str:
    """Render an exhaustive PO response as canonical-labeled markdown.

    When ``embed=True`` the top-level ``## PO …`` heading is omitted —
    used when the PO is rendered as a nested block under another response
    (e.g., ``verify_order_document``) where an indented markdown heading
    would still be parsed as a top-level heading and break intended
    nesting (copilot feedback on #357).
    """
    md_lines: list[str] = []
    if not embed:
        md_lines.append(f"## PO {response.order_no or response.id}")

    for fname in _PO_SCALAR_FIELDS:
        val = getattr(response, fname)
        if val is None or val == "":
            continue
        md_lines.append(f"**{fname}**: {val}")

    # supplier: inline block under the canonical key so the LLM can trace
    # every embedded supplier field without a separate lookup.
    if response.supplier is not None:
        md_lines.append("")
        md_lines.append("**supplier**:")
        md_lines.extend(_render_supplier_md(response.supplier))
    else:
        md_lines.append("**supplier**: null")

    # purchase_order_rows: explicit list syntax so empty lists render as `[]`
    # rather than a dangling section header an LLM could misread (#346).
    if response.purchase_order_rows:
        md_lines.append("")
        md_lines.append(
            f"**purchase_order_rows** ({len(response.purchase_order_rows)}):"
        )
        for row in response.purchase_order_rows:
            md_lines.extend(_render_po_row_md(row))
    else:
        md_lines.append("**purchase_order_rows**: []")

    if response.additional_cost_rows:
        md_lines.append("")
        md_lines.append(
            f"**additional_cost_rows** ({len(response.additional_cost_rows)}):"
        )
        for row in response.additional_cost_rows:
            md_lines.extend(_render_po_additional_cost_row_md(row))
    else:
        md_lines.append("**additional_cost_rows**: []")

    if response.accounting_metadata:
        md_lines.append("")
        md_lines.append(
            f"**accounting_metadata** ({len(response.accounting_metadata)}):"
        )
        for meta in response.accounting_metadata:
            md_lines.extend(_render_po_accounting_metadata_md(meta))
    else:
        md_lines.append("**accounting_metadata**: []")

    return "\n".join(md_lines)


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

    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2),
            structured_content=response.model_dump(),
        )

    return make_simple_result(
        _render_get_purchase_order_md(response),
        structured_data=response.model_dump(),
    )


# ============================================================================
# Tool: verify_order_document
# ============================================================================


class DocumentItem(BaseModel):
    """Item from a supplier document to verify."""

    sku: str = Field(..., description="Item SKU from document")
    quantity: float = Field(..., description="Quantity from document")
    unit_price: float | None = Field(None, description="Price from document")


class MatchResult(BaseModel):
    """Result of matching a document item to a PO line."""

    sku: str = Field(..., description="Item SKU")
    quantity: float = Field(..., description="Matched quantity")
    unit_price: float | None = Field(None, description="Matched price")
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
    type: DiscrepancyType = Field(..., description="Type of discrepancy")
    expected: float | None = Field(None, description="Expected value (from PO)")
    actual: float | None = Field(None, description="Actual value (from document)")
    message: str = Field(..., description="Human-readable description")


class VerifyOrderDocumentRequest(BaseModel):
    """Request to verify a document against a purchase order."""

    order_id: int = Field(..., description="Purchase order ID")
    document_items: list[DocumentItem] = Field(
        ..., description="Items from the document to verify", min_length=1
    )
    format: Literal["markdown", "json"] = Field(
        default="markdown",
        description=(
            "Output format: 'markdown' (default) for human-readable tables; "
            "'json' for structured data consumable by downstream tools/aggregations."
        ),
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
    matches: list[MatchResult] = Field(default_factory=list)
    discrepancies: list[Discrepancy] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)
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
        # to avoid doubling latency on the verify path.
        default_group_id = unwrap_unset(po.default_group_id, None)
        additional_cost_rows, accounting_metadata = await asyncio.gather(
            _fetch_po_additional_cost_rows(services, default_group_id),
            _fetch_po_accounting_metadata(services, po.id),
        )
        exhaustive_po = _build_get_purchase_order_response(
            po,
            additional_cost_rows=additional_cost_rows,
            accounting_metadata=accounting_metadata,
        )

        # Extract order number safely using unwrap_unset
        order_no = unwrap_unset(po.order_no, f"PO-{request.order_id}")

        # Get PO rows - use unwrap_unset for UNSET check
        po_rows_raw = unwrap_unset(po.purchase_order_rows, None)
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

        po_rows = po_rows_raw

        # Collect all variant IDs from PO rows using unwrap_unset
        variant_ids = []
        for row in po_rows:
            variant_id = unwrap_unset(row.variant_id, None)
            if variant_id is not None:
                variant_ids.append(variant_id)

        # Fetch only the needed variants by ID (API-level filtering)
        try:
            filtered_variants = await services.client.variants.list(ids=variant_ids)
            variant_by_id = {v.id: v for v in filtered_variants}
        except Exception as e:
            logger.error(f"Failed to fetch variants: {e}")
            raise

        # Build a map of SKU -> PO row for matching
        sku_to_row: dict[str, Any] = {}
        for row in po_rows:
            variant_id = unwrap_unset(row.variant_id, None)
            if variant_id is None:
                continue
            variant = variant_by_id.get(variant_id)
            if variant and variant.sku:
                sku_to_row[variant.sku] = row

        # Now match document items to PO rows
        matches: list[MatchResult] = []
        discrepancies: list[Discrepancy] = []

        for doc_item in request.document_items:
            # Check if SKU exists in PO
            if doc_item.sku not in sku_to_row:
                discrepancies.append(
                    Discrepancy(
                        sku=doc_item.sku,
                        type=DiscrepancyType.MISSING_IN_PO,
                        expected=None,
                        actual=doc_item.quantity,
                        message=f"SKU {doc_item.sku}: Not found in purchase order {order_no}",
                    )
                )
                continue

            row = sku_to_row[doc_item.sku]
            row_qty = unwrap_unset(row.quantity, 0.0)
            row_price = unwrap_unset(row.price_per_unit, 0.0)

            # Track match status and discrepancies
            has_qty_mismatch = False
            has_price_mismatch = False

            # Check quantity match
            if (
                abs(doc_item.quantity - row_qty) > 0.01
            ):  # Small tolerance for float comparison
                has_qty_mismatch = True
                discrepancies.append(
                    Discrepancy(
                        sku=doc_item.sku,
                        type=DiscrepancyType.QUANTITY_MISMATCH,
                        expected=row_qty,
                        actual=doc_item.quantity,
                        message=f"SKU {doc_item.sku}: Quantity mismatch (Document: {doc_item.quantity}, PO: {row_qty})",
                    )
                )

            # Check price match if provided
            if (
                doc_item.unit_price is not None
                and abs(doc_item.unit_price - row_price) > 0.01
            ):
                has_price_mismatch = True
                discrepancies.append(
                    Discrepancy(
                        sku=doc_item.sku,
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

            # Create match result
            matches.append(
                MatchResult(
                    sku=doc_item.sku,
                    quantity=doc_item.quantity,
                    unit_price=doc_item.unit_price,
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
    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2),
            structured_content=response.model_dump(),
        )
    return _verify_response_to_tool_result(response)


# ============================================================================
# Tool: list_purchase_orders (list-tool pattern v2)
# ============================================================================


class ListPurchaseOrdersRequest(BaseModel):
    """Request to list/filter purchase orders (list-tool pattern v2)."""

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
        default=None, description="Filter by receiving location ID"
    )
    tracking_location_id: int | None = Field(
        default=None,
        description=(
            "Filter by tracking location ID (outsourced POs). The cache "
            "stores this as a hoisted column on every row; regular POs "
            "match only when ``None`` is filtered, which doesn't apply "
            "here — pair with ``entity_type='outsourced'`` to scope."
        ),
    )
    supplier_id: int | None = Field(default=None, description="Filter by supplier ID")
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

    # Output formatting
    format: Literal["markdown", "json"] = Field(
        default="markdown",
        description=(
            "Output format: 'markdown' (default) for human-readable tables; "
            "'json' for structured data consumable by downstream tools/aggregations."
        ),
    )


class PurchaseOrderRowSummary(BaseModel):
    """Summary of a purchase order line item (used when include_rows=True)."""

    id: int | None = None
    variant_id: int | None = None
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
    # time and we skip the correlated COUNT subquery.
    if request.include_rows:
        stmt = select(CachedPurchaseOrder).options(
            selectinload(CachedPurchaseOrder.purchase_order_rows)
        )
    else:
        row_count_subq = (
            select(func.count(CachedPurchaseOrderRow.id))
            .where(CachedPurchaseOrderRow.purchase_order_id == CachedPurchaseOrder.id)
            .correlate(CachedPurchaseOrder)
            .scalar_subquery()
            .label("row_count")
        )
        stmt = select(CachedPurchaseOrder, row_count_subq)
    stmt = _apply_purchase_order_filters(stmt, request, parsed_dates)
    stmt = stmt.order_by(
        CachedPurchaseOrder.created_at.desc(), CachedPurchaseOrder.id.desc()
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

    summaries: list[PurchaseOrderSummary] = []
    for po, row_count in orders_with_counts:
        rows: list[PurchaseOrderRowSummary] | None = None
        if request.include_rows:
            rows = [
                PurchaseOrderRowSummary(
                    id=r.id,
                    variant_id=r.variant_id,
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

    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2),
            structured_content=response.model_dump(),
        )

    if not response.orders:
        md = "No purchase orders match the given filters."
    else:
        table = format_md_table(
            headers=[
                "Order #",
                "Status",
                "Supplier",
                "Location",
                "Rows",
                "Total",
                "Expected Arrival",
            ],
            rows=[
                [
                    o.order_no or o.id,
                    o.status or "—",
                    o.supplier_id if o.supplier_id is not None else "—",
                    o.location_id if o.location_id is not None else "—",
                    o.row_count,
                    f"{o.total:.2f} {o.currency or ''}" if o.total is not None else "—",
                    o.expected_arrival_date or "—",
                ]
                for o in response.orders
            ],
        )
        md = f"## Purchase Orders ({response.total_count})\n\n{table}"

    if response.pagination is not None:
        p = response.pagination
        if p.page is not None and p.total_pages is not None:
            summary = f"\n\nPage {p.page} of {p.total_pages}"
            if p.total_records is not None:
                summary += f" (total: {p.total_records} records)"
            md += summary

    return make_simple_result(md, structured_data=response.model_dump())


def register_tools(mcp: FastMCP) -> None:
    """Register all purchase order tools with the FastMCP instance.

    Args:
        mcp: FastMCP server instance to register tools with
    """
    from mcp.types import ToolAnnotations

    _write = ToolAnnotations(
        readOnlyHint=False, destructiveHint=False, openWorldHint=True
    )
    _read = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )

    mcp.tool(
        tags={"orders", "purchasing", "write"},
        annotations=_write,
        meta=UI_META,
    )(create_purchase_order)
    mcp.tool(
        tags={"orders", "purchasing", "write"},
        annotations=_write,
        meta=UI_META,
    )(receive_purchase_order)
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
