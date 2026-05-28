"""Sales order management tools for Katana MCP Server.

Foundation tools covering the sales-order lifecycle: create, list, get
(read-mostly tools), plus the unified modify/delete pair.

Tools:
- create_sales_order: Create sales orders with preview/apply pattern
- list_sales_orders / get_sales_order: discovery + exhaustive read
- modify_sales_order: header + row CRUD + addresses + fulfillments +
  shipping-fee CRUD via typed sub-payload slots
- delete_sales_order: destructive sibling of modify_sales_order
"""

from __future__ import annotations

import asyncio
from datetime import datetime
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
    float_or_none,
    iso_or_none,
    make_json_result,
    make_tool_result,
    parse_request_dates,
    resolve_entity_name,
)
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_mcp.web_urls import katana_web_url

# Modify/delete API endpoints used by ``modify_sales_order`` /
# ``delete_sales_order``. Hoisted to module scope for declarative dependency
# tracking and consistency with the rest of the codebase.
from katana_public_api_client.api.sales_order import (
    delete_sales_order as api_delete_sales_order,
    get_sales_order as api_get_sales_order,
    update_sales_order as api_update_sales_order,
)
from katana_public_api_client.api.sales_order_address import (
    create_sales_order_address as api_create_so_address,
    delete_sales_order_address as api_delete_so_address,
    update_sales_order_address as api_update_so_address,
)
from katana_public_api_client.api.sales_order_fulfillment import (
    create_sales_order_fulfillment as api_create_so_fulfillment,
    delete_sales_order_fulfillment as api_delete_so_fulfillment,
    get_sales_order_fulfillment as api_get_so_fulfillment,
    update_sales_order_fulfillment as api_update_so_fulfillment,
)
from katana_public_api_client.api.sales_order_row import (
    create_sales_order_row as api_create_so_row,
    delete_sales_order_row as api_delete_so_row,
    get_sales_order_row as api_get_so_row,
    update_sales_order_row as api_update_so_row,
)
from katana_public_api_client.api.sales_orders import (
    create_sales_order_shipping_fee as api_create_so_shipping_fee,
    delete_sales_order_shipping_fee as api_delete_so_shipping_fee,
    get_sales_order_shipping_fee as api_get_so_shipping_fee,
    update_sales_order_shipping_fee as api_update_so_shipping_fee,
)
from katana_public_api_client.client_types import UNSET, Unset
from katana_public_api_client.domain.converters import to_unset, unwrap_unset
from katana_public_api_client.models import (
    AddressEntityType,
    CreateSalesOrderAddressRequest as APICreateSOAddressRequest,
    CreateSalesOrderFulfillmentRequest as APICreateSOFulfillmentRequest,
    CreateSalesOrderRequest as APICreateSalesOrderRequest,
    CreateSalesOrderRequestAddressesItem as APICreateSORequestAddressesItem,
    CreateSalesOrderRequestCustomFieldsType0 as APISOCustomFieldsMap,
    CreateSalesOrderRequestSalesOrderRowsItem,
    CreateSalesOrderRequestSalesOrderRowsItemAttributesItem as APISORowAttributeItem,
    CreateSalesOrderRowRequest as APICreateSORowRequest,
    CreateSalesOrderShippingFeeRequest as APICreateSOShippingFeeRequest,
    CreateSalesOrderStatus,
    SalesOrder,
    SalesOrderAddress as APISalesOrderAddress,
    SalesOrderFulfillment,
    SalesOrderFulfillmentRowRequest,
    SalesOrderFulfillmentStatus,
    SalesOrderRow,
    SalesOrderShippingFee,
    UpdateSalesOrderAddressRequest as APIUpdateSOAddressRequest,
    UpdateSalesOrderFulfillmentRequest as APIUpdateSOFulfillmentRequest,
    UpdateSalesOrderRequest as APIUpdateSalesOrderRequest,
    UpdateSalesOrderRowRequest as APIUpdateSORowRequest,
    UpdateSalesOrderShippingFeeRequest as APIUpdateSOShippingFeeRequest,
    UpdateSalesOrderStatus,
)
from katana_public_api_client.models_pydantic._generated import (
    CachedCustomer,
    CachedLocation,
    CachedVariant,
)
from katana_public_api_client.utils import unwrap_as

logger = get_logger(__name__)


# ============================================================================
# Tool 1: create_sales_order
# ============================================================================


class SalesOrderRowAttribute(BaseModel):
    """A free-form key/value attribute attached to a sales-order row.

    Used for product customization metadata (engraving text, monogram,
    gift-wrap notes, etc.). The same shape lands on
    ``modify_sales_order.update_rows[*].attributes`` so callers can edit
    these later.
    """

    model_config = ConfigDict(extra="forbid")

    key: str = Field(..., description="Attribute key")
    value: str = Field(..., description="Attribute value")


class SalesOrderItem(BaseModel):
    """Line item for a sales order."""

    model_config = ConfigDict(extra="forbid")

    variant_id: int = Field(..., description="Variant ID to sell")
    quantity: float = Field(..., description="Quantity to sell", gt=0)
    price_per_unit: float | None = Field(
        default=None,
        description="Override price per unit (uses default if not specified)",
    )
    tax_rate_id: int | None = Field(
        default=None,
        description=("Tax rate ID (optional). Look up via `list_tax_rates`."),
    )
    location_id: int | None = Field(
        default=None,
        description=("Location to pick from (optional). Look up via `list_locations`."),
    )
    total_discount: float | None = Field(
        default=None, description="Discount for this line item (optional)"
    )
    attributes: list[SalesOrderRowAttribute] | None = Field(
        default=None,
        description=(
            "Free-form key/value attributes attached to this row — e.g. "
            "engraving text, monogram, gift-wrap notes. Use a list-of-objects "
            "shape: `[{key: 'engraving', value: 'For Dad'}]`."
        ),
    )


class SalesOrderAddress(BaseModel):
    """Billing or shipping address for a sales order.

    Field names mirror the wire format — ``zip`` (not ``zip_code``) matches
    what ``get_sales_order`` returns and what the Katana API accepts on
    inline create. The attrs-side wire field is ``zip_`` (builtin-name
    avoidance, JSON name ``zip``); the field name here intentionally shadows
    the ``zip()`` builtin within this model scope to keep the JSON contract
    transparent for callers.
    """

    model_config = ConfigDict(extra="forbid")

    entity_type: Literal["billing", "shipping"] = Field(
        ..., description="Type of address - billing or shipping"
    )
    first_name: str | None = Field(default=None, description="First name of contact")
    last_name: str | None = Field(default=None, description="Last name of contact")
    company: str | None = Field(default=None, description="Company name")
    phone: str | None = Field(default=None, description="Phone number")
    line_1: str | None = Field(default=None, description="Primary address line")
    line_2: str | None = Field(default=None, description="Secondary address line")
    city: str | None = Field(default=None, description="City")
    state: str | None = Field(default=None, description="State or province")
    zip: str | None = Field(default=None, description="Postal/ZIP code")
    country: str | None = Field(
        default=None, description="Country code (e.g., US, CA, GB)"
    )


class SOShippingFeeAdd(BaseModel):
    """A new shipping fee to attach to a sales order.

    Shared between the ``create_sales_order`` inline-fees slot (#818) and
    ``modify_sales_order.add_shipping_fees``. Defined at module top so it's
    available to ``CreateSalesOrderRequest``; the modify path imports it
    from the same location.
    """

    model_config = ConfigDict(extra="forbid")

    amount: str = Field(..., description="Fee amount (decimal string)")
    description: str | None = Field(
        default=None,
        description="Customer-facing fee label (e.g., 'Standard shipping')",
    )
    tax_rate_id: int | None = Field(
        default=None,
        description=("Tax rate ID. Look up via `list_tax_rates`."),
    )


class SOShippingFeeUpdate(BaseModel):
    """Patch to an existing SO shipping fee.

    Note: Katana's API requires ``amount`` even on PATCH — it's a replace
    semantic on the fee's amount, not a partial update. The other fields
    are genuinely optional.
    """

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Shipping fee ID to update")
    amount: str = Field(..., description="Fee amount (required by API)")
    description: str | None = Field(
        default=None,
        description="New customer-facing fee label",
    )
    tax_rate_id: int | None = Field(
        default=None,
        description=("Tax rate ID. Look up via `list_tax_rates`."),
    )


class CreateSalesOrderRequest(BaseModel):
    """Request to create a sales order."""

    model_config = ConfigDict(extra="forbid")

    customer_id: int = Field(..., description="Customer ID placing the order")
    order_number: str = Field(..., description="Unique sales order number")
    items: list[SalesOrderItem] = Field(..., description="Line items", min_length=1)
    location_id: int | None = Field(
        default=None,
        description=(
            "Primary fulfillment location ID (optional). Look up via `list_locations`."
        ),
    )
    delivery_date: WireDatetime | None = Field(
        default=None,
        description=(
            "Requested delivery date (optional) — ISO 8601 date or datetime "
            "(e.g. '2026-05-08T14:30:00Z' or '2026-05-08T14:30:00-08:00'). "
            "Naive datetimes (no timezone) are interpreted as UTC."
        ),
    )
    order_created_date: WireDatetime | None = Field(
        default=None,
        description=(
            "Date the order was placed. Leave None to let Katana stamp the "
            "current time server-side; supply a value for back-fills (e.g. "
            "importing historical orders) or to reflect actual placement when "
            "different from the call time."
        ),
    )
    currency: str | None = Field(
        default=None,
        description="Currency code (defaults to company base currency)",
    )
    addresses: list[SalesOrderAddress] | None = Field(
        default=None, description="Billing and/or shipping addresses (optional)"
    )
    notes: str | None = Field(default=None, description="Additional notes (optional)")
    customer_ref: str | None = Field(
        default=None, description="Customer's reference number (optional)"
    )
    tracking_number: str | None = Field(
        default=None,
        description=(
            "Shipping tracking number (optional). Set if a carrier label is "
            "already known at order-creation time; otherwise patch in later "
            "via `modify_sales_order.update_header.tracking_number`."
        ),
    )
    tracking_number_url: str | None = Field(
        default=None,
        description="URL pointing to the tracking page for the shipment.",
    )
    ecommerce_order_type: str | None = Field(
        default=None,
        description=(
            "Type of ecommerce order, e.g. 'shopify_order' / 'woocommerce_order'. "
            "Use when the SO mirrors an order from an ecommerce store."
        ),
    )
    ecommerce_store_name: str | None = Field(
        default=None,
        description=(
            "Name of the ecommerce store the order originated from "
            "(e.g. 'Acme Online Store')."
        ),
    )
    ecommerce_order_id: str | None = Field(
        default=None,
        description=(
            "Original order ID from the ecommerce platform — used to "
            "cross-reference the Katana SO back to the storefront record."
        ),
    )
    custom_fields: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Custom-field values attached to the sales order header, keyed by "
            "configured field name (e.g. `{'PO Reference': 'PO-12345'}`). "
            "Names must already exist on the SO custom-field collection "
            "(configured via Katana's UI) and value types must match each "
            "field's configured type."
        ),
    )
    shipping_fees: list[SOShippingFeeAdd] | None = Field(
        default=None,
        description=(
            "Optional shipping fees to attach to the new SO. Each entry: "
            "`amount` (decimal string, required), `description` (label like "
            "'Standard shipping'), `tax_rate_id` (see `list_tax_rates`). "
            "Wire-level: Katana's `POST /sales_orders` does NOT accept "
            "inline fees, so the apply path creates the SO first and then "
            "fires `POST /sales_order_shipping_fee` per fee. Best-effort "
            "semantics — if the SO succeeds but a fee fails, the response "
            "carries a warning and the SO is preserved; retry the failed "
            "fees via `modify_sales_order(id=<so_id>, add_shipping_fees=[...])`."
        ),
    )
    preview: bool = Field(
        default=True,
        description="If true (default), returns preview. If false, creates order.",
    )


