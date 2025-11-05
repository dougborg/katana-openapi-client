"""Purchase order management tools for Katana MCP Server.

Foundation tools for creating, receiving, and verifying purchase orders.

These tools provide:
- create_purchase_order: Create regular purchase orders with preview/confirm pattern
- receive_purchase_order: Receive items from purchase orders (stub)
- verify_order_document: Verify supplier documents against POs (stub)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import cast

from fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

from katana_mcp.services import get_services
from katana_public_api_client.client_types import UNSET
from katana_public_api_client.models import (
    CreatePurchaseOrderRequest as APICreatePurchaseOrderRequest,
    CreatePurchaseOrderRequestEntityType,
    CreatePurchaseOrderRequestStatus,
    PurchaseOrderRowRequest,
    RegularPurchaseOrder,
)

logger = logging.getLogger(__name__)

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
    status: str | None = Field(
        None,
        description="Initial status (NOT_RECEIVED, PARTIALLY_RECEIVED, RECEIVED, CANCELLED)",
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
    warnings: list[str] = []
    next_actions: list[str] = []
    message: str


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

    # Confirm mode - create the purchase order via API
    try:
        services = get_services(context)

        # Build purchase order rows
        po_rows = []
        for item in request.items:
            row = PurchaseOrderRowRequest(
                variant_id=item.variant_id,
                quantity=item.quantity,
                price_per_unit=item.price_per_unit,
                tax_rate_id=item.tax_rate_id if item.tax_rate_id is not None else UNSET,
                purchase_uom=item.purchase_uom
                if item.purchase_uom is not None
                else UNSET,
                purchase_uom_conversion_rate=item.purchase_uom_conversion_rate
                if item.purchase_uom_conversion_rate is not None
                else UNSET,
                arrival_date=item.arrival_date
                if item.arrival_date is not None
                else UNSET,
            )
            po_rows.append(row)

        # Build API request
        api_request = APICreatePurchaseOrderRequest(
            order_no=request.order_number,
            supplier_id=request.supplier_id,
            location_id=request.location_id,
            purchase_order_rows=po_rows,
            entity_type=CreatePurchaseOrderRequestEntityType.REGULAR,
            currency=request.currency if request.currency is not None else UNSET,
            status=CreatePurchaseOrderRequestStatus(request.status)
            if request.status is not None
            else UNSET,
            order_created_date=datetime.now(UTC),
            additional_info=request.notes if request.notes is not None else UNSET,
        )

        # Call API
        from katana_public_api_client.api.purchase_order import (
            create_purchase_order as api_create_purchase_order,
        )

        response = await api_create_purchase_order.asyncio_detailed(
            client=services.client, body=api_request
        )

        if response.status_code == 200 and isinstance(
            response.parsed, RegularPurchaseOrder
        ):
            po = response.parsed
            logger.info(f"Successfully created purchase order ID {po.id}")

            # Extract values, handling UNSET with cast for type narrowing
            order_no: str = (
                cast(str, po.order_no)
                if not isinstance(po.order_no, type(UNSET))
                else request.order_number
            )
            supplier_id: int = (
                cast(int, po.supplier_id)
                if not isinstance(po.supplier_id, type(UNSET))
                else request.supplier_id
            )
            location_id: int = (
                cast(int, po.location_id)
                if not isinstance(po.location_id, type(UNSET))
                else request.location_id
            )
            currency: str | None = (
                cast(str, po.currency)
                if not isinstance(po.currency, type(UNSET)) and po.currency is not None
                else None
            )

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
        else:
            raise Exception(f"API returned unexpected status: {response.status_code}")

    except Exception as e:
        logger.error(f"Failed to create purchase order: {e}")
        raise


async def create_purchase_order(
    request: CreatePurchaseOrderRequest, context: Context
) -> PurchaseOrderResponse:
    """Create a purchase order with two-step confirmation.

    This tool supports a two-step confirmation process:
    1. Preview (confirm=false): Shows order details and calculations without creating
    2. Confirm (confirm=true): Creates the actual purchase order in Katana

    The tool creates regular purchase orders (not outsourced) and supports:
    - Multiple line items with different variants
    - Optional tax rates, purchase UOMs, and arrival dates
    - Currency specification
    - Order notes

    Args:
        request: Request with purchase order details and confirm flag
        context: Server context with KatanaClient

    Returns:
        Purchase order response with ID (if created) and details

    Example:
        Preview:
            Request: {"supplier_id": 4001, "location_id": 1, "order_number": "PO-2024-001",
                     "items": [{"variant_id": 501, "quantity": 100, "price_per_unit": 25.50}],
                     "confirm": false}
            Returns: Preview with calculated total

        Confirm:
            Request: Same as above but with "confirm": true
            Returns: Created PO with ID and status
    """
    return await _create_purchase_order_impl(request, context)


# ============================================================================
# Tool 2: receive_purchase_order (STUB)
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
    order_number: str = "stub_not_implemented"
    items_received: int = 0
    is_preview: bool = True
    warnings: list[str] = []
    next_actions: list[str] = []
    message: str = "Receive purchase order tool is a stub - not yet implemented"


async def _receive_purchase_order_impl(
    request: ReceivePurchaseOrderRequest, context: Context
) -> ReceivePurchaseOrderResponse:
    """STUB implementation of receive_purchase_order tool.

    Args:
        request: Request with purchase order ID and items to receive
        context: Server context with KatanaClient

    Returns:
        Receive response (currently stub)

    Note:
        This is a placeholder. Full implementation requires:
        - Understanding PurchaseOrderReceiveRow model
        - Proper API endpoint usage (no ID parameter in path)
        - Batch transaction handling
        - Inventory update confirmation
    """
    logger.warning("receive_purchase_order is a stub - returning placeholder response")

    return ReceivePurchaseOrderResponse(
        order_id=request.order_id,
        items_received=len(request.items),
        is_preview=not request.confirm,
        warnings=["This tool is not yet fully implemented"],
        next_actions=[
            "Purchase order receiving not yet implemented",
            "See tool documentation for implementation status",
        ],
        message=f"STUB: Would {'receive' if request.confirm else 'preview receiving'} {len(request.items)} items for PO {request.order_id}",
    )


async def receive_purchase_order(
    request: ReceivePurchaseOrderRequest, context: Context
) -> ReceivePurchaseOrderResponse:
    """Receive items from a purchase order (STUB - not yet implemented).

    This tool will support a two-step confirmation process:
    1. Preview (confirm=false): Shows items to be received
    2. Confirm (confirm=true): Receives the items and updates inventory

    Args:
        request: Request with purchase order ID, items, and confirm flag
        context: Server context with KatanaClient

    Returns:
        Receive response (currently stub)

    Note:
        This is a stub implementation. Full functionality coming in future update.
    """
    return await _receive_purchase_order_impl(request, context)


# ============================================================================
# Tool 3: verify_order_document (STUB)
# ============================================================================


class DocumentItem(BaseModel):
    """Item from a supplier document to verify."""

    sku: str = Field(..., description="Item SKU from document")
    quantity: float = Field(..., description="Quantity from document")
    unit_price: float | None = Field(None, description="Price from document")


class VerifyOrderDocumentRequest(BaseModel):
    """Request to verify a document against a purchase order."""

    order_id: int = Field(..., description="Purchase order ID")
    document_items: list[DocumentItem] = Field(
        ..., description="Items from the document to verify", min_length=1
    )


class VerifyOrderDocumentResponse(BaseModel):
    """Response from verifying an order document."""

    order_id: int
    matches: int = 0
    discrepancies: list[str] = []
    suggested_actions: list[str] = []
    message: str = "Document verification is a stub - not yet implemented"


async def _verify_order_document_impl(
    request: VerifyOrderDocumentRequest, context: Context
) -> VerifyOrderDocumentResponse:
    """STUB implementation of verify_order_document tool.

    Args:
        request: Request with order ID and document items
        context: Server context with KatanaClient

    Returns:
        Verification response (currently stub)

    Note:
        This is a placeholder. Full implementation requires:
        - Fetching PO details with line items
        - Matching document items to PO rows by SKU
        - Comparing quantities and prices
        - Identifying discrepancies with actionable suggestions
    """
    logger.warning("verify_order_document is a stub - returning placeholder response")

    return VerifyOrderDocumentResponse(
        order_id=request.order_id,
        matches=0,
        discrepancies=["Document verification not yet implemented"],
        suggested_actions=[
            "Manual verification required",
            "Tool implementation pending",
        ],
        message=f"STUB: Would verify {len(request.document_items)} items against PO {request.order_id}",
    )


async def verify_order_document(
    request: VerifyOrderDocumentRequest, context: Context
) -> VerifyOrderDocumentResponse:
    """Verify a document against a purchase order (STUB - not yet implemented).

    Compares items from a supplier document (invoice, packing slip, etc.)
    against the purchase order to identify matches and discrepancies.

    Args:
        request: Request with order ID and document items
        context: Server context with KatanaClient

    Returns:
        Verification response (currently stub)

    Note:
        This is a stub implementation. Full functionality coming in future update.
    """
    return await _verify_order_document_impl(request, context)


def register_tools(mcp: FastMCP) -> None:
    """Register all purchase order tools with the FastMCP instance.

    Args:
        mcp: FastMCP server instance to register tools with

    Note:
        These are currently stub implementations that return placeholder responses.
        They are registered to establish the tool interface, but full functionality
        requires additional implementation work with the complex Katana PO API.
    """
    mcp.tool()(create_purchase_order)
    mcp.tool()(receive_purchase_order)
    mcp.tool()(verify_order_document)
