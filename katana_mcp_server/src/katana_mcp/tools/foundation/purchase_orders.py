"""Purchase order management tools for Katana MCP Server.

Foundation tools for creating, receiving, and verifying purchase orders.

These tools provide:
- create_purchase_order: Create regular purchase orders with preview/confirm pattern
- receive_purchase_order: Receive items from purchase orders with inventory updates
- verify_order_document: Verify supplier documents against POs
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Annotated, Any, cast

from fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

from katana_mcp.services import get_services
from katana_mcp.unpack import Unpack, unpack_pydantic_params
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


@unpack_pydantic_params
async def create_purchase_order(
    request: Annotated[CreatePurchaseOrderRequest, Unpack()], context: Context
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
    order_number: str = "stub_not_implemented"
    items_received: int = 0
    is_preview: bool = True
    warnings: list[str] = []
    next_actions: list[str] = []
    message: str = "Receive purchase order tool is a stub - not yet implemented"


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

        if po_response.status_code != 200 or not isinstance(
            po_response.parsed, RegularPurchaseOrder
        ):
            raise Exception(
                f"Failed to fetch purchase order {request.order_id}: {po_response.status_code}"
            )

        po = po_response.parsed
        order_no = (
            cast(str, po.order_no)
            if not isinstance(po.order_no, type(UNSET))
            else f"PO-{request.order_id}"
        )

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

        # Confirm mode - receive items via API
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

        if response.status_code == 204:
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
        else:
            raise Exception(f"API returned unexpected status: {response.status_code}")

    except Exception as e:
        logger.error(f"Failed to receive purchase order: {e}")
        raise


@unpack_pydantic_params
async def receive_purchase_order(
    request: Annotated[ReceivePurchaseOrderRequest, Unpack()], context: Context
) -> ReceivePurchaseOrderResponse:
    """Receive items from a purchase order with two-step confirmation.

    This tool supports a two-step confirmation process:
    1. Preview (confirm=false): Shows items to be received
    2. Confirm (confirm=true): Receives the items and updates inventory

    The tool marks items as received in Katana and updates inventory levels.
    The API returns 204 (no content) on success.

    Args:
        request: Request with purchase order ID, items, and confirm flag
        context: Server context with KatanaClient

    Returns:
        Receive response with status and details

    Example:
        Preview:
            Request: {"order_id": 1234, "items": [{"purchase_order_row_id": 501, "quantity": 100}], "confirm": false}
            Returns: Preview with summary

        Confirm:
            Request: Same as above but with "confirm": true
            Returns: Success message with updated inventory
    """
    return await _receive_purchase_order_impl(request, context)


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


class DiscrepancyType(str, Enum):
    """Types of discrepancies.

    Note: EXTRA_IN_DOCUMENT is reserved for future use to detect items
    in the document that exceed PO quantities or are unexpected.
    Currently, we only verify items from the document against the PO.
    """

    QUANTITY_MISMATCH = "quantity_mismatch"
    PRICE_MISMATCH = "price_mismatch"
    MISSING_IN_PO = "missing_in_po"
    EXTRA_IN_DOCUMENT = "extra_in_document"  # Reserved for future enhancement


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
    matches: list[MatchResult] = []
    discrepancies: list[Discrepancy] = []
    suggested_actions: list[str] = []
    overall_status: str = Field(..., description="match, partial_match, or no_match")
    message: str


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

        if po_response.status_code != 200 or not isinstance(
            po_response.parsed, RegularPurchaseOrder
        ):
            raise Exception(
                f"Failed to fetch purchase order {request.order_id}: {po_response.status_code}"
            )

        po = po_response.parsed
        order_no = (
            cast(str, po.order_no)
            if not isinstance(po.order_no, type(UNSET))
            else f"PO-{request.order_id}"
        )

        # Get PO rows
        if (
            isinstance(po.purchase_order_rows, type(UNSET))
            or not po.purchase_order_rows
        ):
            return VerifyOrderDocumentResponse(
                order_id=request.order_id,
                matches=[],
                discrepancies=[],
                suggested_actions=["Verify purchase order data in Katana"],
                overall_status="no_match",
                message=f"Purchase order {order_no} has no line items",
            )

        po_rows = po.purchase_order_rows

        # Collect all variant IDs from PO rows
        variant_ids = []
        for row in po_rows:
            if not isinstance(row.variant_id, type(UNSET)):
                variant_ids.append(cast(int, row.variant_id))

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
            if isinstance(row.variant_id, type(UNSET)):
                continue
            variant_id = cast(int, row.variant_id)
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
            row_qty = (
                cast(float, row.quantity)
                if not isinstance(row.quantity, type(UNSET))
                else 0.0
            )
            row_price = (
                cast(float, row.price_per_unit)
                if not isinstance(row.price_per_unit, type(UNSET))
                else 0.0
            )

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


@unpack_pydantic_params
async def verify_order_document(
    request: Annotated[VerifyOrderDocumentRequest, Unpack()], context: Context
) -> VerifyOrderDocumentResponse:
    """Verify a document against a purchase order.

    Compares items from a supplier document (invoice, packing slip, etc.)
    against the purchase order to identify matches and discrepancies.

    The tool:
    - Fetches the purchase order details
    - Looks up variants to match SKUs
    - Compares quantities and prices
    - Reports discrepancies with actionable suggestions

    Args:
        request: Request with order ID and document items
        context: Server context with KatanaClient

    Returns:
        Verification response with matches and discrepancies

    Example:
        Request: {
            "order_id": 1234,
            "document_items": [
                {"sku": "WIDGET-001", "quantity": 100, "unit_price": 25.50},
                {"sku": "WIDGET-002", "quantity": 50, "unit_price": 30.00}
            ]
        }
        Returns: Verification report with matches/discrepancies
    """
    return await _verify_order_document_impl(request, context)


def register_tools(mcp: FastMCP) -> None:
    """Register all purchase order tools with the FastMCP instance.

    Registers three fully-functional purchase order tools:
    - create_purchase_order: Create regular purchase orders
    - receive_purchase_order: Receive items and update inventory
    - verify_order_document: Verify supplier documents against POs

    All tools follow the preview/confirm pattern for safe operation.

    Args:
        mcp: FastMCP server instance to register tools with
    """
    mcp.tool()(create_purchase_order)
    mcp.tool()(receive_purchase_order)
    mcp.tool()(verify_order_document)