class ShippingFeeOutcome(BaseModel):
    """Per-fee outcome row for ``create_sales_order``'s inline shipping fees.

    Used for both preview (planned fees with ``succeeded=None``) and apply
    (per-fee results with ``succeeded=True``/``False``). The UI renders one
    row per outcome — preview shows the planned amount/description, applied
    swaps in an APPLIED/FAILED status pill.

    Best-effort semantics on apply: the parent SO can succeed while one or
    more fees fail. Failed fees report ``error`` text; surviving rows can
    be retried via ``modify_sales_order(id=<so_id>, add_shipping_fees=[...])``.
    """

    description: str | None = Field(
        default=None,
        description="Customer-facing fee label, mirrors the request entry.",
    )
    amount: str | None = Field(
        default=None,
        description="Fee amount (decimal string), mirrors the request entry.",
    )
    tax_rate_id: int | None = Field(
        default=None,
        description="Tax rate ID associated with the fee, if any.",
    )
    succeeded: bool | None = Field(
        default=None,
        description=(
            "None on preview; True/False on apply. False indicates the SO "
            "succeeded but this fee POST failed — retry via "
            "`modify_sales_order(id=<so_id>, add_shipping_fees=[...])`."
        ),
    )
    created_id: int | None = Field(
        default=None,
        description="Server-assigned shipping-fee ID on success.",
    )
    error: str | None = Field(
        default=None,
        description="Error message when this fee failed to create.",
    )


class SalesOrderResponse(BaseModel):
    """Response from creating a sales order."""

    id: int | None = None
    order_number: str
    customer_id: int
    customer_name: str | None = None
    location_id: int | None = None
    location_name: str | None = Field(
        default=None,
        description=(
            "Resolved location display name (via ``resolve_entity_name`` on "
            "``CachedLocation``). Pre-#card-ux ``build_so_create_ui`` called "
            "``_render_party_line(name=None, ...)`` and the helper degraded "
            "to ``'Location ID: <id>'`` (anti-pattern #7). Now the impl side "
            "resolves the name; the card-side party-line shows ``'Location: "
            "<name>'`` instead of the bare id."
        ),
    )
    status: str | None = None
    total: float | None = None
    currency: str | None = None
    delivery_date: str | None = None
    item_count: int | None = None
    is_preview: bool
    shipping_fee_outcomes: list[ShippingFeeOutcome] = Field(
        default_factory=list,
        description=(
            "Per-fee outcome rows when ``shipping_fees`` was supplied. "
            "Preview: planned fees with ``succeeded=None``. Apply: per-fee "
            "results with ``succeeded`` + ``created_id`` (on success) or "
            "``error`` (on failure). Empty when no fees were requested."
        ),
    )
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


def _validate_shipping_fee_amounts(
    fees: list[SOShippingFeeAdd],
) -> list[str]:
    """Sanity-check shipping-fee ``amount`` strings on the request.

    Returns a list of ``BLOCK:``-prefixed warning strings — one per fee that
    fails to parse as a non-negative decimal. The Katana wire shape carries
    ``amount`` as a decimal string, so the simplest meaningful validation
    we can do at request time is to confirm each amount actually parses.

    Note: ``SOShippingFeeAdd`` does not carry a per-fee currency field
    (shipping fees inherit the parent SO's currency at the wire level),
    so a "currency mismatch" check is structurally impossible on the
    current schema. This guard catches the closely-related class of
    request-shape bugs the wire-level POST would otherwise 422 on.

    ``Decimal`` constructor accepts "NaN" and "Infinity" as valid strings
    (they raise ``InvalidOperation`` on subsequent arithmetic, not parse).
    Explicitly reject non-finite values so the user gets a clear BLOCK
    warning instead of letting the wire POST fail with a generic 422
    (or worse — a later comparison raising ``InvalidOperation``).
    """
    from decimal import Decimal, InvalidOperation

    warnings: list[str] = []
    for idx, fee in enumerate(fees, start=1):
        try:
            parsed = Decimal(fee.amount)
        except (InvalidOperation, ValueError):
            warnings.append(
                f"{BLOCK_WARNING_PREFIX} shipping_fees[{idx}].amount "
                f"({fee.amount!r}) is not a valid decimal — Katana's "
                f"POST /sales_order_shipping_fee requires a parseable "
                f"decimal string."
            )
            continue
        if not parsed.is_finite():
            warnings.append(
                f"{BLOCK_WARNING_PREFIX} shipping_fees[{idx}].amount "
                f"({fee.amount!r}) is not a finite decimal (NaN/Infinity) "
                f"— Katana's POST /sales_order_shipping_fee requires a "
                f"finite decimal string."
            )
            continue
        try:
            is_negative = parsed < 0
        except InvalidOperation:
            # Defensive — by here ``parsed`` is finite, but ``< 0`` on a
            # signaling NaN could still raise. Treat as invalid.
            warnings.append(
                f"{BLOCK_WARNING_PREFIX} shipping_fees[{idx}].amount "
                f"({fee.amount!r}) could not be compared as a decimal — "
                f"Katana's POST /sales_order_shipping_fee requires a "
                f"comparable decimal string."
            )
            continue
        if is_negative:
            warnings.append(
                f"{BLOCK_WARNING_PREFIX} shipping_fees[{idx}].amount "
                f"({fee.amount!r}) is negative — shipping fees must be "
                f"non-negative."
            )
    return warnings


def _outcomes_from_planned_fees(
    fees: list[SOShippingFeeAdd],
) -> list[ShippingFeeOutcome]:
    """Convert request-side ``SOShippingFeeAdd`` list to outcome rows.

    Used for both the preview (succeeded=None, no created_id/error) and
    as the seed list for the apply path — each outcome's ``succeeded`` /
    ``created_id`` / ``error`` is mutated in place as the per-fee POSTs
    land. ``ShippingFeeOutcome`` intentionally omits ``ConfigDict(frozen=
    True)`` to allow this in-place mutation; tests pin the mutation
    behavior.
    """
    return [
        ShippingFeeOutcome(
            description=fee.description,
            amount=fee.amount,
            tax_rate_id=fee.tax_rate_id,
        )
        for fee in fees
    ]


