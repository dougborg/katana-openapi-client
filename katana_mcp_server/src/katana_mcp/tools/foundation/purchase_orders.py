"""Purchase order management tools for Katana MCP Server.

Foundation tools for creating, receiving, and verifying purchase orders.

Note: This is a STUB implementation. The Katana purchase order API is complex
with many required fields (order_no, location_id, etc.) that need proper handling.
These tools are registered but return placeholder responses until fully implemented.

See GitHub issue for tracking: TODO - create issue for PO implementation
"""

from __future__ import annotations

import logging

from fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ============================================================================
# Tool 1: create_purchase_order (STUB)
# ============================================================================


class PurchaseOrderItem(BaseModel):
    """Line item for a purchase order."""

    variant_id: int = Field(..., description="Variant ID to purchase")
    quantity: float = Field(..., description="Quantity to order", gt=0)
    price_per_unit: float = Field(..., description="Unit price")


class CreatePurchaseOrderRequest(BaseModel):
    """Request to create a purchase order."""

    supplier_id: int = Field(..., description="Supplier ID")
    location_id: int = Field(
        ..., description="Location ID where items will be received"
    )
    order_number: str = Field(..., description="Purchase order number")
    items: list[PurchaseOrderItem] = Field(..., description="Line items", min_length=1)
    notes: str | None = Field(None, description="Order notes")
    confirm: bool = Field(
        False, description="If false, returns preview. If true, creates order."
    )


class PurchaseOrderResponse(BaseModel):
    """Response from creating a purchase order."""

    id: int | None = None
    order_number: str | None = None
    supplier_id: int
    location_id: int
    status: str = "stub_not_implemented"
    total_cost: float | None = None
    is_preview: bool = True
    warnings: list[str] = []
    next_actions: list[str] = []
    message: str = "Purchase order tool is a stub - not yet implemented"


async def _create_purchase_order_impl(
    request: CreatePurchaseOrderRequest, context: Context
) -> PurchaseOrderResponse:
    """STUB implementation of create_purchase_order tool.

    Args:
        request: Request with purchase order details
        context: Server context with KatanaClient

    Returns:
        Purchase order response (currently stub)

    Note:
        This is a placeholder. Full implementation requires:
        - Proper CreatePurchaseOrderRequest model usage
        - Entity type handling (regular vs outsourced)
        - Tax rate handling
        - Currency handling
        - Proper error handling
    """
    logger.warning("create_purchase_order is a stub - returning placeholder response")

    # Calculate preview total
    total_cost = sum(item.price_per_unit * item.quantity for item in request.items)

    return PurchaseOrderResponse(
        supplier_id=request.supplier_id,
        location_id=request.location_id,
        order_number=request.order_number,
        total_cost=total_cost,
        is_preview=not request.confirm,
        warnings=["This tool is not yet fully implemented"],
        next_actions=[
            "Purchase order creation not yet implemented",
            "See tool documentation for implementation status",
        ],
        message=f"STUB: Would {'create' if request.confirm else 'preview'} PO for supplier {request.supplier_id}",
    )


async def create_purchase_order(
    request: CreatePurchaseOrderRequest, context: Context
) -> PurchaseOrderResponse:
    """Create a purchase order (STUB - not yet implemented).

    This tool will support a two-step confirmation process:
    1. Preview (confirm=false): Shows order details and calculations
    2. Confirm (confirm=true): Creates the actual purchase order

    Args:
        request: Request with purchase order details and confirm flag
        context: Server context with KatanaClient

    Returns:
        Purchase order response (currently stub)

    Note:
        This is a stub implementation. Full functionality coming in future update.
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
