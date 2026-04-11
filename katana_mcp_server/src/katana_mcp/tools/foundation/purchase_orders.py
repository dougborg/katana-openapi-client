"""Purchase order management tools for Katana MCP Server.

Foundation tools for creating, receiving, and verifying purchase orders.

These tools provide:
- create_purchase_order: Create regular purchase orders with preview/confirm pattern
- receive_purchase_order: Receive items from purchase orders with inventory updates
- verify_order_document: Verify supplier documents against POs
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Any, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, Field

from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.schemas import ConfirmationResult, require_confirmation
from katana_mcp.tools.tool_result_utils import (
    enum_to_str,
    format_md_table,
    iso_or_none,
    make_tool_result,
)
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.client_types import UNSET
from katana_public_api_client.domain.converters import to_unset, unwrap_unset
from katana_public_api_client.models import (
    CreatePurchaseOrderInitialStatus,
    CreatePurchaseOrderRequest as APICreatePurchaseOrderRequest,
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
    """Convert PurchaseOrderResponse to ToolResult with markdown + Prefab UI."""
    from katana_mcp.tools.prefab_ui import (
        build_order_created_ui,
        build_order_preview_ui,
    )

    # Format next_actions as bullet list for template
    next_actions_text = "\n".join(f"- {action}" for action in response.next_actions)

    # Handle None values for template
    total_cost = response.total_cost if response.total_cost is not None else 0.0
    currency = response.currency if response.currency else "USD"

    template_name = "order_preview" if response.is_preview else "order_created"

    order_dict = response.model_dump()
    if response.is_preview:
        ui = build_order_preview_ui(order_dict, "Purchase Order")
    else:
        ui = build_order_created_ui(order_dict, "Purchase Order")

    return make_tool_result(
        response,
        template_name,
        ui=ui,
        id=response.id,
        order_number=response.order_number,
        supplier_id=response.supplier_id,
        location_id=response.location_id,
        status=response.status,
        total_cost=total_cost,
        currency=currency,
        entity_type=response.entity_type,
        next_actions_text=next_actions_text,
    )


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
    """Convert ReceivePurchaseOrderResponse to ToolResult with markdown + Prefab UI."""
    from katana_mcp.tools.prefab_ui import build_receipt_ui

    ui = build_receipt_ui(response.model_dump())

    return make_tool_result(
        response,
        "order_received",
        ui=ui,
        order_id=response.order_id,
        order_number=response.order_number,
        items_received=response.items_received,
        message=response.message,
    )


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
# Tool 3: verify_order_document
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


class VerifyOrderDocumentResponse(BaseModel):
    """Response from verifying an order document."""

    order_id: int
    matches: list[MatchResult] = Field(default_factory=list)
    discrepancies: list[Discrepancy] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)
    overall_status: str = Field(..., description="match, partial_match, or no_match")
    message: str


def _verify_response_to_tool_result(
    response: VerifyOrderDocumentResponse,
) -> ToolResult:
    """Convert VerifyOrderDocumentResponse to ToolResult with markdown + Prefab UI."""
    from katana_mcp.tools.prefab_ui import build_verification_ui

    # Format matches and discrepancies as text for template
    if response.matches:
        matches_text = "\n".join(
            f"- **{m.sku}**: {m.quantity} units @ ${m.unit_price or 0:.2f} ({m.status})"
            for m in response.matches
        )
    else:
        matches_text = "No matches found"

    if response.discrepancies:
        discrepancies_text = "\n".join(f"- {d.message}" for d in response.discrepancies)
    else:
        discrepancies_text = "No discrepancies"

    suggested_actions_text = "\n".join(
        f"- {action}" for action in response.suggested_actions
    )

    # Choose template based on overall status
    if response.overall_status == "match":
        template_name = "order_verification_match"
    elif response.overall_status == "partial_match":
        template_name = "order_verification_partial"
    else:
        template_name = "order_verification_no_match"

    ui = build_verification_ui(response.model_dump())

    return make_tool_result(
        response,
        template_name,
        ui=ui,
        order_id=response.order_id,
        overall_status=response.overall_status,
        message=response.message,
        matches_text=matches_text,
        discrepancies_text=discrepancies_text,
        suggested_actions_text=suggested_actions_text,
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

        # Extract order number safely using unwrap_unset
        order_no = unwrap_unset(po.order_no, f"PO-{request.order_id}")

        # Get PO rows - use unwrap_unset for UNSET check
        po_rows_raw = unwrap_unset(po.purchase_order_rows, None)
        if not po_rows_raw:
            return VerifyOrderDocumentResponse(
                order_id=request.order_id,
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
# Tool: get_purchase_order
# ============================================================================


class GetPurchaseOrderRequest(BaseModel):
    """Request to look up a purchase order by number or ID."""

    order_no: str | None = Field(
        default=None, description="Purchase order number (e.g., 'PO-1022')"
    )
    order_id: int | None = Field(default=None, description="Purchase order ID")


class PurchaseOrderRowInfo(BaseModel):
    """Summary of a purchase order line item."""

    id: int
    variant_id: int | None
    quantity: float | None
    price_per_unit: float | None
    arrival_date: str | None
    received_date: str | None
    total: float | None


class GetPurchaseOrderResponse(BaseModel):
    """Response containing purchase order details."""

    id: int
    order_no: str | None
    status: str | None
    supplier_id: int | None
    location_id: int | None
    currency: str | None
    expected_arrival_date: str | None
    total: float | None
    rows: list[PurchaseOrderRowInfo]


def _po_row_info(row: Any) -> PurchaseOrderRowInfo:
    """Extract row info from an attrs PurchaseOrderRow."""
    arrival = unwrap_unset(row.arrival_date, None)
    received = unwrap_unset(row.received_date, None)
    return PurchaseOrderRowInfo(
        id=row.id,
        variant_id=unwrap_unset(row.variant_id, None),
        quantity=unwrap_unset(row.quantity, None),
        price_per_unit=unwrap_unset(row.price_per_unit, None),
        arrival_date=iso_or_none(arrival),
        received_date=iso_or_none(received),
        total=unwrap_unset(row.total, None),
    )


async def _get_purchase_order_impl(
    request: GetPurchaseOrderRequest, context: Context
) -> GetPurchaseOrderResponse:
    """Look up a PO by order_no or ID and return structured details."""
    from katana_public_api_client.api.purchase_order import (
        find_purchase_orders,
        get_purchase_order as api_get_purchase_order,
    )
    from katana_public_api_client.models import ErrorResponse
    from katana_public_api_client.utils import unwrap_data

    if not request.order_no and not request.order_id:
        raise ValueError("Either order_no or order_id must be provided")

    services = get_services(context)

    if request.order_id:
        response = await api_get_purchase_order.asyncio_detailed(
            id=request.order_id, client=services.client
        )
        po_result = unwrap(response)
        if isinstance(po_result, ErrorResponse):
            raise ValueError(f"Purchase order ID {request.order_id} not found")
        po = po_result
    else:
        if not request.order_no:
            raise ValueError("order_no is required when order_id is not provided")
        list_response = await find_purchase_orders.asyncio_detailed(
            client=services.client, order_no=request.order_no, limit=1
        )
        orders = unwrap_data(list_response, default=[])
        if not orders:
            raise ValueError(f"Purchase order '{request.order_no}' not found")
        po = orders[0]

    # Extract rows
    raw_rows = unwrap_unset(po.purchase_order_rows, [])
    rows = [_po_row_info(r) for r in raw_rows] if raw_rows else []

    expected_arrival = unwrap_unset(po.expected_arrival_date, None)

    return GetPurchaseOrderResponse(
        id=po.id,
        order_no=unwrap_unset(po.order_no, None),
        status=enum_to_str(unwrap_unset(po.status, None)),
        supplier_id=unwrap_unset(po.supplier_id, None),
        location_id=unwrap_unset(po.location_id, None),
        currency=unwrap_unset(po.currency, None),
        expected_arrival_date=expected_arrival.isoformat()
        if expected_arrival
        else None,
        total=unwrap_unset(po.total, None),
        rows=rows,
    )


@observe_tool
@unpack_pydantic_params
async def get_purchase_order(
    request: Annotated[GetPurchaseOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Look up a purchase order by order number or ID.

    Returns order details including status, supplier, location, total, and all
    line items with variant_ids, quantities, prices, and arrival dates. Use to
    inspect a PO before receiving, or to find the variant IDs of items on order.

    Provide either order_no (e.g., 'PO-1022') or order_id.
    """
    from katana_mcp.tools.tool_result_utils import make_simple_result

    response = await _get_purchase_order_impl(request, context)

    lines = [
        f"## PO {response.order_no or response.id}",
        f"- **Status**: {response.status}",
    ]
    if response.supplier_id is not None:
        lines.append(f"- **Supplier ID**: {response.supplier_id}")
    if response.location_id is not None:
        lines.append(f"- **Location ID**: {response.location_id}")
    if response.total is not None:
        lines.append(f"- **Total**: {response.total} {response.currency or ''}")
    if response.expected_arrival_date:
        lines.append(f"- **Expected Arrival**: {response.expected_arrival_date}")

    if response.rows:
        lines.append("")
        lines.append("### Line Items")
        lines.append(
            format_md_table(
                headers=[
                    "Row ID",
                    "Variant ID",
                    "Qty",
                    "Price",
                    "Arrival",
                    "Received",
                ],
                rows=[
                    [
                        r.id,
                        r.variant_id,
                        r.quantity,
                        r.price_per_unit,
                        r.arrival_date or "N/A",
                        r.received_date or "N/A",
                    ]
                    for r in response.rows
                ],
            )
        )

    return make_simple_result(
        "\n".join(lines),
        structured_data=response.model_dump(),
    )


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

    mcp.tool(tags={"orders", "purchasing", "write"}, annotations=_write)(
        create_purchase_order
    )
    mcp.tool(tags={"orders", "purchasing", "write"}, annotations=_write)(
        receive_purchase_order
    )
    mcp.tool(tags={"orders", "purchasing", "read"}, annotations=_read)(
        verify_order_document
    )
    mcp.tool(tags={"orders", "purchasing", "read"}, annotations=_read)(
        get_purchase_order
    )