async def _create_sales_order_impl(
    request: CreateSalesOrderRequest, context: Context
) -> SalesOrderResponse:
    """Implementation of create_sales_order tool.

    Args:
        request: Request with sales order details
        context: Server context with KatanaClient

    Returns:
        Sales order response with details

    Raises:
        ValueError: If validation fails
        Exception: If API call fails
    """
    logger.info(
        f"{'Previewing' if request.preview else 'Creating'} sales order {request.order_number}"
    )

    # Calculate preview total (estimate based on items with prices)
    total_estimate = sum(
        (item.price_per_unit or 0.0) * item.quantity - (item.total_discount or 0.0)
        for item in request.items
    )

    requested_fees = request.shipping_fees or []

    # Resolve customer + location names once, up front, so every return
    # path (preview / refusal / success) carries the resolved Tier-3
    # reference fields. Pre-fix the apply-path shipping-fee refusal
    # silently dropped them and the card fell back to ``"Customer ID: <id>"``
    # — review item #5. The cache-miss advisories thread through
    # ``resolution_warnings`` so refusal-branch responses can include
    # them too (mirrors PO RECEIVED / MO duplicate-link refusal fixes).
    services = get_services(context)
    customer_name, cust_warn = await resolve_entity_name(
        services.typed_cache.catalog,
        CachedCustomer,
        request.customer_id,
        entity_label="Customer",
    )
    resolution_warnings: list[str] = [cust_warn] if cust_warn else []
    location_name: str | None = None
    if request.location_id is not None:
        location_name, loc_warn = await resolve_entity_name(
            services.typed_cache.catalog,
            CachedLocation,
            request.location_id,
            entity_label="Location",
        )
        if loc_warn:
            resolution_warnings.append(loc_warn)

    if request.preview:
        logger.info(
            f"Preview mode: SO {request.order_number} would have {len(request.items)} items"
        )

        warnings: list[str] = list(resolution_warnings)
        if request.location_id is None:
            warnings.append(
                "No location_id specified - order will use default location"
            )
        if request.delivery_date is None:
            warnings.append(
                "No delivery_date specified - order will have no delivery deadline"
            )
        # Validate shipping-fee amounts at preview time — surfacing a BLOCK
        # warning gates the Confirm button so the user fixes the request
        # before the wire-level fee POST would 422.
        if requested_fees:
            warnings.extend(_validate_shipping_fee_amounts(requested_fees))

        return SalesOrderResponse(
            order_number=request.order_number,
            customer_id=request.customer_id,
            customer_name=customer_name,
            location_id=request.location_id,
            location_name=location_name,
            status="PENDING",
            total=total_estimate if total_estimate > 0 else None,
            currency=request.currency,
            delivery_date=request.delivery_date.isoformat()
            if request.delivery_date
            else None,
            item_count=len(request.items),
            is_preview=True,
            shipping_fee_outcomes=_outcomes_from_planned_fees(requested_fees),
            warnings=warnings,
            next_actions=[
                "Review the order details",
                "Set preview=false to create the sales order",
            ],
            message=f"Preview: Sales order {request.order_number} with {len(request.items)} items"
            + (f" totaling {total_estimate:.2f}" if total_estimate > 0 else ""),
        )

    try:
        # ``services`` already obtained above for the name-resolution
        # pass; no second ``get_services`` call needed.

        # Apply-path BLOCK validation: amounts must parse to non-negative
        # decimals BEFORE we POST the SO. We don't roll back the SO on a
        # later fee failure, so a malformed amount caught after the SO
        # POST would leave a created SO + zero applied fees on the books.
        # Preventing the SO POST is the only clean exit. (Same validation
        # the preview path emits as a BLOCK warning to gate the Confirm
        # button — an agent that called ``preview=False`` directly bypasses
        # that gate, so we re-check here.)
        #
        # On failure we return ``is_preview=True`` (not False) so the card
        # UI seeds ``state.applied=False`` and renders as a preview with
        # BLOCK warnings disabling the Confirm button — visually matches
        # the actual outcome (nothing was created). Returning
        # ``is_preview=False`` would flip the card into the "CREATED"
        # rendering despite no SO existing, which misleads the operator.
        if requested_fees:
            block_warnings = _validate_shipping_fee_amounts(requested_fees)
            if block_warnings:
                return SalesOrderResponse(
                    order_number=request.order_number,
                    customer_id=request.customer_id,
                    customer_name=customer_name,
                    location_id=request.location_id,
                    location_name=location_name,
                    is_preview=True,
                    shipping_fee_outcomes=_outcomes_from_planned_fees(requested_fees),
                    warnings=block_warnings + resolution_warnings,
                    next_actions=[
                        "Fix the failing shipping_fees amounts and retry",
                    ],
                    message=(
                        f"Sales order {request.order_number} was NOT created — "
                        f"one or more shipping_fees amounts failed validation. "
                        f"Fix the amounts and re-issue with preview=false."
                    ),
                )

        # Build sales order rows
        so_rows = []
        for item in request.items:
            row_attributes: list[APISORowAttributeItem] | Unset = UNSET
            if item.attributes is not None:
                row_attributes = [
                    APISORowAttributeItem(key=a.key, value=a.value)
                    for a in item.attributes
                ]
            row = CreateSalesOrderRequestSalesOrderRowsItem(
                variant_id=item.variant_id,
                quantity=item.quantity,
                price_per_unit=to_unset(item.price_per_unit),
                tax_rate_id=to_unset(item.tax_rate_id),
                location_id=to_unset(item.location_id),
                total_discount=to_unset(item.total_discount),
                attributes=row_attributes,
            )
            so_rows.append(row)

        # Build addresses if provided. Use the inline write-shaped DTO (no
        # ``id`` / ``sales_order_id`` — those are server-assigned and rejected
        # by the live API on inline create). See #772.
        addresses_list: list[APICreateSORequestAddressesItem] | Unset = UNSET
        if request.addresses:
            addresses_list = []
            for addr in request.addresses:
                api_addr = APICreateSORequestAddressesItem(
                    entity_type=AddressEntityType(addr.entity_type),
                    first_name=to_unset(addr.first_name),
                    last_name=to_unset(addr.last_name),
                    company=to_unset(addr.company),
                    phone=to_unset(addr.phone),
                    line_1=to_unset(addr.line_1),
                    line_2=to_unset(addr.line_2),
                    city=to_unset(addr.city),
                    state=to_unset(addr.state),
                    zip_=to_unset(addr.zip),
                    country=to_unset(addr.country),
                )
                addresses_list.append(api_addr)

        # Build API request. order_created_date is forwarded from the caller
        # (None => UNSET => Katana server-stamps it) — the previous
        # datetime.now(UTC) hardcode silently overwrote any caller intent and
        # blocked back-fills, mirroring the create_purchase_order regression
        # that #605 / #627 fixed.
        custom_fields_map: APISOCustomFieldsMap | Unset = UNSET
        if request.custom_fields is not None:
            custom_fields_map = APISOCustomFieldsMap.from_dict(request.custom_fields)

        api_request = APICreateSalesOrderRequest(
            order_no=request.order_number,
            customer_id=request.customer_id,
            sales_order_rows=so_rows,
            location_id=to_unset(request.location_id),
            delivery_date=to_unset(request.delivery_date),
            order_created_date=to_unset(request.order_created_date),
            currency=to_unset(request.currency),
            addresses=addresses_list,
            additional_info=to_unset(request.notes),
            customer_ref=to_unset(request.customer_ref),
            tracking_number=to_unset(request.tracking_number),
            tracking_number_url=to_unset(request.tracking_number_url),
            ecommerce_order_type=to_unset(request.ecommerce_order_type),
            ecommerce_store_name=to_unset(request.ecommerce_store_name),
            ecommerce_order_id=to_unset(request.ecommerce_order_id),
            custom_fields=custom_fields_map,
            status=CreateSalesOrderStatus.PENDING,
        )

        # Call API
        from katana_public_api_client.api.sales_order import (
            create_sales_order as api_create_sales_order,
        )

        response = await api_create_sales_order.asyncio_detailed(
            client=services.client, body=api_request
        )

        # unwrap_as() raises typed exceptions on error, returns typed SalesOrder
        so = unwrap_as(response, SalesOrder)
        logger.info(f"Successfully created sales order ID {so.id}")

        # Extract values using unwrap_unset for clean UNSET handling
        currency = unwrap_unset(so.currency, None)
        total = unwrap_unset(so.total, None)

        # Inline shipping fees (#818). The wire endpoint POST /sales_orders
        # does NOT accept fees inline, so we fire POST /sales_order_shipping_fee
        # per fee against the just-created SO. Best-effort semantics: SO
        # success is durable; per-fee failures surface as outcomes + a
        # warning telling the user how to retry the failed fees via
        # modify_sales_order(id=<so_id>, add_shipping_fees=[...]).
        fee_outcomes = _outcomes_from_planned_fees(requested_fees)
        fee_warnings: list[str] = []
        # ``SalesOrder.id`` is non-optional in the generated model — ``unwrap_as``
        # raises if the wire shape is missing it, so by this point ``so.id`` is
        # guaranteed populated; no need to guard.
        if requested_fees:
            for outcome, fee in zip(fee_outcomes, requested_fees, strict=True):
                fee_body = _build_create_shipping_fee_request(so.id, fee)
                try:
                    fee_resp = await api_create_so_shipping_fee.asyncio_detailed(
                        client=services.client, body=fee_body
                    )
                    created_fee = unwrap_as(fee_resp, SalesOrderShippingFee)
                except Exception as fee_exc:
                    logger.warning(
                        "create_sales_order shipping fee POST failed",
                        sales_order_id=so.id,
                        amount=fee.amount,
                        description=fee.description,
                        error=str(fee_exc),
                    )
                    outcome.succeeded = False
                    outcome.error = str(fee_exc)
                    continue
                outcome.succeeded = True
                outcome.created_id = created_fee.id

            failed_count = sum(1 for o in fee_outcomes if o.succeeded is False)
            if failed_count:
                fee_warnings.append(
                    f"{failed_count} of {len(requested_fees)} shipping fee(s) "
                    f"failed to create on SO {so.id} — the sales order itself "
                    f"is preserved. Retry the failed fees via "
                    f"`modify_sales_order(id={so.id}, add_shipping_fees=[...])`."
                )

        next_actions = [
            f"Sales order created with ID {so.id}",
            "Use fulfill_order to ship items when ready",
        ]
        if any(o.succeeded is False for o in fee_outcomes):
            next_actions.append(
                f"Retry failed shipping fees via "
                f"modify_sales_order(id={so.id}, add_shipping_fees=[...])"
            )

        message = f"Successfully created sales order {so.order_no} (ID: {so.id})"
        if requested_fees:
            ok_count = sum(1 for o in fee_outcomes if o.succeeded is True)
            message += f" with {ok_count}/{len(requested_fees)} shipping fee(s) applied"

        # Reuse the customer + location names resolved up front in the
        # common case where Katana echoed back the IDs we sent — saves a
        # typed-cache round-trip per name and prevents duplicate
        # cache-miss advisories in ``resolution_warnings`` (Copilot
        # finding on PR #861). Only re-resolve when Katana assigned a
        # different ID (e.g., the caller omitted ``location_id`` and
        # the server picked a default).
        apply_customer_name = customer_name
        apply_resolution_warnings: list[str] = []
        if so.customer_id != request.customer_id:
            apply_customer_name, cust_warn = await resolve_entity_name(
                services.typed_cache.catalog,
                CachedCustomer,
                so.customer_id,
                entity_label="Customer",
            )
            if cust_warn:
                apply_resolution_warnings.append(cust_warn)

        apply_location_id = unwrap_unset(so.location_id, None)
        if apply_location_id == request.location_id:
            apply_location_name = location_name
        elif apply_location_id is not None:
            apply_location_name, loc_warn = await resolve_entity_name(
                services.typed_cache.catalog,
                CachedLocation,
                apply_location_id,
                entity_label="Location",
            )
            if loc_warn:
                apply_resolution_warnings.append(loc_warn)
        else:
            apply_location_name = None

        return SalesOrderResponse(
            id=so.id,
            order_number=so.order_no,
            customer_id=so.customer_id,
            customer_name=apply_customer_name,
            location_id=so.location_id,
            location_name=apply_location_name,
            status=so.status.value if so.status else "UNKNOWN",
            total=total,
            currency=currency,
            is_preview=False,
            shipping_fee_outcomes=fee_outcomes,
            warnings=(fee_warnings + resolution_warnings + apply_resolution_warnings),
            katana_url=katana_web_url("sales_order", so.id),
            next_actions=next_actions,
            message=message,
        )

    except Exception as e:
        logger.error(f"Failed to create sales order: {e}")
        raise


@observe_tool
@unpack_pydantic_params
async def create_sales_order(
    request: Annotated[CreateSalesOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Create a sales order for a customer purchase.

    Two-step flow: preview=true (default) to preview totals, preview=false to create.
    Requires customer_id, order_number, and at least one line item with
    variant_id and quantity. Supports optional pricing overrides, discounts,
    delivery dates, and billing/shipping addresses.
    """
    from katana_mcp.tools.prefab_ui import build_so_create_ui

    response = await _create_sales_order_impl(request, context)

    ui = build_so_create_ui(
        response.model_dump(mode="json"),
        confirm_request=request,
        confirm_tool="create_sales_order",
    )

    return make_tool_result(response, ui=ui)


# ============================================================================
# Tool 2: list_sales_orders
# ============================================================================


class ListSalesOrdersRequest(BaseModel):
    """Request to list/filter sales orders (list-tool pattern v2)."""

    model_config = ConfigDict(extra="forbid")

    # Paging
    limit: int = Field(
        default=50,
        ge=1,
        le=250,
        description=(
            "Max orders to return (default 50, min 1, max 250 — Katana's "
            "per-page ceiling). When `page` is set, acts as the page size "
            "for that request."
        ),
    )
    page: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Page number (1-based). When set, returns a single page and "
            "disables auto-pagination; `limit` becomes the page size for "
            "that request."
        ),
    )

    # Domain filters
    order_no: str | None = Field(default=None, description="Filter by exact order_no")
    ids: CoercedIntListOpt = Field(
        default=None,
        description=(
            "Filter by explicit list of sales order IDs. "
            "JSON array of integers, e.g. [101, 202, 303]."
        ),
    )
    customer_id: int | None = Field(default=None, description="Filter by customer ID")
    location_id: int | None = Field(
        default=None,
        description=("Filter by location ID. Look up via `list_locations`."),
    )
    status: str | None = Field(
        default=None, description="Filter by sales order status (e.g. NOT_SHIPPED)"
    )
    production_status: str | None = Field(
        default=None,
        description="Filter by production status (NONE, NOT_STARTED, IN_PROGRESS, BLOCKED, DONE, NOT_APPLICABLE)",
    )
    invoicing_status: str | None = Field(
        default=None,
        description="Filter by invoicing status (e.g. NOT_INVOICED, INVOICED)",
    )
    currency: str | None = Field(
        default=None, description="Filter by currency code (e.g. 'USD')"
    )
    include_deleted: bool | None = Field(
        default=None,
        description="When true, include soft-deleted sales orders in the results.",
    )
    needs_work_orders: bool = Field(
        default=False,
        description="Convenience: filter to orders with production_status=NONE (no MOs created yet)",
    )

    # Time-window filters (server-side on Katana)
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

    # Time-window filters on delivery_date (applied as indexed SQL range
    # queries against the local cache post-#342).
    delivered_after: str | None = Field(
        default=None,
        description="ISO-8601 datetime lower bound on delivery_date.",
    )
    delivered_before: str | None = Field(
        default=None,
        description="ISO-8601 datetime upper bound on delivery_date.",
    )

    # Row inclusion
    include_rows: bool = Field(
        default=False,
        description=(
            "When true, populate row-level detail (id, variant_id, quantity, "
            "price_per_unit, linked_manufacturing_order_id) on each summary "
            "via the `rows` field. `sku` is not resolved in list context — "
            "use `get_sales_order` for SKU-enriched rows on a single order."
        ),
    )


class SalesOrderRowInfo(BaseModel):
    """Summary of a sales order line item."""

    id: int
    variant_id: int | None
    sku: str | None
    display_name: str | None = None
    """Katana-UI-format human-readable name lifted from the typed cache
    in a single batched IN-clause read (one query regardless of result-set
    size). ``None`` on cache miss; the list path stays cache-only by design
    so the variant must be present in ``CachedVariant`` for the field to
    populate. Matches the convention used by every other variant-displaying
    surface (search_items, check_inventory, recipe rows, verify card).
    """
    quantity: float | None
    price_per_unit: float | None
    linked_manufacturing_order_id: int | None


class SalesOrderSummary(BaseModel):
    """Summary row for a sales order in a list."""

    id: int
    order_no: str | None
    customer_id: int | None
    location_id: int | None
    status: str | None
    production_status: str | None
    invoicing_status: str | None
    created_at: str | None
    delivery_date: str | None
    total: float | None
    currency: str | None
    row_count: int
    rows: list[SalesOrderRowInfo] | None = None
    katana_url: str | None = None


class ListSalesOrdersResponse(BaseModel):
    """Response containing a list of sales orders."""

    orders: list[SalesOrderSummary]
    total_count: int
    pagination: PaginationMeta | None = Field(
        default=None,
        description=(
            "Pagination metadata — populated when the caller requests a "
            "specific `page`; `None` otherwise."
        ),
    )


_SALES_ORDER_DATE_FIELDS = (
    "created_after",
    "created_before",
    "updated_after",
    "updated_before",
    "delivered_after",
    "delivered_before",
)


def _apply_sales_order_filters(
    stmt: Any,
    request: ListSalesOrdersRequest,
    parsed_dates: dict[str, datetime | None],
) -> Any:
    """Translate request filters into WHERE clauses on a ``SalesOrder`` query.

    Shared by the data SELECT and the COUNT SELECT so pagination totals
    reflect exactly the same filter set as the data rows. ``parsed_dates``
    must come from :func:`parse_request_dates` — keeping parsing out of
    this function lets the paginated path avoid re-parsing on the COUNT
    query.
    """

    from katana_public_api_client.models_pydantic._generated import (
        CachedSalesOrder,
        SalesOrderProductionStatus,
        SalesOrderStatus,
    )

    production_status = request.production_status
    if production_status is None and request.needs_work_orders:
        production_status = "NONE"

    if request.order_no is not None:
        stmt = stmt.where(CachedSalesOrder.order_no == request.order_no)
    if request.ids is not None:
        stmt = stmt.where(CachedSalesOrder.id.in_(request.ids))
    if request.customer_id is not None:
        stmt = stmt.where(CachedSalesOrder.customer_id == request.customer_id)
    if request.location_id is not None:
        stmt = stmt.where(CachedSalesOrder.location_id == request.location_id)
    if request.status is not None:
        stmt = stmt.where(
            CachedSalesOrder.status
            == coerce_enum(request.status, SalesOrderStatus, "status")
        )
    if production_status is not None:
        stmt = stmt.where(
            CachedSalesOrder.production_status
            == coerce_enum(
                production_status, SalesOrderProductionStatus, "production_status"
            )
        )
    if request.invoicing_status is not None:
        stmt = stmt.where(CachedSalesOrder.invoicing_status == request.invoicing_status)
    if request.currency is not None:
        stmt = stmt.where(CachedSalesOrder.currency == request.currency)
    if not request.include_deleted:
        stmt = stmt.where(CachedSalesOrder.deleted_at.is_(None))

    return apply_date_window_filters(
        stmt,
        parsed_dates,
        ge_pairs={
            "created_after": CachedSalesOrder.created_at,
            "updated_after": CachedSalesOrder.updated_at,
            "delivered_after": CachedSalesOrder.delivery_date,
        },
        le_pairs={
            "created_before": CachedSalesOrder.created_at,
            "updated_before": CachedSalesOrder.updated_at,
            "delivered_before": CachedSalesOrder.delivery_date,
        },
    )


async def _list_sales_orders_impl(
    request: ListSalesOrdersRequest, context: Context
) -> ListSalesOrdersResponse:
    """List sales orders with filters via the typed cache.

    ``ensure_sales_orders_synced`` runs an incremental ``updated_at_min``
    delta (debounced — see :data:`_SYNC_DEBOUNCE`); the query then
    translates request filters into indexed SQL and returns results
    directly. See ADR-0018.
    """
    from sqlalchemy.orm import selectinload
    from sqlmodel import func, select

    from katana_mcp.typed_cache import ensure_sales_orders_synced
    from katana_public_api_client.models_pydantic._generated import (
        CachedSalesOrder,
        CachedSalesOrderRow,
    )

    services = get_services(context)

    await ensure_sales_orders_synced(services.client, services.typed_cache)

    parsed_dates = parse_request_dates(request, _SALES_ORDER_DATE_FIELDS)

    # When ``include_rows`` is set, ``selectinload`` eager-loads the
    # children, so ``len(so.sales_order_rows)`` is free at materialization
    # time and we skip the correlated COUNT subquery entirely. Both paths
    # filter ``deleted_at IS NULL`` so soft-deleted rows never surface
    # (see #803).
    if request.include_rows:
        stmt = select(CachedSalesOrder).options(
            selectinload(
                CachedSalesOrder.sales_order_rows.and_(
                    CachedSalesOrderRow.deleted_at.is_(None)
                )
            )
        )
    else:
        row_count_subq = (
            select(func.count(CachedSalesOrderRow.id))
            .where(CachedSalesOrderRow.sales_order_id == CachedSalesOrder.id)
            .where(CachedSalesOrderRow.deleted_at.is_(None))
            .correlate(CachedSalesOrder)
            .scalar_subquery()
            .label("row_count")
        )
        stmt = select(CachedSalesOrder, row_count_subq)
    stmt = _apply_sales_order_filters(stmt, request, parsed_dates)
    stmt = stmt.order_by(CachedSalesOrder.created_at.desc(), CachedSalesOrder.id.desc())
    if request.page is not None:
        stmt = stmt.offset((request.page - 1) * request.limit).limit(request.limit)
    else:
        stmt = stmt.limit(request.limit)

    async with services.typed_cache.session() as session:
        data_result = await session.exec(stmt)
        if request.include_rows:
            cached_orders = list(data_result.all())
            orders_with_counts: list[tuple[CachedSalesOrder, int]] = [
                (so, len(so.sales_order_rows)) for so in cached_orders
            ]
        else:
            orders_with_counts = data_result.all()

        pagination: PaginationMeta | None = None
        if request.page is not None:
            # Re-apply the same filter predicate to the COUNT so totals
            # never disagree with the data set.
            count_stmt = _apply_sales_order_filters(
                select(func.count()).select_from(CachedSalesOrder),
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

    # When ``include_rows`` is set, lift SKU + canonical display_name from
    # the typed cache in one batched IN-clause read. Adds one extra query
    # — much cheaper than the per-row API fallback the get path uses, and
    # keeps the ``ensure_sales_orders_synced`` cache-only win for everything
    # else.
    variant_lookup: dict[int, Any] = {}
    if request.include_rows:
        from katana_public_api_client.models_pydantic._generated import CachedVariant

        variant_ids = {
            r.variant_id
            for so, _ in orders_with_counts
            for r in so.sales_order_rows
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
        # Guard ``None`` lookups — keeps the dict-get type narrow and
        # avoids silently shadowing the empty-map default for rows that
        # legitimately carry ``variant_id=None``.
        vid = row.variant_id
        return variant_lookup.get(vid) if vid is not None else None

    orders: list[SalesOrderSummary] = []
    for so, row_count in orders_with_counts:
        row_infos: list[SalesOrderRowInfo] | None = None
        if request.include_rows:
            row_infos = [
                SalesOrderRowInfo(
                    id=r.id,
                    variant_id=r.variant_id,
                    sku=_row_attr(_variant_for_row(r), "sku"),
                    display_name=_row_attr(_variant_for_row(r), "display_name"),
                    quantity=r.quantity,
                    price_per_unit=float_or_none(r.price_per_unit),
                    linked_manufacturing_order_id=r.linked_manufacturing_order_id,
                )
                for r in so.sales_order_rows
            ]
        orders.append(
            SalesOrderSummary(
                id=so.id,
                order_no=so.order_no,
                customer_id=so.customer_id,
                location_id=so.location_id,
                status=enum_to_str(so.status),
                production_status=enum_to_str(so.production_status),
                invoicing_status=enum_to_str(so.invoicing_status),
                created_at=iso_or_none(so.created_at),
                delivery_date=iso_or_none(so.delivery_date),
                total=so.total,
                currency=so.currency,
                row_count=row_count,
                rows=row_infos,
                katana_url=katana_web_url("sales_order", so.id),
            )
        )

    return ListSalesOrdersResponse(
        orders=orders, total_count=len(orders), pagination=pagination
    )


@observe_tool
@unpack_pydantic_params
async def list_sales_orders(
    request: Annotated[ListSalesOrdersRequest, Unpack()], context: Context
) -> ToolResult:
    """List sales orders with filters — pass `ids=[1,2,3]` to fetch a specific batch by ID (cache-backed, indexed SQL).

    Use this for discovery workflows — find recent orders, orders needing work
    orders, orders for a specific customer, etc. Returns summary info (order_no,
    status, production_status, totals, row count).

    **Common filters:**
    - `needs_work_orders=true` — orders with no MOs yet (production_status=NONE)
    - `status="NOT_SHIPPED"` — unshipped orders
    - `customer_id=N` — orders for a specific customer

    **Time windows** — all applied as indexed SQL range queries against
    the local cache (post-#342 cache-back):
    - `created_after` / `created_before` — bounds on `created_at`
    - `updated_after` / `updated_before` — bounds on `updated_at`
    - `delivered_after` / `delivered_before` — bounds on `delivery_date`

    **Row detail:**
    - `include_rows=true` — populate per-order row details (id, variant_id,
      quantity, price_per_unit, linked_manufacturing_order_id). `sku` is left
      None in list context; use `get_sales_order` for SKU-enriched rows on a
      specific order.
    """
    response = await _list_sales_orders_impl(request, context)
    return make_json_result(response)


# ============================================================================
# Tool 3: get_sales_order
# ============================================================================


class GetSalesOrderRequest(BaseModel):
    """Request to look up a single sales order with line items."""

    model_config = ConfigDict(extra="forbid")

    order_no: str | None = Field(default=None, description="Sales order number")
    order_id: int | None = Field(default=None, description="Sales order ID")


class SalesOrderRowDetail(SoftDeletableResponse):
    """Full sales order row — every field on ``SalesOrderRow`` surfaced.

    Used inside ``GetSalesOrderResponse.rows`` where we want the exhaustive
    row-level detail. ``SalesOrderRowInfo`` (used by list_sales_orders) stays
    summary-shaped so the list tool remains compact.
    """

    id: int
    variant_id: int | None = None
    sku: str | None = None
    display_name: str | None = None
    """Katana-UI-format human-readable name for this row's variant.

    Lifted from the typed-cache ``CachedVariant.display_name`` column
    (built via :func:`build_variant_display_name`) so the rendered name
    stays consistent with every other variant-displaying surface. ``None``
    when the variant can't be resolved from the cache.
    """
    quantity: float | None = None
    sales_order_id: int | None = None
    tax_rate_id: int | None = None
    tax_rate: float | None = None
    location_id: int | None = None
    product_availability: str | None = None
    product_expected_date: str | None = None
    price_per_unit: float | None = None
    price_per_unit_in_base_currency: float | None = None
    total: float | None = None
    total_in_base_currency: float | None = None
    total_discount: str | None = None
    cogs_value: float | None = None
    linked_manufacturing_order_id: int | None = None
    conversion_rate: float | None = None
    conversion_date: str | None = None
    serial_numbers: list[int] = Field(
        default_factory=list,
        description="Serial number IDs allocated to this row.",
    )
    created_at: str | None = None
    updated_at: str | None = None


class SalesOrderAddressInfo(SoftDeletableResponse):
    """Full sales order address — one entry in ``GetSalesOrderResponse.addresses``.

    Mirrors every field on the ``SalesOrderAddress`` attrs model. The attrs
    field ``zip_`` is a Python keyword workaround; the wire format (and this
    Pydantic field) is ``zip``.
    """

    id: int
    sales_order_id: int | None = None
    entity_type: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    phone: str | None = None
    line_1: str | None = None
    line_2: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    country: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class SalesOrderShippingFeeInfo(BaseModel):
    """Shipping fee block — mirrors the ``SalesOrderShippingFee`` attrs model."""

    id: int
    sales_order_id: int | None = None
    amount: str | None = None
    tax_rate_id: int | None = None
    description: str | None = None


class GetSalesOrderResponse(SoftDeletableResponse):
    """Full sales order details. Exhaustive — every field Katana exposes on
    ``SalesOrder`` is surfaced (including nested rows, addresses, and
    shipping fee) so callers don't need follow-up lookups for standard fields.
    """

    # Identifiers / header
    id: int
    katana_url: str | None = None
    order_no: str | None = None
    customer_id: int | None = None
    location_id: int | None = None
    source: str | None = None
    order_created_date: str | None = None

    # Status / workflow
    status: str | None = None
    production_status: str | None = None
    invoicing_status: str | None = None
    product_availability: str | None = None
    product_expected_date: str | None = None
    ingredient_availability: str | None = None
    ingredient_expected_date: str | None = None

    # Dates
    delivery_date: str | None = None
    picked_date: str | None = None

    # Money
    currency: str | None = None
    total: float | None = None
    total_in_base_currency: float | None = None
    conversion_rate: float | None = None
    conversion_date: str | None = None

    # Notes / reference
    additional_info: str | None = None
    customer_ref: str | None = None

    # Tracking
    tracking_number: str | None = None
    tracking_number_url: str | None = None

    # Addresses — both the ID pointers on the SO and the full resolved list
    billing_address_id: int | None = None
    shipping_address_id: int | None = None
    addresses: list[SalesOrderAddressInfo] = Field(
        default_factory=list,
        description="Sales order addresses (billing and shipping).",
    )

    # Linked resources
    linked_manufacturing_order_id: int | None = None
    shipping_fee: SalesOrderShippingFeeInfo | None = None

    # Ecommerce metadata
    ecommerce_order_type: str | None = None
    ecommerce_store_name: str | None = None
    ecommerce_order_id: str | None = None

    # Timestamps
    created_at: str | None = None
    updated_at: str | None = None

    # Line items — exhaustive per-row detail
    rows: list[SalesOrderRowDetail] = Field(
        default_factory=list,
        description="Line items on the sales order.",
    )


def _shipping_fee_from_attrs(fee: Any) -> SalesOrderShippingFeeInfo | None:
    """Build a SalesOrderShippingFeeInfo from a populated attrs fee or None.

    Callers must pre-unwrap the attrs field (via ``unwrap_unset(obj.shipping_fee,
    None)``) so this helper only receives ``None`` or a populated object —
    passing the raw UNSET sentinel would AttributeError on ``.id``.

    Accepts both attrs ``SalesOrderShippingFee`` and a raw dict: the
    generated ``SalesOrder._parse_shipping_fee`` silently falls through to
    a raw dict cast as the union type when ``SalesOrderShippingFee.from_dict``
    raises (a quirk of openapi-python-client's oneOf codegen). When that
    happens, parse the dict via ``from_dict`` here; if even that fails
    (malformed payload), return ``None`` so the SO assembly completes
    rather than crashing with an opaque ``AttributeError`` (#501).
    """
    if fee is None:
        return None
    if isinstance(fee, dict):
        from katana_public_api_client.models import SalesOrderShippingFee

        try:
            fee = SalesOrderShippingFee.from_dict(fee)
        except (TypeError, ValueError, KeyError, AttributeError):
            return None
    return SalesOrderShippingFeeInfo(
        id=fee.id,
        sales_order_id=fee.sales_order_id,
        amount=unwrap_unset(fee.amount, None),
        tax_rate_id=unwrap_unset(fee.tax_rate_id, None),
        description=unwrap_unset(fee.description, None),
    )


async def _fetch_sales_order_addresses(
    services: Any, sales_order_id: int
) -> list[SalesOrderAddressInfo]:
    """Fetch all addresses for a sales order via /sales_order_addresses.

    SOs aren't cached today (per #342 they're transactional), so this is a
    fetch-on-demand call alongside the SO lookup. Returns the full list of
    addresses linked to ``sales_order_id``.
    """
    from katana_public_api_client.api.sales_order_address import (
        get_all_sales_order_addresses,
    )
    from katana_public_api_client.utils import unwrap_data

    response = await get_all_sales_order_addresses.asyncio_detailed(
        client=services.client,
        sales_order_ids=[sales_order_id],
        limit=250,
    )
    rows = unwrap_data(response, default=[])
    result: list[SalesOrderAddressInfo] = []
    for row in rows:
        row_dict = row.to_dict() if hasattr(row, "to_dict") else row
        # The attrs model uses ``zip_`` as a Python keyword workaround; the
        # API wire format is ``zip``. ``to_dict()`` emits the wire name.
        result.append(
            SalesOrderAddressInfo(
                id=row_dict.get("id", 0),
                sales_order_id=row_dict.get("sales_order_id"),
                entity_type=row_dict.get("entity_type"),
                first_name=row_dict.get("first_name"),
                last_name=row_dict.get("last_name"),
                company=row_dict.get("company"),
                phone=row_dict.get("phone"),
                line_1=row_dict.get("line_1"),
                line_2=row_dict.get("line_2"),
                city=row_dict.get("city"),
                state=row_dict.get("state"),
                zip=row_dict.get("zip"),
                country=row_dict.get("country"),
                # to_dict() has already serialized these to ISO strings;
                # iso_or_none expects datetime and would AttributeError.
                created_at=row_dict.get("created_at"),
                updated_at=row_dict.get("updated_at"),
                deleted_at=row_dict.get("deleted_at"),
            )
        )
    return result


async def _get_sales_order_impl(
    request: GetSalesOrderRequest, context: Context
) -> GetSalesOrderResponse:
    """Look up a single sales order by order_no or order_id with line items.

    Exhaustive response — every field Katana exposes on ``SalesOrder`` (plus
    nested rows, addresses, and shipping fee) is surfaced so callers don't
    need follow-up lookups for standard fields. SO is not cached today (#342
    covers the cache migration), so this keeps the same SO lookup path the
    prior impl used and adds a fetch-on-demand for addresses.
    """
    from katana_public_api_client.api.sales_order import (
        get_all_sales_orders,
        get_sales_order as api_get_sales_order,
    )
    from katana_public_api_client.models import SalesOrder
    from katana_public_api_client.utils import unwrap_as, unwrap_data

    if not request.order_no and not request.order_id:
        raise ValueError("Either order_no or order_id must be provided")

    services = get_services(context)

    if request.order_id:
        response = await api_get_sales_order.asyncio_detailed(
            id=request.order_id, client=services.client
        )
        so = unwrap_as(response, SalesOrder)
    else:
        if not request.order_no:
            raise ValueError("order_no is required when order_id is not provided")
        list_response = await get_all_sales_orders.asyncio_detailed(
            client=services.client, order_no=request.order_no, limit=1
        )
        orders = unwrap_data(list_response, default=[])
        if not orders:
            raise ValueError(f"Sales order '{request.order_no}' not found")
        so = orders[0]

    raw_rows = unwrap_unset(so.sales_order_rows, [])

    # One batched IN-clause SQLite read for all row variants, in parallel
    # with the address fetch — both depend only on the SO we just loaded.
    variant_ids = {
        v_id
        for v_id in (unwrap_unset(r.variant_id, None) for r in raw_rows)
        if v_id is not None
    }
    variants, addresses = await asyncio.gather(
        services.typed_cache.catalog.get_many_by_ids(
            CachedVariant, variant_ids, include_deleted=True
        ),
        _fetch_sales_order_addresses(services, so.id),
    )

    def _sku_for(v: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, dict):
            return v.get("sku")
        return getattr(v, "sku", None)

    def _display_name_for(v: Any) -> str | None:
        """Lift the typed cache's pre-computed display_name when available."""
        if v is None:
            return None
        if isinstance(v, dict):
            return v.get("display_name")
        return getattr(v, "display_name", None)

    row_details: list[SalesOrderRowDetail] = []
    for r in raw_rows:
        v_id = unwrap_unset(r.variant_id, None)
        variant = variants.get(v_id) if v_id is not None else None
        row_details.append(
            SalesOrderRowDetail(
                id=r.id,
                variant_id=v_id,
                sku=_sku_for(variant),
                display_name=_display_name_for(variant),
                quantity=unwrap_unset(r.quantity, None),
                sales_order_id=unwrap_unset(r.sales_order_id, None),
                tax_rate_id=unwrap_unset(r.tax_rate_id, None),
                tax_rate=unwrap_unset(r.tax_rate, None),
                location_id=unwrap_unset(r.location_id, None),
                product_availability=enum_to_str(
                    unwrap_unset(r.product_availability, None)
                ),
                product_expected_date=iso_or_none(
                    unwrap_unset(r.product_expected_date, None)
                ),
                price_per_unit=float_or_none(unwrap_unset(r.price_per_unit, None)),
                price_per_unit_in_base_currency=unwrap_unset(
                    r.price_per_unit_in_base_currency, None
                ),
                total=unwrap_unset(r.total, None),
                total_in_base_currency=unwrap_unset(r.total_in_base_currency, None),
                total_discount=unwrap_unset(r.total_discount, None),
                cogs_value=float_or_none(unwrap_unset(r.cogs_value, None)),
                linked_manufacturing_order_id=unwrap_unset(
                    r.linked_manufacturing_order_id, None
                ),
                conversion_rate=unwrap_unset(r.conversion_rate, None),
                conversion_date=iso_or_none(unwrap_unset(r.conversion_date, None)),
                serial_numbers=unwrap_unset(r.serial_numbers, []),
                created_at=iso_or_none(unwrap_unset(r.created_at, None)),
                updated_at=iso_or_none(unwrap_unset(r.updated_at, None)),
                deleted_at=iso_or_none(unwrap_unset(r.deleted_at, None)),
            )
        )

    return GetSalesOrderResponse(
        id=so.id,
        katana_url=katana_web_url("sales_order", so.id),
        order_no=unwrap_unset(so.order_no, None),
        customer_id=unwrap_unset(so.customer_id, None),
        location_id=unwrap_unset(so.location_id, None),
        source=unwrap_unset(so.source, None),
        order_created_date=iso_or_none(unwrap_unset(so.order_created_date, None)),
        status=enum_to_str(unwrap_unset(so.status, None)),
        production_status=enum_to_str(unwrap_unset(so.production_status, None)),
        invoicing_status=enum_to_str(unwrap_unset(so.invoicing_status, None)),
        product_availability=enum_to_str(unwrap_unset(so.product_availability, None)),
        product_expected_date=iso_or_none(unwrap_unset(so.product_expected_date, None)),
        ingredient_availability=enum_to_str(
            unwrap_unset(so.ingredient_availability, None)
        ),
        ingredient_expected_date=iso_or_none(
            unwrap_unset(so.ingredient_expected_date, None)
        ),
        delivery_date=iso_or_none(unwrap_unset(so.delivery_date, None)),
        picked_date=iso_or_none(unwrap_unset(so.picked_date, None)),
        currency=unwrap_unset(so.currency, None),
        total=unwrap_unset(so.total, None),
        total_in_base_currency=unwrap_unset(so.total_in_base_currency, None),
        conversion_rate=unwrap_unset(so.conversion_rate, None),
        conversion_date=iso_or_none(unwrap_unset(so.conversion_date, None)),
        additional_info=unwrap_unset(so.additional_info, None),
        customer_ref=unwrap_unset(so.customer_ref, None),
        tracking_number=unwrap_unset(so.tracking_number, None),
        tracking_number_url=unwrap_unset(so.tracking_number_url, None),
        billing_address_id=unwrap_unset(so.billing_address_id, None),
        shipping_address_id=unwrap_unset(so.shipping_address_id, None),
        addresses=addresses,
        linked_manufacturing_order_id=unwrap_unset(
            so.linked_manufacturing_order_id, None
        ),
        shipping_fee=_shipping_fee_from_attrs(unwrap_unset(so.shipping_fee, None)),
        ecommerce_order_type=unwrap_unset(so.ecommerce_order_type, None),
        ecommerce_store_name=unwrap_unset(so.ecommerce_store_name, None),
        ecommerce_order_id=unwrap_unset(so.ecommerce_order_id, None),
        created_at=iso_or_none(unwrap_unset(so.created_at, None)),
        updated_at=iso_or_none(unwrap_unset(so.updated_at, None)),
        deleted_at=iso_or_none(unwrap_unset(so.deleted_at, None)),
        rows=row_details,
    )


@observe_tool
@unpack_pydantic_params
async def get_sales_order(
    request: Annotated[GetSalesOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Look up a sales order by number or ID with all line items.

    For multiple sales orders at once, use ``list_sales_orders(ids=[...])`` —
    it returns a summary table and supports all the same filters.

    Returns every field Katana exposes on the sales order record — identity,
    status/workflow flags, dates, totals, tracking, ecommerce metadata,
    timestamps — plus the full list of associated billing/shipping addresses
    (fetched on-demand via /sales_order_addresses, since SOs aren't cached)
    and exhaustive per-row detail (variant, SKU via variant cache, pricing,
    linked manufacturing order, batch tracking, serial numbers). Use with
    `list_sales_orders` for discovery; this is the single-call path to the rest.
    """
    response = await _get_sales_order_impl(request, context)
    return make_json_result(response)


# ============================================================================
# Tool: modify_sales_order — unified modification surface
# ============================================================================


class SOOperation(StrEnum):
    """Operation names emitted on ActionSpecs by ``modify_sales_order`` /
    ``delete_sales_order`` plan builders.
    """

    UPDATE_HEADER = "update_header"
    DELETE = "delete"
    ADD_ROW = "add_row"
    UPDATE_ROW = "update_row"
    DELETE_ROW = "delete_row"
    ADD_ADDRESS = "add_address"
    UPDATE_ADDRESS = "update_address"
    DELETE_ADDRESS = "delete_address"
    ADD_FULFILLMENT = "add_fulfillment"
    UPDATE_FULFILLMENT = "update_fulfillment"
    DELETE_FULFILLMENT = "delete_fulfillment"
    ADD_SHIPPING_FEE = "add_shipping_fee"
    UPDATE_SHIPPING_FEE = "update_shipping_fee"
    DELETE_SHIPPING_FEE = "delete_shipping_fee"


# Tool-facing literals — values match the API StrEnum's ``.value`` directly,
# so ``EnumClass(literal)`` resolves the enum without a lookup table.
SalesOrderStatusLiteral = Literal["NOT_SHIPPED", "PENDING", "PACKED", "DELIVERED"]
FulfillmentStatusLiteral = Literal["DELIVERED", "PACKED"]
AddressEntityTypeLiteral = Literal["billing", "shipping"]


# ----------------------------------------------------------------------------
# Diff-context fetchers
# ----------------------------------------------------------------------------


async def _fetch_sales_order_attrs(services: Any, so_id: int) -> SalesOrder | None:
    return await safe_fetch_for_diff(
        api_get_sales_order, services, so_id, return_type=SalesOrder, label="SO"
    )


async def _fetch_so_row(services: Any, row_id: int) -> SalesOrderRow | None:
    return await safe_fetch_for_diff(
        api_get_so_row, services, row_id, return_type=SalesOrderRow, label="SO row"
    )


async def _fetch_so_row_attrs_for_merge(
    services: Any, sales_order_id: int
) -> list[Any]:
    """Return raw attrs ``SalesOrderRow`` list for the cache merge fan-out.

    Same rationale as the PO row fetcher: Katana hides soft-deleted SO
    rows from the parent fetch even with ``include_deleted=true`` at
    the parent level. The sibling ``/sales_order_rows`` endpoint
    exposes ``include_deleted`` for its own scope, so the typed-cache
    schema syncs rows independently to catch tombstones (see
    ``_SALES_ORDER_ROW_SPEC`` in ``typed_cache/sync.py``). Wire this
    into ``CacheMerge.refetch_related`` so ``modify_sales_order`` row
    deletions write through to the cache immediately.
    """
    from katana_public_api_client.api.sales_order_row import (
        get_all_sales_order_rows,
    )
    from katana_public_api_client.utils import unwrap_data

    response = await get_all_sales_order_rows.asyncio_detailed(
        client=services.client,
        sales_order_ids=[sales_order_id],
        include_deleted=True,
        limit=250,
    )
    return unwrap_data(response, default=[])


async def _fetch_so_fulfillment(
    services: Any, fulfillment_id: int
) -> SalesOrderFulfillment | None:
    return await safe_fetch_for_diff(
        api_get_so_fulfillment,
        services,
        fulfillment_id,
        return_type=SalesOrderFulfillment,
        label="SO fulfillment",
    )


async def _fetch_so_shipping_fee(
    services: Any, fee_id: int
) -> SalesOrderShippingFee | None:
    return await safe_fetch_for_diff(
        api_get_so_shipping_fee,
        services,
        fee_id,
        return_type=SalesOrderShippingFee,
        label="SO shipping fee",
    )


# Note: addresses do not have a get-by-id endpoint (only list-by-SO). Updates
# go through with ``unknown_prior=True`` since we can't cheaply fetch one row.


# ----------------------------------------------------------------------------
# Sub-payload models (typed slots on ModifySalesOrderRequest)
# ----------------------------------------------------------------------------


class SOHeaderPatch(BaseModel):
    """Header fields to patch on an SO. Status is included here — the Katana
    PATCH endpoint accepts it as a regular field."""

    model_config = ConfigDict(extra="forbid")

    order_no: str | None = Field(default=None, description="New SO number")
    customer_id: int | None = Field(default=None, description="New customer ID")
    location_id: int | None = Field(
        default=None,
        description=("New location ID. Look up via `list_locations`."),
    )
    status: SalesOrderStatusLiteral | None = Field(
        default=None,
        description="New status — NOT_SHIPPED / PENDING / PACKED / DELIVERED",
    )
    currency: str | None = Field(default=None, description="New currency code")
    conversion_rate: float | None = Field(
        default=None, description="New currency conversion rate"
    )
    conversion_date: str | None = Field(
        default=None, description="New conversion date (ISO-8601)"
    )
    order_created_date: WireDatetime | None = Field(
        default=None,
        description=(
            "New order created date — ISO 8601 date or datetime "
            "(e.g. '2026-05-08T14:30:00Z' or '2026-05-08T14:30:00-08:00'). "
            "Naive datetimes (no timezone) are interpreted as UTC."
        ),
    )
    delivery_date: WireDatetime | None = Field(
        default=None,
        description=(
            "New delivery date — ISO 8601 date or datetime "
            "(e.g. '2026-05-08T14:30:00Z' or '2026-05-08T14:30:00-08:00'). "
            "Naive datetimes (no timezone) are interpreted as UTC."
        ),
    )
    picked_date: WireDatetime | None = Field(
        default=None,
        description=(
            "New picked date — ISO 8601 date or datetime "
            "(e.g. '2026-05-08T14:30:00Z' or '2026-05-08T14:30:00-08:00'). "
            "Naive datetimes (no timezone) are interpreted as UTC."
        ),
    )
    additional_info: str | None = Field(
        default=None, description="New notes / additional info"
    )
    customer_ref: str | None = Field(default=None, description="New customer reference")
    tracking_number: str | None = Field(default=None, description="Tracking number")
    tracking_number_url: str | None = Field(default=None, description="Tracking URL")


class SORowAdd(BaseModel):
    """A new line item to add to the SO."""

    model_config = ConfigDict(extra="forbid")

    variant_id: int = Field(..., description="Variant ID")
    quantity: float = Field(..., description="Quantity", gt=0)
    price_per_unit: float | None = Field(default=None, description="Unit price")
    tax_rate_id: int | None = Field(
        default=None,
        description=("Tax rate ID. Look up via `list_tax_rates`."),
    )
    location_id: int | None = Field(
        default=None,
        description=("Location ID. Look up via `list_locations`."),
    )
    total_discount: float | None = Field(default=None, description="Total discount")


class SORowUpdate(BaseModel):
    """Patch to an existing SO row."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Row ID to update")
    variant_id: int | None = Field(default=None, description="New variant ID")
    quantity: float | None = Field(default=None, description="New quantity", gt=0)
    price_per_unit: float | None = Field(default=None, description="New unit price")
    tax_rate_id: int | None = Field(
        default=None,
        description=("New tax rate ID. Look up via `list_tax_rates`."),
    )
    location_id: int | None = Field(
        default=None,
        description=("New location ID. Look up via `list_locations`."),
    )
    total_discount: float | None = Field(default=None, description="New discount")


class SOAddressAdd(BaseModel):
    """A new address to attach to the SO."""

    model_config = ConfigDict(extra="forbid")

    entity_type: AddressEntityTypeLiteral = Field(
        ..., description="Address kind — billing or shipping"
    )
    first_name: str | None = Field(default=None, description="Recipient first name")
    last_name: str | None = Field(default=None, description="Recipient last name")
    company: str | None = Field(default=None, description="Company name")
    city: str | None = Field(default=None, description="City")
    state: str | None = Field(default=None, description="State or region")
    zip: str | None = Field(default=None, description="Postal/ZIP code")
    country: str | None = Field(
        default=None,
        description="Country (ISO 3166 name or two-letter code, e.g. 'US', 'United States')",
    )
    phone: str | None = Field(default=None, description="Contact phone number")


class SOAddressUpdate(BaseModel):
    """Patch to an existing SO address. Address get-by-id isn't exposed by
    the Katana API, so previews show every supplied field as
    ``is_unknown_prior=True`` — we can't read the prior values cheaply."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Address ID to update")
    first_name: str | None = Field(default=None, description="New recipient first name")
    last_name: str | None = Field(default=None, description="New recipient last name")
    company: str | None = Field(default=None, description="New company name")
    city: str | None = Field(default=None, description="New city")
    state: str | None = Field(default=None, description="New state or region")
    zip: str | None = Field(default=None, description="New postal/ZIP code")
    country: str | None = Field(
        default=None,
        description="New country (ISO 3166 name or two-letter code)",
    )
    phone: str | None = Field(default=None, description="New contact phone number")


class SOFulfillmentRowInput(BaseModel):
    """A row inside a fulfillment — references an SO row + a quantity to fulfill."""

    model_config = ConfigDict(extra="forbid")

    sales_order_row_id: int = Field(..., description="SO row being fulfilled")
    quantity: float = Field(..., description="Quantity fulfilled", gt=0)


class SOFulfillmentAdd(BaseModel):
    """A new fulfillment for the SO."""

    model_config = ConfigDict(extra="forbid")

    status: FulfillmentStatusLiteral = Field(
        ..., description="Fulfillment status — DELIVERED or PACKED"
    )
    sales_order_fulfillment_rows: list[SOFulfillmentRowInput] = Field(
        ..., description="Rows being fulfilled (variant + quantity)", min_length=1
    )
    picked_date: WireDatetime | None = Field(
        default=None,
        description=(
            "When items were picked — ISO 8601 date or datetime "
            "(e.g. '2026-05-08T14:30:00Z' or '2026-05-08T14:30:00-08:00'). "
            "Naive datetimes (no timezone) are interpreted as UTC."
        ),
    )
    conversion_rate: float | None = Field(
        default=None,
        description="Currency conversion rate applied to the fulfillment",
    )
    conversion_date: WireDatetime | None = Field(
        default=None,
        description=(
            "Conversion-rate fix date — ISO 8601 date or datetime "
            "(e.g. '2026-05-08T14:30:00Z' or '2026-05-08T14:30:00-08:00'). "
            "Naive datetimes (no timezone) are interpreted as UTC."
        ),
    )
    tracking_number: str | None = Field(
        default=None, description="Carrier tracking number"
    )
    tracking_url: str | None = Field(default=None, description="Carrier tracking URL")
    tracking_carrier: str | None = Field(
        default=None, description="Carrier name (e.g., UPS, FedEx, USPS)"
    )
    tracking_method: str | None = Field(
        default=None, description="Shipping method (e.g., Ground, Express, 2-Day)"
    )


class SOFulfillmentUpdate(BaseModel):
    """Patch to an existing SO fulfillment."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Fulfillment ID to update")
    status: FulfillmentStatusLiteral | None = Field(
        default=None,
        description="New fulfillment status — DELIVERED or PACKED",
    )
    picked_date: WireDatetime | None = Field(
        default=None,
        description=(
            "New picked date — ISO 8601 date or datetime "
            "(e.g. '2026-05-08T14:30:00Z' or '2026-05-08T14:30:00-08:00'). "
            "Naive datetimes (no timezone) are interpreted as UTC."
        ),
    )
    packer_id: int | None = Field(
        default=None,
        description=("New packer (operator). Look up via `list_operators`."),
    )
    conversion_rate: float | None = Field(
        default=None, description="New currency conversion rate"
    )
    conversion_date: WireDatetime | None = Field(
        default=None,
        description=(
            "New conversion-rate fix date — ISO 8601 date or datetime "
            "(e.g. '2026-05-08T14:30:00Z' or '2026-05-08T14:30:00-08:00'). "
            "Naive datetimes (no timezone) are interpreted as UTC."
        ),
    )
    tracking_number: str | None = Field(
        default=None, description="New carrier tracking number"
    )
    tracking_url: str | None = Field(
        default=None, description="New carrier tracking URL"
    )
    tracking_carrier: str | None = Field(
        default=None, description="New carrier name (e.g., UPS, FedEx, USPS)"
    )
    tracking_method: str | None = Field(
        default=None,
        description="New shipping method (e.g., Ground, Express, 2-Day)",
    )


class ModifySalesOrderRequest(ConfirmableRequest):
    """Unified modification request for a sales order.

    Sub-payload slots span header + rows + addresses + fulfillments +
    shipping fees. Multiple slots can be combined; actions execute in
    canonical order. To remove the SO entirely, use ``delete_sales_order``.
    """

    id: int = Field(..., description="Sales order ID")
    update_header: SOHeaderPatch | None = Field(
        default=None,
        description=(
            "Header-level patch. Fields: order_no, customer_id, location_id, "
            "status (NOT_SHIPPED/PENDING/PACKED/DELIVERED), currency, "
            "conversion_rate, conversion_date, order_created_date, "
            "delivery_date, picked_date, additional_info, customer_ref, "
            "tracking_number, tracking_number_url."
        ),
    )
    add_rows: list[SORowAdd] | None = Field(
        default=None,
        description=(
            "New line items. Each row: variant_id (int, required), quantity "
            "(float, required, >0), price_per_unit, tax_rate_id (see "
            "`list_tax_rates`), location_id, total_discount."
        ),
    )
    update_rows: list[SORowUpdate] | None = Field(
        default=None,
        description=(
            "Patches to existing line items. Each entry: id (int, required) + "
            "any subset of variant_id, quantity, price_per_unit, tax_rate_id, "
            "location_id, total_discount."
        ),
    )
    delete_row_ids: list[int] | None = Field(
        default=None,
        description="Row IDs to delete from the SO.",
    )
    add_addresses: list[SOAddressAdd] | None = Field(
        default=None,
        description=(
            "New addresses. Each: entity_type (billing | shipping, required), "
            "first_name, last_name, company, city, state, zip, country, phone."
        ),
    )
    update_addresses: list[SOAddressUpdate] | None = Field(
        default=None,
        description=(
            "Patches to existing addresses. Each entry: id (int, required) + "
            "any subset of first_name, last_name, company, city, state, zip, "
            "country, phone. Katana doesn't expose address get-by-id, so "
            "previews mark every supplied field as is_unknown_prior=True."
        ),
    )
    delete_address_ids: list[int] | None = Field(
        default=None,
        description="Address IDs to delete from the SO.",
    )
    add_fulfillments: list[SOFulfillmentAdd] | None = Field(
        default=None,
        description=(
            "New fulfillments. Each: status (DELIVERED | PACKED, required), "
            "sales_order_fulfillment_rows (list of {sales_order_row_id, "
            "quantity}, required, min_length=1), picked_date, "
            "conversion_rate, conversion_date, tracking_number, tracking_url, "
            "tracking_carrier, tracking_method."
        ),
    )
    update_fulfillments: list[SOFulfillmentUpdate] | None = Field(
        default=None,
        description=(
            "Patches to existing fulfillments. Each entry: id (int, "
            "required) + any subset of status, picked_date, packer_id "
            "(operator — see `list_operators`), conversion_rate, "
            "conversion_date, tracking_number, tracking_url, "
            "tracking_carrier, tracking_method."
        ),
    )
    delete_fulfillment_ids: list[int] | None = Field(
        default=None,
        description="Fulfillment IDs to delete from the SO.",
    )
    add_shipping_fees: list[SOShippingFeeAdd] | None = Field(
        default=None,
        description=(
            "New shipping fees. Each: amount (decimal string, required), "
            "description, tax_rate_id (see `list_tax_rates`)."
        ),
    )
    update_shipping_fees: list[SOShippingFeeUpdate] | None = Field(
        default=None,
        description=(
            "Patches to existing shipping fees. Each entry: id (int, "
            "required), amount (decimal string, required — Katana semantics "
            "are replace, not partial), description, tax_rate_id."
        ),
    )
    delete_shipping_fee_ids: list[int] | None = Field(
        default=None,
        description="Shipping fee IDs to delete from the SO.",
    )


class DeleteSalesOrderRequest(ConfirmableRequest):
    """Delete a sales order. Destructive — Katana cascades child rows /
    addresses / fulfillments / shipping fees server-side.
    """

    id: int = Field(..., description="Sales order ID to delete")


# ----------------------------------------------------------------------------
# API request builders — pure data shaping per sub-payload kind.
# ----------------------------------------------------------------------------


def _build_update_header_request(patch: SOHeaderPatch) -> APIUpdateSalesOrderRequest:
    return APIUpdateSalesOrderRequest(
        **unset_dict(patch, transforms={"status": UpdateSalesOrderStatus})
    )


def _build_create_row_request(so_id: int, row: SORowAdd) -> APICreateSORowRequest:
    return APICreateSORowRequest(sales_order_id=so_id, **unset_dict(row))


def _build_update_row_request(patch: SORowUpdate) -> APIUpdateSORowRequest:
    return APIUpdateSORowRequest(**unset_dict(patch, exclude=("id",)))


def _build_create_address_request(
    so_id: int, addr: SOAddressAdd
) -> APICreateSOAddressRequest:
    return APICreateSOAddressRequest(
        sales_order_id=so_id,
        **unset_dict(
            addr,
            field_map={"zip": "zip_"},
            transforms={"entity_type": AddressEntityType},
        ),
    )


def _build_update_address_request(
    patch: SOAddressUpdate,
) -> APIUpdateSOAddressRequest:
    return APIUpdateSOAddressRequest(
        **unset_dict(patch, exclude=("id",), field_map={"zip": "zip_"})
    )


def _build_create_fulfillment_request(
    so_id: int, fulfillment: SOFulfillmentAdd
) -> APICreateSOFulfillmentRequest:
    rows = [
        SalesOrderFulfillmentRowRequest(
            sales_order_row_id=r.sales_order_row_id, quantity=r.quantity
        )
        for r in fulfillment.sales_order_fulfillment_rows
    ]
    return APICreateSOFulfillmentRequest(
        sales_order_id=so_id,
        sales_order_fulfillment_rows=rows,
        **unset_dict(
            fulfillment,
            exclude=("sales_order_fulfillment_rows",),
            transforms={"status": SalesOrderFulfillmentStatus},
        ),
    )


def _build_update_fulfillment_request(
    patch: SOFulfillmentUpdate,
) -> APIUpdateSOFulfillmentRequest:
    return APIUpdateSOFulfillmentRequest(
        **unset_dict(
            patch,
            exclude=("id",),
            transforms={"status": SalesOrderFulfillmentStatus},
        )
    )


def _build_create_shipping_fee_request(
    so_id: int, fee: SOShippingFeeAdd
) -> APICreateSOShippingFeeRequest:
    return APICreateSOShippingFeeRequest(sales_order_id=so_id, **unset_dict(fee))


def _build_update_shipping_fee_request(
    patch: SOShippingFeeUpdate,
) -> APIUpdateSOShippingFeeRequest:
    return APIUpdateSOShippingFeeRequest(**unset_dict(patch, exclude=("id",)))


# ----------------------------------------------------------------------------
# Implementations
# ----------------------------------------------------------------------------


async def _modify_sales_order_impl(
    request: ModifySalesOrderRequest, context: Context
) -> ModificationResponse:
    """Build the action plan from the request's sub-payloads and either
    preview or execute based on ``preview``."""
    services = get_services(context)

    if not has_any_subpayload(request):
        raise ValueError(
            "At least one sub-payload must be set: update_header, "
            "add/update/delete_rows, add/update/delete_addresses, "
            "add/update/delete_fulfillments, or "
            "add/update/delete_shipping_fees. To remove the SO entirely, "
            "use delete_sales_order."
        )

    existing_so = await _fetch_sales_order_attrs(services, request.id)

    plan: list[ActionSpec] = []

    # Header — single optional patch.
    if request.update_header is not None:
        diff = compute_field_diff(
            existing_so, request.update_header, unknown_prior=existing_so is None
        )
        plan.append(
            ActionSpec(
                operation=SOOperation.UPDATE_HEADER,
                target_id=request.id,
                diff=diff,
                apply=make_patch_apply(
                    api_update_sales_order,
                    services,
                    request.id,
                    _build_update_header_request(request.update_header),
                    return_type=SalesOrder,
                ),
                verify=make_response_verifier(diff),
            )
        )

    # Rows.
    plan.extend(
        plan_creates(
            request.add_rows,
            SOOperation.ADD_ROW,
            lambda row: _build_create_row_request(request.id, row),
            lambda body: make_post_apply(
                api_create_so_row, services, body, return_type=SalesOrderRow
            ),
        )
    )
    plan.extend(
        await plan_updates(
            request.update_rows,
            SOOperation.UPDATE_ROW,
            lambda rid: _fetch_so_row(services, rid),
            _build_update_row_request,
            lambda rid, body: make_patch_apply(
                api_update_so_row, services, rid, body, return_type=SalesOrderRow
            ),
        )
    )
    plan.extend(
        plan_deletes(
            request.delete_row_ids,
            SOOperation.DELETE_ROW,
            lambda rid: make_delete_apply(api_delete_so_row, services, rid),
        )
    )

    # Addresses. Updates have no get-by-id endpoint, so fetcher is None
    # (every diff marks ``is_unknown_prior=True``).
    plan.extend(
        plan_creates(
            request.add_addresses,
            SOOperation.ADD_ADDRESS,
            lambda addr: _build_create_address_request(request.id, addr),
            lambda body: make_post_apply(
                api_create_so_address, services, body, return_type=APISalesOrderAddress
            ),
        )
    )
    plan.extend(
        await plan_updates(
            request.update_addresses,
            SOOperation.UPDATE_ADDRESS,
            None,  # no get-by-id endpoint
            _build_update_address_request,
            lambda aid, body: make_patch_apply(
                api_update_so_address,
                services,
                aid,
                body,
                return_type=APISalesOrderAddress,
            ),
        )
    )
    plan.extend(
        plan_deletes(
            request.delete_address_ids,
            SOOperation.DELETE_ADDRESS,
            lambda aid: make_delete_apply(api_delete_so_address, services, aid),
        )
    )

    # Fulfillments.
    plan.extend(
        plan_creates(
            request.add_fulfillments,
            SOOperation.ADD_FULFILLMENT,
            lambda fulfillment: _build_create_fulfillment_request(
                request.id, fulfillment
            ),
            lambda body: make_post_apply(
                api_create_so_fulfillment,
                services,
                body,
                return_type=SalesOrderFulfillment,
            ),
        )
    )
    plan.extend(
        await plan_updates(
            request.update_fulfillments,
            SOOperation.UPDATE_FULFILLMENT,
            lambda fid: _fetch_so_fulfillment(services, fid),
            _build_update_fulfillment_request,
            lambda fid, body: make_patch_apply(
                api_update_so_fulfillment,
                services,
                fid,
                body,
                return_type=SalesOrderFulfillment,
            ),
        )
    )
    plan.extend(
        plan_deletes(
            request.delete_fulfillment_ids,
            SOOperation.DELETE_FULFILLMENT,
            lambda fid: make_delete_apply(api_delete_so_fulfillment, services, fid),
        )
    )

    # Shipping fees.
    plan.extend(
        plan_creates(
            request.add_shipping_fees,
            SOOperation.ADD_SHIPPING_FEE,
            lambda fee: _build_create_shipping_fee_request(request.id, fee),
            lambda body: make_post_apply(
                api_create_so_shipping_fee,
                services,
                body,
                return_type=SalesOrderShippingFee,
            ),
        )
    )
    plan.extend(
        await plan_updates(
            request.update_shipping_fees,
            SOOperation.UPDATE_SHIPPING_FEE,
            lambda fid: _fetch_so_shipping_fee(services, fid),
            _build_update_shipping_fee_request,
            lambda fid, body: make_patch_apply(
                api_update_so_shipping_fee,
                services,
                fid,
                body,
                return_type=SalesOrderShippingFee,
            ),
        )
    )
    plan.extend(
        plan_deletes(
            request.delete_shipping_fee_ids,
            SOOperation.DELETE_SHIPPING_FEE,
            lambda fid: make_delete_apply(api_delete_so_shipping_fee, services, fid),
        )
    )

    response = await run_modify_plan(
        request=request,
        naming=EntityNaming(
            entity_type="sales_order",
            entity_label=f"sales order {request.id}",
            tool_name="modify_sales_order",
        ),
        web_url_kind="sales_order",
        existing=existing_so,
        plan=plan,
        cache_merge=CacheMerge(
            cache=services.typed_cache,
            refetch_for_merge=lambda eid: _fetch_sales_order_attrs(services, eid),
            # Soft-deleted rows are hidden from the parent fetch even
            # with ``include_deleted=true`` (parent-scope only). Fan
            # out to the sibling ``/sales_order_rows`` endpoint with
            # ``include_deleted=True`` to catch tombstones — mirrors
            # ``_SALES_ORDER_ROW_SPEC``'s row-watermark rationale.
            refetch_related=(
                (
                    "sales_order_row",
                    lambda eid: _fetch_so_row_attrs_for_merge(services, eid),
                ),
            ),
        ),
    )

    # Apply-path: synthesize NOT-RUN entries for the unattempted plan tail.
    # ``execute_plan`` is fail-fast: ``response.actions`` ends at the first
    # failed action. Without these synthetic entries the modify card's
    # per-section row morph would silently HIDE every planned action past
    # the failure — the operator would see "1 succeeded, 1 failed" with
    # no indication that 3 more actions were never attempted. Mirror
    # ``_modify_product_bom_impl``'s NOT RUN pattern (#811): emit one
    # entry per leftover ``ActionSpec`` with ``status_label="NOT RUN"``
    # and ``succeeded=None`` (so per-row chrome renders the "secondary"
    # Badge variant via :data:`_SO_SUB_STATUS_VARIANTS`). The renderer
    # picks them up via ``response.extras["not_run_actions"]`` and merges
    # them into the per-section row bucketing in
    # :func:`build_so_modify_ui` — #858 finding B.
    if not response.is_preview:
        not_run_specs = plan[len(response.actions) :]
        not_run_actions = [
            {
                "operation": spec.operation,
                "target_id": spec.target_id,
                "succeeded": None,
                "error": None,
                "changes": [
                    c.model_dump() if hasattr(c, "model_dump") else dict(c)
                    for c in spec.diff
                ],
                "status_label": "NOT RUN",
            }
            for spec in not_run_specs
        ]
        if not_run_actions:
            response.extras["not_run_actions"] = not_run_actions
    return response


@observe_tool
@unpack_pydantic_params
async def modify_sales_order(
    request: Annotated[ModifySalesOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Modify a sales order — unified surface across header, rows, addresses,
    fulfillments, and shipping fees.

    Sub-payloads (any subset, all optional):

    - ``update_header`` — patch header fields (incl. status)
    - ``add_rows`` / ``update_rows`` / ``delete_row_ids`` — line item CRUD
    - ``add_addresses`` / ``update_addresses`` / ``delete_address_ids`` —
      billing/shipping addresses
    - ``add_fulfillments`` / ``update_fulfillments`` / ``delete_fulfillment_ids`` —
      fulfillments (each carries its own status + tracking)
    - ``add_shipping_fees`` / ``update_shipping_fees`` /
      ``delete_shipping_fee_ids`` — shipping/freight charges

    To remove an SO entirely, use the sibling ``delete_sales_order`` tool.

    Two-step flow: ``preview=true`` (default) returns a per-action preview;
    ``preview=false`` executes the plan in canonical order. Fail-fast on
    error; per-action ``verified`` reflects post-execution re-fetch
    confirmation (when supported by the resource).

    The response carries a ``prior_state`` snapshot of the pre-modification
    SO. Note: address updates can't be diffed pre-execution because Katana
    doesn't expose a per-address GET; their previews show every supplied
    field as ``(prior unknown) → new``.
    """
    response = await _modify_sales_order_impl(request, context)
    return to_tool_result(
        response, confirm_request=request, confirm_tool="modify_sales_order"
    )


# ============================================================================
# Tool: delete_sales_order
# ============================================================================


async def _delete_sales_order_impl(
    request: DeleteSalesOrderRequest, context: Context
) -> ModificationResponse:
    """One-action plan that removes the SO. Katana cascades child rows,
    addresses, fulfillments, and shipping fees server-side."""
    return await run_delete_plan(
        request=request,
        services=get_services(context),
        entity_type="sales_order",
        entity_label=f"sales order {request.id}",
        web_url_kind="sales_order",
        fetcher=_fetch_sales_order_attrs,
        delete_endpoint=api_delete_sales_order,
        operation=SOOperation.DELETE,
    )


@observe_tool
@unpack_pydantic_params
async def delete_sales_order(
    request: Annotated[DeleteSalesOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Delete a sales order. Destructive — Katana cascades the delete to
    child rows / addresses / fulfillments / shipping fees server-side.

    The response carries a ``prior_state`` snapshot for manual revert.
    """
    response = await _delete_sales_order_impl(request, context)
    return to_tool_result(
        response, confirm_request=request, confirm_tool="delete_sales_order"
    )


def register_tools(mcp: FastMCP) -> None:
    """Register all sales order tools with the FastMCP instance.

    Args:
        mcp: FastMCP server instance to register tools with
    """
    from mcp.types import ToolAnnotations

    from katana_mcp.tools.prefab_ui import register_preview_tool

    _read = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )

    _create = ToolAnnotations(
        readOnlyHint=False, destructiveHint=False, openWorldHint=True
    )
    _modify = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
        openWorldHint=True,
    )
    _destructive = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
        openWorldHint=True,
    )

    register_preview_tool(
        mcp,
        create_sales_order,
        tags={"orders", "sales", "write"},
        annotations=_create,
        meta=UI_META,
    )
    mcp.tool(tags={"orders", "sales", "read"}, annotations=_read)(list_sales_orders)
    mcp.tool(tags={"orders", "sales", "read"}, annotations=_read)(get_sales_order)
    register_preview_tool(
        mcp,
        modify_sales_order,
        tags={"orders", "sales", "write"},
        annotations=_modify,
        meta=UI_META,
    )
    register_preview_tool(
        mcp,
        delete_sales_order,
        tags={"orders", "sales", "write", "destructive"},
        annotations=_destructive,
        meta=UI_META,
    )
