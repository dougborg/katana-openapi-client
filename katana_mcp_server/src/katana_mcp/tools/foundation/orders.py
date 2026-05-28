"""Order fulfillment tools for Katana MCP Server.

Foundation tools for fulfilling manufacturing orders and sales orders.

These tools provide:
- fulfill_order: Complete manufacturing orders or fulfill sales orders
"""

from __future__ import annotations

import asyncio
from collections import Counter
from datetime import datetime, timedelta
from typing import Annotated, Any, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, ConfigDict, Field

from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools._modification import WireDatetime
from katana_mcp.tools.tool_result_utils import (
    BLOCK_WARNING_PREFIX,
    UI_META,
    make_tool_result,
    resolve_entity_name,
)
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_mcp.web_urls import katana_web_url
from katana_public_api_client.domain.converters import to_unset, unwrap_unset
from katana_public_api_client.models import (
    ManufacturingOrder,
    ManufacturingOrderProduction,
    SalesOrder,
)
from katana_public_api_client.models.address_entity_type import AddressEntityType
from katana_public_api_client.models_pydantic._generated import (
    CachedCustomer,
    CachedMaterial,
    CachedProduct,
    CachedVariant,
)
from katana_public_api_client.utils import unwrap, unwrap_as

logger = get_logger(__name__)

# ============================================================================
# Tool: fulfill_order
# ============================================================================


class FulfillRowOverride(BaseModel):
    """Per-row override for sales-order fulfillment.

    Currently carries serial-number IDs to attach to a specific row. Used
    when a row's variant is serial-tracked: Katana's
    ``POST /sales_order_fulfillments`` rejects the request with HTTP 422
    unless the row carries one ``SerialNumber`` ID per unit shipped.
    """

    model_config = ConfigDict(extra="forbid")

    sales_order_row_id: int = Field(..., description="Sales order row ID to override")
    serial_numbers: list[int] | None = Field(
        default=None,
        description=(
            "Pre-existing SerialNumber IDs to attach to this fulfillment row. "
            "Length must equal the row's ordered quantity. Required when the "
            "row's variant is serial-tracked."
        ),
    )


class FulfillOrderRequest(BaseModel):
    """Request to fulfill an order."""

    model_config = ConfigDict(extra="forbid")

    order_id: int = Field(..., description="Order ID to fulfill")
    order_type: Literal["manufacturing", "sales"] = Field(
        ..., description="Type of order (manufacturing or sales)"
    )
    preview: bool = Field(
        default=True,
        description="If true (default), returns preview. If false, fulfills order.",
    )
    rows: list[FulfillRowOverride] | None = Field(
        default=None,
        description=(
            "Per-row overrides (currently: serial_numbers). When omitted, the "
            "tool ships the full ordered quantity with no serials attached. "
            "Sales orders only — ignored for order_type='manufacturing'."
        ),
    )
    serial_numbers: list[int] | None = Field(
        default=None,
        description=(
            "Pre-existing SerialNumber IDs to attach to the produced units of a "
            "manufacturing order on completion. Length must equal "
            "``actual_quantity``. Required when the MO's finished-good variant "
            "is serial-tracked. Manufacturing orders only — ignored for "
            "order_type='sales' (use ``rows`` for per-row sales-order serials)."
        ),
    )
    completed_at: WireDatetime | None = Field(
        default=None,
        description=(
            "Backdated completion timestamp for catching up on a backlog. "
            "For manufacturing orders, sets the production record's "
            "``completed_date`` which Katana propagates verbatim to "
            "``MO.done_date``; for sales orders, sets the fulfillment's "
            "``picked_date``. ISO 8601 (e.g. '2026-05-01T20:30:00Z'); "
            "naive datetimes are interpreted as UTC. When omitted, Katana "
            "stamps server-time. Manufacturing branch: lands atomically via "
            "a single ``POST /manufacturing_order_productions`` — no "
            "follow-up PATCH needed. The MO's first-serial "
            "``SerialNumber.transaction_date`` is derived from "
            "``done_date`` / ``completed_date``, so the Traceability "
            "'Production date' column tracks this value."
        ),
    )
    acknowledge_inventory_ordering: bool = Field(
        default=False,
        description=(
            "Override the inventory-ordering BLOCK warning. When set to True, "
            "the tool will proceed despite a detected ordering risk between "
            "MO ``done_date`` and SO ``picked_date``. The strict invariant is "
            "MO ``done_date`` must be **before** SO ``picked_date`` — if they "
            "are simultaneous (or out of order), Katana processes stock "
            "movements in the wrong sequence and records transient negative "
            "inventory on the ``inventory_movements`` ledger. The guard fires "
            "when ``completed_at`` is supplied and a linked entity's "
            "timestamp is known. Use only when you have explicitly verified "
            "Katana's inventory ledger and accepted the consequence of "
            "transient negative balances."
        ),
    )


class FulfilledRowInfo(BaseModel):
    """Per-row fulfillment detail surfaced on the fulfill card (#553).

    Joins the row's identity (variant SKU + ``display_name`` from the
    typed cache) with the fulfillment payload (quantity, serial numbers,
    batch transactions, line total) so the agent can verify *what* is
    being shipped before confirming. Mirrors ``ReceivedItemInfo`` from
    ``foundation/purchase_orders.py``.

    The shape is intentionally uniform across the sales + manufacturing
    branches — the manufacturing branch fills a single row representing
    the MO's finished good, with ``row_id`` set to ``None`` (an MO has
    no row IDs the way an SO does) and ``quantity`` populated from the
    MO's ``actual_quantity``.
    """

    row_id: int | None = Field(
        default=None,
        description=(
            "Sales-order-row ID for SO fulfillments. ``None`` for MO "
            "fulfillments (the MO header carries one variant, not a row)."
        ),
    )
    variant_id: int | None = None
    sku: str | None = None
    display_name: str | None = None
    quantity: float
    serial_numbers: list[int] = Field(
        default_factory=list,
        description=(
            "SerialNumber IDs being attached on this fulfillment "
            "(serial-tracked rows only)."
        ),
    )
    batch_summary: str | None = Field(
        default=None,
        description=(
            "Pre-formatted batch allocations (e.g., 'batch 42x30, batch 51x22') "
            "for batch-tracked variants. ``None`` when the row carries no "
            "batch transactions."
        ),
    )
    price_per_unit: float | None = None
    row_total: float | None = Field(
        default=None,
        description="quantity * price_per_unit in the order currency.",
    )
    currency: str | None = None


class FulfillOrderResponse(BaseModel):
    """Response from fulfilling an order."""

    order_id: int
    order_type: str
    order_number: str
    status: str
    is_preview: bool
    inventory_updates: list[str] = Field(
        default_factory=list, description="Inventory changes made or to be made"
    )
    warnings: list[str] = Field(default_factory=list, description="Warning messages")
    next_actions: list[str] = Field(
        default_factory=list, description="Suggested next steps"
    )
    message: str

    # ---- Tier 2 metrics + Tier 3 per-row breakdown (#553) ----
    fulfilled_rows: list[FulfilledRowInfo] = Field(
        default_factory=list,
        description=(
            "Per-row breakdown of what's being fulfilled — variant identity, "
            "quantity, serials, batch allocations. Drives the Tier 3 "
            "DataTable on the fulfillment card."
        ),
    )
    rows_count: int = Field(
        default=0,
        description=(
            "Count of rows being fulfilled. For sales orders this is the "
            "number of SO rows; for manufacturing orders it's always 1 "
            "(the MO's finished good)."
        ),
    )
    total_quantity: float = Field(
        default=0.0,
        description=(
            "Sum of quantities across all fulfilled rows. Surfaced as a "
            "Tier 2 metric on the card."
        ),
    )
    total_value: float | None = Field(
        default=None,
        description=(
            "Sum of ``row_total`` across all fulfilled rows (in the "
            "order's currency). ``None`` when no row carries a price "
            "(e.g., manufacturing orders — MOs track cost, not price)."
        ),
    )
    currency: str | None = Field(
        default=None,
        description="ISO 4217 currency code (sales orders only).",
    )
    katana_url: str | None = Field(
        default=None,
        description=(
            "Deep link to the order in the Katana web UI. Drives the "
            "Tier 4 'View in Katana' action on the success card."
        ),
    )

    # ---- Tier 3 reference fields surfaced on the fulfill card (sales only) ----
    customer_id: int | None = Field(
        default=None,
        description=(
            "Customer placing the sales order. Drives the Tier 3 'Customer:' "
            "party line. ``None`` on manufacturing orders (MOs have no customer)."
        ),
    )
    customer_name: str | None = Field(
        default=None,
        description=(
            "Resolved customer display name (from typed cache via "
            "``resolve_entity_name``). When ``None`` the card falls back to "
            "``'Customer ID: <id>'`` — a non-fatal warning is appended to "
            "``warnings`` so the operator sees why the name is missing."
        ),
    )
    shipping_address: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Shipping ``SalesOrderAddress.to_dict()`` for the SO. Drives the "
            "Tier 3 'Shipping Address' block. ``None`` when the SO carries no "
            "shipping address or on manufacturing orders."
        ),
    )
    billing_address: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Billing ``SalesOrderAddress.to_dict()`` for the SO. Only set when "
            "the billing address differs from shipping (via "
            "``_addresses_are_equivalent``) — when they match, the card hides "
            "the billing block to avoid duplication."
        ),
    )
    picked_date: str | None = Field(
        default=None,
        description=(
            "ISO-8601 timestamp surfaced as the 'Picked' (sales) or "
            "'Completed' (manufacturing) Metric on the card. Population "
            "rules:\n\n"
            "- **Preview**: caller's ``completed_at`` if supplied, else "
            "  ``None`` (Metric is omitted; the server stamps at apply "
            "  time).\n"
            "- **SO apply-success**: prefers the server-stamped "
            "  ``fulfillment.picked_date`` over ``completed_at`` — so a "
            "  caller that omitted ``completed_at`` still sees the real "
            "  timestamp Katana recorded.\n"
            "- **MO apply-success**: prefers ``final_mo.done_date`` over "
            "  ``completed_at`` for the same reason.\n"
            "- **Refusal paths**: carries the caller's ``completed_at`` "
            "  (no server stamp yet)."
        ),
    )


def _fulfill_response_to_tool_result(
    response: FulfillOrderResponse, *, request: FulfillOrderRequest
) -> ToolResult:
    """Convert FulfillOrderResponse to ToolResult with the appropriate Prefab UI.

    ``request`` is the original tool input. The preview branch threads it
    into ``build_fulfill_preview_ui`` so the rendered Confirm button's
    apply payload carries every non-default arg the user supplied
    (``completed_at`` / ``serial_numbers`` / ``acknowledge_inventory_ordering``
    / ``rows``). Without this plumbing the apply re-issue defaults those
    fields out and silently completes the order at click-time ``now()``
    instead of the backdated timestamp the preview promised. See #845.
    """
    from katana_mcp.tools.prefab_ui import (
        build_fulfill_preview_ui,
        build_fulfill_success_ui,
    )

    response_dict = response.model_dump()
    if response.is_preview:
        ui = build_fulfill_preview_ui(response_dict, request=request)
    else:
        ui = build_fulfill_success_ui(response_dict)

    return make_tool_result(response, ui=ui)


async def _fulfill_manufacturing_order(
    request: FulfillOrderRequest, context: Context
) -> FulfillOrderResponse:
    """Fulfill a manufacturing order by marking it as DONE.

    Serial-tracked finished-good variants need ``serial_numbers`` IDs
    attached on completion; callers pass them via ``request.serial_numbers``.
    Without them, Katana 422s on apply, so the tool emits a ``BLOCK:``
    warning at preview time and refuses on direct apply (parity with the
    sales-order serial-tracked guard added in #547).
    """
    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order as api_get_manufacturing_order,
    )

    services = get_services(context)
    mo_response = await api_get_manufacturing_order.asyncio_detailed(
        id=request.order_id, client=services.client
    )
    mo = unwrap_as(mo_response, ManufacturingOrder)
    order_number = unwrap_unset(mo.order_no, f"MO-{request.order_id}")
    current_status = mo.status.value if mo.status else "UNKNOWN"
    variant_id = unwrap_unset(mo.variant_id, None)
    actual_quantity = unwrap_unset(mo.actual_quantity, None)

    is_serial_tracked, sku, display_name = await _resolve_variant_serial_info(
        services, variant_id
    )

    # The MO header carries one variant — surface the canonical display
    # name in the inventory-updates summary so the rendered fulfillment
    # card matches the variant-naming convention used by every other
    # surface. Falls back to SKU when the typed cache hasn't resolved a
    # display name yet (cold cache / API fallback with no parent).
    finished_good_label = display_name or sku
    inventory_updates = [
        f"Manufacturing order completion will produce {finished_good_label}",
        "Finished goods will be added to stock",
        "Raw materials will be consumed from inventory based on BOM",
    ]
    if is_serial_tracked and request.serial_numbers:
        inventory_updates.append(
            f"Finished-good serials to attach: {request.serial_numbers}"
        )
    if request.completed_at is not None:
        inventory_updates.append(
            f"completed_date / done_date will be set to "
            f"{request.completed_at.isoformat()} "
            "(atomic via POST /manufacturing_order_productions)"
        )

    warnings: list[str] = []
    if current_status == "DONE":
        warnings.append(
            f"{BLOCK_WARNING_PREFIX} Manufacturing order {order_number} is already "
            "completed. No further action will mark it DONE again."
        )
    elif current_status == "BLOCKED":
        warnings.append(
            f"Manufacturing order {order_number} is blocked - review before completing"
        )

    warnings.extend(
        _build_mo_serial_warnings(
            order_number=order_number,
            sku=sku,
            is_serial_tracked=is_serial_tracked,
            actual_quantity=actual_quantity,
            serial_numbers=request.serial_numbers,
        )
    )

    # Tier 3 enrichment (#553): single row representing the MO's finished
    # good. Built before the preview/apply branches so both surfaces share
    # the same payload — the success card's table shouldn't differ from
    # the preview's except for the date timestamp the API stamped.
    mo_batch_transactions = unwrap_unset(getattr(mo, "batch_transactions", None), None)
    fulfilled_rows = [
        _build_fulfilled_row_manufacturing(
            variant_id=variant_id,
            sku=sku,
            display_name=display_name,
            actual_quantity=actual_quantity,
            serial_numbers=request.serial_numbers,
            batch_transactions=mo_batch_transactions,
            order_id=request.order_id,
        )
    ]
    rows_count, total_qty, total_value = _summarize_fulfilled_rows(fulfilled_rows)
    katana_url = katana_web_url("manufacturing_order", request.order_id)

    # Inventory-ordering guard (#787). Symmetric to the SO branch: when the
    # caller backdates done_date and the linked SO is already fulfilled
    # (picked_date set on the header), require strict ordering
    # ``mo_done_at < so_picked_at`` so Katana's timestamp-ordered movement
    # engine doesn't write a transient negative on the inventory_movements
    # ledger. Skip when completed_at is None (server-time) or when there's
    # no linked SO yet (or the SO isn't fulfilled — its future fulfill will
    # be subject to the SO-branch guard).
    linked_so_id = unwrap_unset(mo.sales_order_id, None)
    if request.completed_at is not None and linked_so_id is not None:
        linked_so_picked_at = await _fetch_linked_so_picked_date(services, linked_so_id)
        warnings.extend(
            _build_inventory_ordering_warnings_mo(
                order_number=order_number,
                mo_done_at=request.completed_at,
                linked_so_id=linked_so_id,
                linked_so_picked_at=linked_so_picked_at,
                acknowledged=request.acknowledge_inventory_ordering,
            )
        )

    # MO ``picked_date`` carries the caller-supplied ``completed_at`` on
    # preview so the card surfaces a "Completed" Metric (review item #8).
    # Pre-fix this field was never set on the MO branch, leaving the
    # documented "Completed" Metric branch in ``_render_fulfill_metrics``
    # unreachable. The success path overrides this with the actual
    # ``done_date`` Katana stamped on the post-completion MO header
    # (review item #7) so the operator sees the server's authoritative
    # timestamp even when ``completed_at`` was not supplied.
    mo_picked_date_iso = (
        request.completed_at.isoformat() if request.completed_at is not None else None
    )

    if request.preview:
        has_block = any(w.startswith(BLOCK_WARNING_PREFIX) for w in warnings)
        if current_status == "DONE":
            next_actions = ["Order is already completed - no action needed"]
        elif has_block:
            next_actions = [
                "Resolve the issue above (cancel and inspect via the Katana UI)"
            ]
        else:
            next_actions = [
                "Review the manufacturing order details",
                "Verify all production steps are complete",
                "Set preview=false to mark order as DONE",
            ]
        return FulfillOrderResponse(
            order_id=request.order_id,
            order_type="manufacturing",
            order_number=order_number,
            status=current_status,
            is_preview=True,
            inventory_updates=inventory_updates,
            warnings=warnings,
            next_actions=next_actions,
            message=f"Preview: Would mark manufacturing order {order_number} as DONE (currently {current_status})",
            fulfilled_rows=fulfilled_rows,
            rows_count=rows_count,
            total_quantity=total_qty,
            total_value=total_value,
            picked_date=mo_picked_date_iso,
            katana_url=katana_url,
        )

    # Refuse on apply if any BLOCK warning is present — the preview would have
    # suppressed the Confirm button in the iframe, but we re-check here so
    # direct/programmatic callers (skipping the UI) get the same protection.
    has_block = any(w.startswith(BLOCK_WARNING_PREFIX) for w in warnings)
    if current_status == "DONE":
        return FulfillOrderResponse(
            order_id=request.order_id,
            order_type="manufacturing",
            order_number=order_number,
            status=current_status,
            is_preview=False,
            inventory_updates=[],
            warnings=warnings,
            next_actions=["Order is already completed"],
            message=f"Manufacturing order {order_number} is already completed",
            picked_date=mo_picked_date_iso,
            katana_url=katana_url,
        )
    if has_block:
        return FulfillOrderResponse(
            order_id=request.order_id,
            order_type="manufacturing",
            order_number=order_number,
            status=current_status,
            is_preview=False,
            inventory_updates=[],
            warnings=warnings,
            next_actions=[
                "Resolve the issue(s) above and retry with the corrected request"
            ],
            message=(
                f"Refused: Manufacturing order {order_number} completion blocked by "
                f"{sum(1 for w in warnings if w.startswith(BLOCK_WARNING_PREFIX))} "
                "issue(s); no status change made."
            ),
            picked_date=mo_picked_date_iso,
            katana_url=katana_url,
        )

    from katana_public_api_client.api.manufacturing_order_production import (
        create_manufacturing_order_production as api_create_production,
    )
    from katana_public_api_client.models import (
        CreateManufacturingOrderProductionRequest,
    )

    # Source ``completed_quantity`` from the MO's current ``actual_quantity``
    # (Probe 3 / orders.py:177): partial completion is honored verbatim, and
    # ``is_final=True`` is what flips status — not the planned/actual match.
    # When ``actual_quantity`` is null/UNSET (MO never had a prior production),
    # Katana stamps ``actual_quantity = completed_quantity``, so a sane
    # default of 1 closes the MO at qty=1 (matches Katana's own "complete
    # one" semantics in the UI).
    completed_quantity = actual_quantity if actual_quantity else 1

    production_req = CreateManufacturingOrderProductionRequest(
        manufacturing_order_id=request.order_id,
        completed_quantity=completed_quantity,
        completed_date=to_unset(request.completed_at),
        is_final=True,
        serial_numbers=to_unset(request.serial_numbers),
        # ingredients / operations intentionally omitted — Katana auto-
        # consumes from the MO's recipe (documented behavior).
    )
    production_response = await api_create_production.asyncio_detailed(
        client=services.client, body=production_req
    )
    # Raises APIError on non-2xx (unwrap_as on the response below) — preserves
    # the existing fail-loud contract so callers see the upstream error.
    unwrap_as(production_response, ManufacturingOrderProduction)

    # Re-fetch the MO to surface post-mutation status / done_date. The
    # production response doesn't carry the MO header; the MO does. This is
    # the single full-entity fetch the cache-merge contract relies on
    # (CLAUDE.md "verify and cache-merge once at the end via a single full-
    # entity fetch — not per-action").
    final_mo_response = await api_get_manufacturing_order.asyncio_detailed(
        id=request.order_id, client=services.client
    )
    final_mo = unwrap_as(final_mo_response, ManufacturingOrder)
    new_status = final_mo.status.value if final_mo.status else "UNKNOWN"

    next_actions = [
        f"Manufacturing order {order_number} completed",
        "Inventory has been updated",
        "Check stock levels for finished goods",
    ]
    if request.completed_at is not None:
        next_actions.insert(1, f"done_date set to {request.completed_at.isoformat()}")

    # Rebuild the row from the *final* MO so the success card reflects the
    # post-mutation ``actual_quantity`` Katana stamped (matters when the
    # MO had no prior production and Katana wrote ``actual_quantity =
    # completed_quantity``). batch_transactions also lift from the final
    # MO so any production-time batch allocations surface on the card.
    final_actual_quantity = unwrap_unset(final_mo.actual_quantity, None)
    final_batch_transactions = unwrap_unset(
        getattr(final_mo, "batch_transactions", None), None
    )
    success_rows = [
        _build_fulfilled_row_manufacturing(
            variant_id=variant_id,
            sku=sku,
            display_name=display_name,
            actual_quantity=final_actual_quantity,
            serial_numbers=request.serial_numbers,
            batch_transactions=final_batch_transactions,
            order_id=request.order_id,
        )
    ]
    success_rows_count, success_total_qty, success_total_value = (
        _summarize_fulfilled_rows(success_rows)
    )

    # Prefer the server-stamped ``done_date`` over the caller's
    # ``completed_at`` so the success card shows what Katana actually
    # recorded (review item #7, MO-side). Falls back to the caller-
    # supplied timestamp when ``done_date`` is unset (legacy fixtures /
    # transient stamp lag). Defensive isinstance() check — same MagicMock
    # contract trap as the SO branch.
    server_done_date = unwrap_unset(final_mo.done_date, None)
    if isinstance(server_done_date, datetime):
        success_picked_date_iso: str | None = server_done_date.isoformat()
    else:
        success_picked_date_iso = mo_picked_date_iso

    logger.info(f"Successfully marked manufacturing order {order_number} as DONE")
    return FulfillOrderResponse(
        order_id=request.order_id,
        order_type="manufacturing",
        order_number=order_number,
        status=new_status,
        is_preview=False,
        inventory_updates=inventory_updates,
        warnings=warnings,
        next_actions=next_actions,
        message=f"Successfully marked manufacturing order {order_number} as DONE",
        fulfilled_rows=success_rows,
        rows_count=success_rows_count,
        total_quantity=success_total_qty,
        total_value=success_total_value,
        picked_date=success_picked_date_iso,
        katana_url=katana_url,
    )


async def _fetch_missing_from_api(
    services: Any,
    cached: dict[int, Any],
    needed_ids: set[int],
    api_get_fn: Any,
) -> None:
    """Fill ``cached`` in-place with API fetches for IDs not already present.

    Used to backstop cache misses so a cold or stale cache doesn't mask
    serial-tracking detection. Failures (404 / network) are swallowed and
    the ID stays absent from ``cached`` — callers treat that as "unknown,
    don't block" (best-effort, same fallback as a cache miss).

    The cache lookup that seeds ``cached`` returns ``Cached*`` SQLModel
    instances post-#472 Phase D; this helper appends the API attrs models
    on cache miss. Both shapes expose the same field names as attributes
    (``.sku``, ``.product_id``, etc.), so callers can use ``getattr`` to
    read fields uniformly across cache hits and API-fallback rows.
    """
    from katana_public_api_client.models import ErrorResponse

    missing = [eid for eid in needed_ids if eid not in cached]
    if not missing:
        return
    responses = await asyncio.gather(
        *(
            api_get_fn.asyncio_detailed(id=eid, client=services.client)
            for eid in missing
        ),
        return_exceptions=True,
    )
    for eid, response in zip(missing, responses, strict=True):
        if isinstance(response, BaseException):
            continue
        obj = unwrap(response, raise_on_error=False)
        if obj is None or isinstance(obj, ErrorResponse):
            continue
        cached[eid] = obj


def _attr(obj: Any, name: str, default: Any = None) -> Any:
    """Read ``name`` from a cache row, attrs model, OR dict uniformly.

    Cached SQLModel rows expose plain attributes; attrs models use the
    ``UNSET`` sentinel for missing optional fields; tests occasionally
    fixture in raw dicts (the legacy cache shape) — accept all three
    so call sites stay agnostic to which side filled the slot
    (cache hit vs. API-fallback vs. test fixture). Used in
    serial-track / SKU lookup paths.
    """
    from katana_public_api_client.client_types import UNSET

    if obj is None:
        return default
    if isinstance(obj, dict):
        val = obj.get(name, default)
    else:
        val = getattr(obj, name, default)
    return default if val is UNSET else val


async def _resolve_row_serial_info(
    services: Any, so_rows: list[Any]
) -> tuple[dict[int, bool], dict[int, str], dict[int, str]]:
    """Return ``(serial_tracked_by_row, sku_by_row, display_name_by_row)``
    from cache + API fallback.

    The ``serial_tracked`` flag lives on the parent Product/Material, not on
    Variant — so we fan out variant-by-id, then group parent IDs by type
    and bulk-resolve. Cache misses fall back to a per-ID API fetch (parallel)
    so a cold / stale cache doesn't silently mis-classify a serial-tracked
    row as "OK to ship without serials" and surface the original Katana 422
    on apply. IDs that resolve neither in cache nor via API stay marked
    ``serial_tracked=False`` and ``"variant {id}"`` for SKUs (best-effort,
    same as if the entity didn't exist). The two parent maps are kept
    separate per CLAUDE.md "Cache IDs are not globally unique".

    ``display_name_by_row`` lifts the typed cache's pre-computed
    ``CachedVariant.display_name`` column (which delegates to
    :func:`build_variant_display_name`). API-fallback rows don't carry the
    column, so the helper computes it fresh from the parent name + config
    attributes. Empty string when neither resolves (matches the
    ``MISSING_IN_PO`` convention on the verify path).
    """
    if not so_rows:
        return {}, {}, {}
    from katana_public_api_client.api.material import get_material
    from katana_public_api_client.api.product import get_product
    from katana_public_api_client.api.variant import get_variant
    from katana_public_api_client.domain.variant import build_variant_display_name

    variant_ids = {row.variant_id for row in so_rows if row.variant_id is not None}
    catalog = services.typed_cache.catalog
    variants_by_id: dict[int, Any] = await catalog.get_many_by_ids(
        CachedVariant, variant_ids, include_deleted=True
    )
    await _fetch_missing_from_api(services, variants_by_id, variant_ids, get_variant)

    product_ids = {
        pid
        for v in variants_by_id.values()
        if (pid := _attr(v, "product_id")) is not None
    }
    material_ids = {
        mid
        for v in variants_by_id.values()
        if (mid := _attr(v, "material_id")) is not None
    }
    products: dict[int, Any]
    materials: dict[int, Any]
    products, materials = await asyncio.gather(
        catalog.get_many_by_ids(CachedProduct, product_ids, include_archived=True),
        catalog.get_many_by_ids(CachedMaterial, material_ids, include_archived=True),
    )
    await asyncio.gather(
        _fetch_missing_from_api(services, products, product_ids, get_product),
        _fetch_missing_from_api(services, materials, material_ids, get_material),
    )

    serial_tracked: dict[int, bool] = {}
    skus: dict[int, str] = {}
    display_names: dict[int, str] = {}
    for row in so_rows:
        variant = variants_by_id.get(row.variant_id)
        sku = _attr(variant, "sku") if variant is not None else None
        skus[row.id] = sku or f"variant {row.variant_id}"
        if variant is None:
            serial_tracked[row.id] = False
            display_names[row.id] = ""
            continue
        product_id = _attr(variant, "product_id")
        material_id = _attr(variant, "material_id")
        if product_id:
            parent = products.get(product_id)
        elif material_id:
            parent = materials.get(material_id)
        else:
            parent = None
        serial_tracked[row.id] = bool(parent and _attr(parent, "serial_tracked"))
        # Prefer the typed cache's pre-computed display_name when present
        # (cache hit). On the API-fallback path the attrs variant has no
        # such column, so compute fresh from the resolved parent name +
        # config_attributes — same formula every other surface uses.
        cached_display = _attr(variant, "display_name")
        if cached_display:
            display_names[row.id] = cached_display
        else:
            parent_name = _attr(parent, "name") if parent is not None else None
            display_names[row.id] = build_variant_display_name(
                parent_name,
                _attr(variant, "config_attributes") or [],
                sku,
            )
    return serial_tracked, skus, display_names


async def _resolve_variant_serial_info(
    services: Any, variant_id: int | None
) -> tuple[bool, str, str]:
    """Return ``(is_serial_tracked, sku, display_name)`` for a single variant.

    Single-variant counterpart to ``_resolve_row_serial_info`` used by the
    manufacturing-order path (MOs reference one variant, not per-row). Cache
    misses fall back to a per-ID API fetch so a cold / stale cache doesn't
    silently mis-classify a serial-tracked MO as "OK to mark DONE without
    serials" and surface the original Katana 422 on apply. If the variant
    can't be resolved at all, returns ``(False, f"variant {id}", "")`` —
    best-effort, same as if the entity didn't exist.

    ``display_name`` is the canonical Katana-UI-format name lifted from
    the typed cache's ``CachedVariant.display_name`` column, or computed
    fresh from the parent name + config attributes on the API-fallback path.
    """
    if variant_id is None:
        return False, "variant ?", ""
    from katana_public_api_client.api.material import get_material
    from katana_public_api_client.api.product import get_product
    from katana_public_api_client.api.variant import get_variant
    from katana_public_api_client.domain.variant import build_variant_display_name

    catalog = services.typed_cache.catalog
    variants_by_id: dict[int, Any] = await catalog.get_many_by_ids(
        CachedVariant, {variant_id}, include_deleted=True
    )
    await _fetch_missing_from_api(services, variants_by_id, {variant_id}, get_variant)
    variant = variants_by_id.get(variant_id)
    sku_val = _attr(variant, "sku") if variant is not None else None
    sku = sku_val or f"variant {variant_id}"
    if variant is None:
        return False, sku, ""

    product_id = _attr(variant, "product_id")
    material_id = _attr(variant, "material_id")
    parent: Any = None
    if product_id:
        products: dict[int, Any] = await catalog.get_many_by_ids(
            CachedProduct, {product_id}, include_archived=True
        )
        await _fetch_missing_from_api(services, products, {product_id}, get_product)
        parent = products.get(product_id)
    elif material_id:
        materials: dict[int, Any] = await catalog.get_many_by_ids(
            CachedMaterial, {material_id}, include_archived=True
        )
        await _fetch_missing_from_api(services, materials, {material_id}, get_material)
        parent = materials.get(material_id)

    cached_display = _attr(variant, "display_name")
    if cached_display:
        display_name = cached_display
    else:
        parent_name = _attr(parent, "name") if parent is not None else None
        display_name = build_variant_display_name(
            parent_name,
            _attr(variant, "config_attributes") or [],
            sku_val,
        )
    return bool(parent and _attr(parent, "serial_tracked")), sku, display_name


def _format_batch_summary(batch_transactions: Any) -> str | None:
    """Render a list of ``BatchTransaction``-like objects as a one-line
    summary (e.g., ``"batch 42x30, batch 51x20"``).

    Returns ``None`` when the input is empty / UNSET so the card column
    renders as blank rather than a literal string ``"None"``. Uses ASCII
    ``"x"`` (not the multiplication sign) so ruff's RUF001 (ambiguous-
    unicode) stays clean — matches the convention pinned by the receipt
    card (#556 / PR #793).
    """
    txs = unwrap_unset(batch_transactions, None) or []
    if not txs:
        return None
    parts: list[str] = []
    for tx in txs:
        batch_id = unwrap_unset(getattr(tx, "batch_id", None), None)
        qty = unwrap_unset(getattr(tx, "quantity", None), None)
        if batch_id is None or qty is None:
            continue
        parts.append(f"batch {batch_id}x{qty:g}")
    return ", ".join(parts) if parts else None


async def _fetch_so_addresses(
    services: Any, sales_order_id: int
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Fetch shipping + billing address dicts via ``/sales_order_addresses``.

    Returns ``(shipping, billing)`` where each is a
    ``SalesOrderAddress.to_dict()``-shaped dict ready for
    ``_render_address_block`` (wire-name keys — ``zip``, not ``zip_``).

    GET /sales_orders/{id} does NOT return addresses inline on the
    response — the field is ``Unset`` on the wire and only populated when
    the caller explicitly fetches /sales_order_addresses. The high-level
    ``get_sales_order`` tool does that fetch via
    :func:`_fetch_sales_order_addresses` (sales_orders.py:1517); the
    fulfill tool mirrors the pattern so the Tier-3 reference block
    actually appears in production. Pre-fix this function read
    ``so.addresses`` directly and quietly returned ``(None, None)`` on
    every live tenant.

    Billing is returned as ``None`` when it duplicates shipping — the
    operator only needs one block in that case (mirrors
    ``build_customer_create_ui``). Equivalence reuses
    ``addresses_are_equivalent`` from ``katana_mcp.tools._addresses``:
    same fields the block renders, no entity_type / timestamp noise.

    Returns ``(None, None)`` when the SO has no addresses; the card
    branch elides the entire Tier-3 address row in that case. Cache /
    network failures are swallowed (best-effort) so a fulfill preview
    isn't blocked by a transient address-endpoint hiccup.
    """
    from katana_mcp.tools._addresses import addresses_are_equivalent
    from katana_public_api_client.api.sales_order_address import (
        get_all_sales_order_addresses,
    )
    from katana_public_api_client.utils import unwrap_data

    try:
        response = await get_all_sales_order_addresses.asyncio_detailed(
            client=services.client,
            sales_order_ids=[sales_order_id],
            limit=250,
        )
    except Exception as exc:
        logger.warning(
            "fulfill_sales_order: addresses fetch failed",
            sales_order_id=sales_order_id,
            error=str(exc),
        )
        return None, None
    rows = unwrap_data(response, raise_on_error=False, default=[])
    if not rows:
        return None, None

    shipping_dict: dict[str, Any] | None = None
    billing_dict: dict[str, Any] | None = None
    for row in rows:
        # The /sales_order_addresses endpoint returns rows as attrs
        # SalesOrderAddress models when parsed; ``to_dict()`` emits the
        # wire-shape (``zip`` not ``zip_``). Be defensive for the
        # already-dict path that fixture-side tests use.
        row_dict = row.to_dict() if hasattr(row, "to_dict") else row
        entity_type = row_dict.get("entity_type")
        if isinstance(entity_type, AddressEntityType):
            entity_type = entity_type.value
        if entity_type == "shipping" and shipping_dict is None:
            shipping_dict = row_dict
        elif entity_type == "billing" and billing_dict is None:
            billing_dict = row_dict

    if (
        shipping_dict is not None
        and billing_dict is not None
        and addresses_are_equivalent(shipping_dict, billing_dict)
    ):
        billing_dict = None

    return shipping_dict, billing_dict


def _build_fulfilled_rows_sales(
    so_rows: list[Any],
    *,
    overrides_by_row: dict[int, list[int]],
    sku_by_row: dict[int, str],
    display_name_by_row: dict[int, str],
    currency: str | None,
    order_id: int | None = None,
    order_number: str | None = None,
) -> list[FulfilledRowInfo]:
    """Build per-row ``FulfilledRowInfo`` entries for a sales-order fulfillment.

    Pulls identity from the resolved SKU + display_name maps (which the
    sales branch already builds for serial-tracking detection — no extra
    cache round-trip needed) and pulls the receive payload (qty, batch
    transactions, serial overrides) from each SO row. Price comes from
    ``row.price_per_unit`` (stringly-typed in the wire model; cast to
    float when present so the card can compute ``row_total`` cleanly).

    ``order_id`` / ``order_number`` are threaded through purely for
    observability — the defensive-coerce sites log them alongside the
    row id so a wire-format regression in production is actionable from
    the log line alone (no need to grep request context).
    """
    rows: list[FulfilledRowInfo] = []
    for row in so_rows:
        rid = row.id
        vid = row.variant_id
        qty = row.quantity
        serials = overrides_by_row.get(rid) or []
        batch_summary = _format_batch_summary(getattr(row, "batch_transactions", None))
        # ``price_per_unit`` is ``str | UNSET`` on the wire model — coerce
        # to float so the card can multiply for the line total. Skip the
        # row total when no price is present (rare on a sales order; safe
        # for non-priced rows like free samples).
        raw_ppu = unwrap_unset(getattr(row, "price_per_unit", None), None)
        ppu: float | None
        try:
            ppu = float(raw_ppu) if raw_ppu is not None else None
        except (TypeError, ValueError):
            ppu = None
        # Defensive coerce: qty should be a float on the wire, but test
        # fixtures occasionally leave it as the default MagicMock. Log a
        # warning so a wire-format regression surfaces in observability
        # instead of silently flowing through as 0.
        if isinstance(qty, int | float):
            qty_f: float = float(qty)
        else:
            logger.warning(
                "Unexpected type for SO row quantity: %s "
                "(order_id=%s, order_number=%s, row_id=%s)",
                type(qty),
                order_id,
                order_number,
                rid,
            )
            qty_f = 0.0
        row_total = ppu * qty_f if ppu is not None else None
        # Coerce non-string identity fields to None — a MagicMock leaking
        # through ``_resolve_row_serial_info`` (test fixtures that don't
        # set ``variant.display_name``) would otherwise trip the Pydantic
        # validator. The card falls back to SKU / variant id in that case.
        # Log a warning at each coerce so a wire-format regression
        # surfaces in observability instead of silently nulling.
        sku_raw = sku_by_row.get(rid)
        display_raw = display_name_by_row.get(rid)
        if rid is not None and not isinstance(rid, int):
            logger.warning(
                "Unexpected type for SO row id: %s (order_id=%s, order_number=%s)",
                type(rid),
                order_id,
                order_number,
            )
            row_id_safe: int | None = None
        else:
            row_id_safe = rid if isinstance(rid, int) else None
        if vid is not None and not isinstance(vid, int):
            logger.warning(
                "Unexpected type for SO row variant_id: %s "
                "(order_id=%s, order_number=%s, row_id=%s)",
                type(vid),
                order_id,
                order_number,
                rid,
            )
            variant_id_safe: int | None = None
        else:
            variant_id_safe = vid if isinstance(vid, int) else None
        if sku_raw is not None and not isinstance(sku_raw, str):
            logger.warning(
                "Unexpected type for SO row sku: %s "
                "(order_id=%s, order_number=%s, row_id=%s)",
                type(sku_raw),
                order_id,
                order_number,
                rid,
            )
            sku_for_row: str | None = None
        else:
            sku_for_row = sku_raw if isinstance(sku_raw, str) else None
        if display_raw is not None and not isinstance(display_raw, str):
            logger.warning(
                "Unexpected type for SO row display_name: %s "
                "(order_id=%s, order_number=%s, row_id=%s)",
                type(display_raw),
                order_id,
                order_number,
                rid,
            )
            display_for_row: str | None = None
        else:
            display_for_row = (
                display_raw if isinstance(display_raw, str) and display_raw else None
            )
        rows.append(
            FulfilledRowInfo(
                row_id=row_id_safe,
                variant_id=variant_id_safe,
                sku=sku_for_row,
                display_name=display_for_row,
                quantity=qty_f,
                serial_numbers=serials,
                batch_summary=batch_summary,
                price_per_unit=ppu,
                row_total=row_total,
                currency=currency,
            )
        )
    return rows


def _build_fulfilled_row_manufacturing(
    *,
    variant_id: int | None,
    sku: str,
    display_name: str,
    actual_quantity: float | None,
    serial_numbers: list[int] | None,
    batch_transactions: Any,
    order_id: int | None = None,
) -> FulfilledRowInfo:
    """Build the single ``FulfilledRowInfo`` for a manufacturing-order
    completion.

    An MO header carries one variant, not a row list — so we synthesize
    one fulfilled-row entry with ``row_id=None``. Quantity falls back to
    ``1`` to match the apply path's ``completed_quantity`` default
    (``actual_quantity or 1``) so the card's Tier 2 "total qty" metric
    matches what's actually being produced.

    ``price_per_unit`` / ``row_total`` are deliberately left ``None`` —
    MOs track cost, not price, and the cost ledger lives on a separate
    surface. The card hides the Line Total column for MO branches.

    ``order_id`` is threaded purely for observability — defensive-coerce
    sites log it alongside the ``variant_id`` so a wire-format
    regression in production is traceable from the log line alone.
    """
    if isinstance(actual_quantity, int | float):
        qty_f: float = float(actual_quantity)
    elif actual_quantity is not None:
        logger.warning(
            "Unexpected type for MO actual_quantity: %s (order_id=%s, variant_id=%s)",
            type(actual_quantity),
            order_id,
            variant_id,
        )
        qty_f = 1.0
    else:
        qty_f = 1.0
    # Defensive coerce on string fields: test fixtures that miss the SKU
    # / display_name setup leak MagicMocks through ``_resolve_variant_
    # serial_info``; Pydantic's validator rejects those, so coerce to
    # None and let the card fall back to ``variant {id}`` rendering. We
    # *don't* strip the ``"variant {id}"`` fallback sentinel here — real
    # customer SKUs that share the literal ``"variant "`` prefix (e.g.
    # ``"variant 2 pack"`` for a multi-pack) are legitimate, and silently
    # blanking them would be data loss. Empty strings still fall through
    # to ``None`` so the card's ``display_name or sku`` chain works. Log
    # a warning at each coerce so a wire-format regression surfaces in
    # observability instead of silently nulling.
    if isinstance(sku, str):
        sku_safe: str | None = sku or None
    else:
        logger.warning(
            "Unexpected type for MO sku: %s (order_id=%s, variant_id=%s)",
            type(sku),
            order_id,
            variant_id,
        )
        sku_safe = None
    if isinstance(display_name, str):
        display_safe: str | None = display_name or None
    else:
        logger.warning(
            "Unexpected type for MO display_name: %s (order_id=%s, variant_id=%s)",
            type(display_name),
            order_id,
            variant_id,
        )
        display_safe = None
    if variant_id is not None and not isinstance(variant_id, int):
        logger.warning(
            "Unexpected type for MO variant_id: %s (order_id=%s)",
            type(variant_id),
            order_id,
        )
        variant_id_safe: int | None = None
    else:
        variant_id_safe = variant_id if isinstance(variant_id, int) else None
    return FulfilledRowInfo(
        row_id=None,
        variant_id=variant_id_safe,
        sku=sku_safe,
        display_name=display_safe,
        quantity=qty_f,
        serial_numbers=list(serial_numbers or []),
        batch_summary=_format_batch_summary(batch_transactions),
        price_per_unit=None,
        row_total=None,
        currency=None,
    )


def _summarize_fulfilled_rows(
    rows: list[FulfilledRowInfo],
) -> tuple[int, float, float | None]:
    """Return ``(rows_count, total_quantity, total_value)`` for the card's
    Tier 2 metrics row.

    ``total_value`` is ``None`` when *no* row carries a ``row_total``
    (e.g., MO fulfillment — no price) so the card can render a 2-metric
    row instead of a "—"-filled third metric. When at least one row has
    a total, missing values are treated as ``0`` (the sum represents
    "what's priced is X", not "every row priced").
    """
    rows_count = len(rows)
    total_qty = sum(r.quantity for r in rows)
    priced = [r.row_total for r in rows if r.row_total is not None]
    total_value: float | None = sum(priced) if priced else None
    return rows_count, total_qty, total_value


def _build_mo_serial_warnings(
    *,
    order_number: str,
    sku: str,
    is_serial_tracked: bool,
    actual_quantity: float | None,
    serial_numbers: list[int] | None,
) -> list[str]:
    """Return ``BLOCK:`` warnings for a manufacturing-order serial mismatch.

    Mirrors ``_build_row_override_warnings`` but for the single-variant MO
    shape: a serial-tracked MO needs serials attached on completion, the
    count must equal ``actual_quantity``, and a fractional ``actual_quantity``
    is incompatible with serial tracking (each serial represents a whole
    unit). Numeric equality with ``int(qty)`` matches Python's ``2 == 2.0``
    behaviour; non-integral qty on a serial-tracked MO is blocked separately.
    """
    warnings: list[str] = []
    if not is_serial_tracked:
        return warnings
    qty = actual_quantity
    if qty is not None and qty != int(qty):
        warnings.append(
            f"{BLOCK_WARNING_PREFIX} Manufacturing order {order_number} "
            f"({sku}) is serial-tracked but actual_quantity ({qty}) is not a "
            "whole number; serial-tracked variants must be produced in "
            "integer units."
        )
        return warnings
    if not serial_numbers and (qty or 0) > 0:
        warnings.append(
            f"{BLOCK_WARNING_PREFIX} Manufacturing order {order_number} "
            f"({sku}) is serial-tracked. Pass serial_numbers (one "
            "SerialNumber ID per unit produced) to mark the order DONE."
        )
    elif serial_numbers is not None and qty is not None and len(serial_numbers) != qty:
        warnings.append(
            f"{BLOCK_WARNING_PREFIX} Manufacturing order {order_number} "
            f"({sku}): serial_numbers count ({len(serial_numbers)}) must "
            f"equal actual_quantity ({qty})."
        )
    return warnings


def _build_row_override_warnings(
    *,
    so_rows: list[Any],
    request_rows: list[FulfillRowOverride],
    overrides_by_row: dict[int, list[int]],
    serial_tracked_by_row: dict[int, bool],
    sku_by_row: dict[int, str],
    order_number: str,
) -> list[str]:
    """Return all ``BLOCK:`` warnings driven by ``request.rows`` content.

    Covers: unknown row IDs, duplicate overrides, serial-tracked rows
    missing serials, count/quantity mismatches, and non-integer quantity
    on serial-tracked rows. Numeric comparisons use ``qty`` directly —
    Python equality treats ``2 == 2.0`` as ``True``, so an integer-valued
    ``2.0`` qty still matches ``len(serials) == 2``. Non-integral qty on a
    serial-tracked row is blocked separately, since each serial number
    represents a whole unit.
    """
    warnings: list[str] = []
    so_row_ids = {row.id for row in so_rows}

    for ovr in request_rows:
        if ovr.sales_order_row_id not in so_row_ids:
            warnings.append(
                f"{BLOCK_WARNING_PREFIX} Row override references unknown "
                f"sales_order_row_id={ovr.sales_order_row_id} "
                f"(sales order {order_number} has rows {sorted(so_row_ids)})."
            )

    # A row appearing twice in `rows=` would silently keep only the last
    # entry (dict-comp last-key-wins) — flag it so the caller fixes the input.
    duplicate_override_ids = sorted(
        rid
        for rid, count in Counter(
            ovr.sales_order_row_id for ovr in request_rows
        ).items()
        if count > 1
    )
    if duplicate_override_ids:
        warnings.append(
            f"{BLOCK_WARNING_PREFIX} Multiple overrides for the same "
            f"sales_order_row_id ({duplicate_override_ids}); each row may "
            "appear at most once in rows=."
        )

    for row in so_rows:
        rid = row.id
        qty = row.quantity
        is_tracked = serial_tracked_by_row.get(rid, False)
        serials = overrides_by_row.get(rid)
        if is_tracked and qty is not None and qty != int(qty):
            warnings.append(
                f"{BLOCK_WARNING_PREFIX} Row {rid} ({sku_by_row.get(rid)}) is "
                f"serial-tracked but quantity ({qty}) is not a whole number; "
                "serial-tracked variants must ship in integer units."
            )
        elif is_tracked and not serials and (qty or 0) > 0:
            warnings.append(
                f"{BLOCK_WARNING_PREFIX} Row {rid} ({sku_by_row.get(rid)}) is "
                "serial-tracked. Pass serial_numbers via the rows= override "
                "(one SerialNumber ID per unit)."
            )
        elif serials is not None and qty is not None and len(serials) != qty:
            warnings.append(
                f"{BLOCK_WARNING_PREFIX} Row {rid} ({sku_by_row.get(rid)}): "
                f"serial_numbers count ({len(serials)}) must equal quantity "
                f"({qty})."
            )
    return warnings


# ============================================================================
# Inventory-ordering guard (#787)
# ============================================================================
#
# Katana's stock-movement engine is timestamp-ordered: a ``Production`` event
# that lands at ``T`` lifts the finished-good balance from 0 → 1; a
# ``SalesOrderRow`` event at the *same instant* (or earlier) sees balance 0
# and writes a -1 movement to the persistent ``inventory_movements`` ledger
# before the production posts. The transient negative is auditable forever,
# not just a UI race.
#
# Live-tenant probe (issue #787) verified three cases on a producible variant:
#   - MO ``done_date`` ==  SO ``picked_date``: non-deterministic ordering;
#     half the time Katana writes the SalesOrderRow first → bal=-1.
#   - SO before MO: deterministic negative balance recorded.
#   - MO 1 min before SO: clean, never negative.
#
# Guards on both branches:
#   - SO fulfill: if any linked MO has ``done_date >= so_picked_at``, BLOCK.
#   - MO fulfill: if linked SO has ``picked_date <= mo_done_at``, BLOCK.
#
# Override flag ``acknowledge_inventory_ordering`` demotes the BLOCK to a
# non-BLOCK warning (operator has accepted the ledger consequence) — the
# warning is still surfaced in the response, just doesn't trip ``has_block``.

_INVENTORY_ORDERING_SUGGESTED_GAP = timedelta(minutes=1)


def _format_iso(ts: datetime) -> str:
    """Stable ISO-8601 rendering for BLOCK warning bodies.

    ``datetime.isoformat()`` is already stable; centralized here so the
    suggested-correction text and the violation text use the same format
    and stay easy to grep for in tests / logs.
    """
    return ts.isoformat()


def _build_inventory_ordering_warnings_so(
    *,
    order_number: str,
    so_picked_at: datetime | None,
    linked_mo_done_dates: dict[int, datetime | None],
    acknowledged: bool,
) -> list[str]:
    """Return warnings when SO ``picked_date <= any linked MO done_date``.

    Silent when:
      - ``so_picked_at`` is None (server-time, no race the caller controls)
      - no linked MOs were found (``linked_mo_done_dates`` empty)
      - every linked MO has an unset ``done_date`` (nothing to compare against;
        the future MO close will be subject to the MO-branch guard)

    Fires once per violating MO ID. Demotes to a non-``BLOCK:`` warning when
    ``acknowledged=True`` (override flag set) — still surfaced for the audit
    trail, just doesn't trip ``has_block``. Mirrors the spirit of the
    existing non-BLOCK ``done_date PATCH failed`` warning.
    """
    if so_picked_at is None:
        return []

    warnings: list[str] = []
    for mo_id, mo_done in linked_mo_done_dates.items():
        if mo_done is None:
            continue
        if so_picked_at > mo_done:
            continue
        suggested = mo_done + _INVENTORY_ORDERING_SUGGESTED_GAP
        core = (
            f"Sales order {order_number} picked_date "
            f"({_format_iso(so_picked_at)}) is not after linked manufacturing "
            f"order {mo_id} done_date ({_format_iso(mo_done)}). This will "
            "cause transient negative inventory on the inventory_movements "
            "ledger. Set picked_date at least 1 minute after the MO "
            f"done_date (suggested: {_format_iso(suggested)})."
        )
        if acknowledged:
            warnings.append(f"WARNING (acknowledged): {core}")
        else:
            warnings.append(
                f"{BLOCK_WARNING_PREFIX} {core} Pass "
                "acknowledge_inventory_ordering=true to override."
            )
    return warnings


def _build_inventory_ordering_warnings_mo(
    *,
    order_number: str,
    mo_done_at: datetime | None,
    linked_so_id: int | None,
    linked_so_picked_at: datetime | None,
    acknowledged: bool,
) -> list[str]:
    """Return warnings when MO ``done_date >= linked SO picked_date``.

    Silent when:
      - ``mo_done_at`` is None (server-time)
      - ``linked_so_id`` is None (no linked SO to compare against)
      - ``linked_so_picked_at`` is None (SO not yet fulfilled — the future
        SO fulfill will be subject to the SO-branch guard)

    Demotes to a non-``BLOCK:`` warning when ``acknowledged=True``.
    """
    if mo_done_at is None or linked_so_id is None or linked_so_picked_at is None:
        return []
    if mo_done_at < linked_so_picked_at:
        return []

    suggested = linked_so_picked_at - _INVENTORY_ORDERING_SUGGESTED_GAP
    core = (
        f"Manufacturing order {order_number} done_date "
        f"({_format_iso(mo_done_at)}) is not before linked sales order "
        f"{linked_so_id} picked_date ({_format_iso(linked_so_picked_at)}). "
        "This will cause transient negative inventory on the "
        "inventory_movements ledger. Set done_date at least 1 minute before "
        f"the SO picked_date (suggested: {_format_iso(suggested)})."
    )
    if acknowledged:
        return [f"WARNING (acknowledged): {core}"]
    return [
        f"{BLOCK_WARNING_PREFIX} {core} Pass "
        "acknowledge_inventory_ordering=true to override."
    ]


async def _fetch_linked_mo_done_dates(
    services: Any, mo_ids: set[int]
) -> dict[int, datetime | None]:
    """Fan-out fetch ``done_date`` for each linked MO ID.

    Returns ``{mo_id: done_date_or_None}`` for every successfully fetched MO.
    Failures (404 / network) are swallowed — the ID drops out of the dict,
    which the warning helper treats as "unknown, don't block" (best-effort).
    """
    if not mo_ids:
        return {}
    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order as api_get_manufacturing_order,
    )

    # Materialize the set to a stable sequence once. Iterating a ``set``
    # twice (here and below in ``zip``) does not guarantee the same
    # order at the language level, which could mis-associate responses
    # to MO ids and silently block the wrong order or miss a real
    # violation. Sort for determinism — handy for test debugging too.
    mo_id_list = sorted(mo_ids)
    responses = await asyncio.gather(
        *(
            api_get_manufacturing_order.asyncio_detailed(
                id=mo_id, client=services.client
            )
            for mo_id in mo_id_list
        ),
        return_exceptions=True,
    )
    out: dict[int, datetime | None] = {}
    for mo_id, response in zip(mo_id_list, responses, strict=True):
        if isinstance(response, BaseException):
            continue
        mo = unwrap(response, raise_on_error=False)
        if mo is None or not isinstance(mo, ManufacturingOrder):
            continue
        out[mo_id] = unwrap_unset(mo.done_date, None)
    return out


async def _fetch_linked_so_picked_date(services: Any, so_id: int) -> datetime | None:
    """Fetch the linked SO's header ``picked_date``.

    Returns None on any failure (404 / network) or when ``picked_date`` is
    unset. Callers treat None as "nothing to compare against" (best-effort).
    Uses the same ``gather(return_exceptions=True)`` swallow pattern as
    :func:`_fetch_missing_from_api` so a transient lookup failure can't
    take down the apply path.
    """
    from katana_public_api_client.api.sales_order import (
        get_sales_order as api_get_sales_order,
    )

    (response,) = await asyncio.gather(
        api_get_sales_order.asyncio_detailed(id=so_id, client=services.client),
        return_exceptions=True,
    )
    if isinstance(response, BaseException):
        return None
    so = unwrap(response, raise_on_error=False)
    if so is None or not isinstance(so, SalesOrder):
        return None
    return unwrap_unset(so.picked_date, None)


async def _fulfill_sales_order(
    request: FulfillOrderRequest, context: Context
) -> FulfillOrderResponse:
    """Fulfill a sales order by creating a DELIVERED fulfillment record.

    The Katana API ``POST /sales_order_fulfillments`` requires per-row
    fulfillment input (``sales_order_fulfillment_rows``: each carrying a
    ``sales_order_row_id`` and a ``quantity``). The tool fetches the sales
    order's rows and ships the full quantity of each — the standard
    "deliver everything ordered" case. For partial fulfillments the user
    should use the Katana UI directly; the tool's MCP surface intentionally
    keeps the simple case simple.

    Serial-tracked variants need ``serial_numbers`` IDs attached per row;
    callers pass them via ``request.rows`` (``FulfillRowOverride``). Without
    them, Katana 422s on apply, so the tool emits a ``BLOCK:`` warning at
    preview time and refuses on direct apply.
    """
    from katana_public_api_client.api.sales_order import (
        get_sales_order as api_get_sales_order,
    )

    services = get_services(context)
    so_response = await api_get_sales_order.asyncio_detailed(
        id=request.order_id, client=services.client
    )
    so = unwrap_as(so_response, SalesOrder)
    order_number = unwrap_unset(so.order_no, f"SO-{request.order_id}")
    current_status = so.status.value if so.status else "UNKNOWN"
    so_rows = unwrap_unset(so.sales_order_rows, []) or []

    overrides_by_row: dict[int, list[int]] = {
        ovr.sales_order_row_id: ovr.serial_numbers or []
        for ovr in (request.rows or [])
        if ovr.serial_numbers is not None
    }

    (
        serial_tracked_by_row,
        sku_by_row,
        display_name_by_row,
    ) = await _resolve_row_serial_info(services, so_rows)

    warnings: list[str] = []

    # Tier 3 reference data (#card-ux): resolve customer name + extract
    # shipping/billing addresses so the fulfill card can show the operator
    # *who* the package goes to and *where*. Pre-#card-ux the card surfaced
    # only the order number + status; nothing identifying the recipient.
    # ``inventory_updates`` is intentionally left empty for the SO branch —
    # the per-row text dump it carried before duplicated ``fulfilled_rows``
    # one-for-one (the source of the user-cited redundancy). Structured
    # consumers read ``fulfilled_rows``; the card reads the resolved name +
    # addresses below.
    customer_id = unwrap_unset(so.customer_id, None)
    customer_name: str | None = None
    if customer_id is not None:
        customer_name, customer_name_warning = await resolve_entity_name(
            services.typed_cache.catalog,
            CachedCustomer,
            customer_id,
            entity_label="Customer",
        )
        if customer_name_warning:
            warnings.append(customer_name_warning)
    # /sales_order_addresses is a sibling endpoint — GET /sales_orders/{id}
    # does NOT inline addresses on the response (so.addresses is Unset on
    # the wire). The high-level ``get_sales_order`` tool does this same
    # fetch via _fetch_sales_order_addresses; mirroring that pattern here
    # keeps the fulfill card's Tier-3 reference block actually visible in
    # production. Pre-fix this function read so.addresses directly and
    # silently returned (None, None) on every live tenant.
    shipping_address, billing_address = await _fetch_so_addresses(
        services, request.order_id
    )
    picked_date_iso = (
        request.completed_at.isoformat() if request.completed_at is not None else None
    )

    inventory_updates: list[str] = []
    if current_status in ("DELIVERED", "PARTIALLY_DELIVERED"):
        warnings.append(
            f"{BLOCK_WARNING_PREFIX} Sales order {order_number} status is "
            f"{current_status}. Creating another fulfillment may double-ship items."
        )
    if not so_rows:
        warnings.append(
            f"{BLOCK_WARNING_PREFIX} Sales order {order_number} has no rows to fulfill."
        )

    warnings.extend(
        _build_row_override_warnings(
            so_rows=so_rows,
            request_rows=request.rows or [],
            overrides_by_row=overrides_by_row,
            serial_tracked_by_row=serial_tracked_by_row,
            sku_by_row=sku_by_row,
            order_number=order_number,
        )
    )

    # Tier 3 enrichment (#553): per-row breakdown for the card so the
    # operator can verify *what* is being shipped without reading the raw
    # tool-call blob. Reuses the SKU + display_name maps that the
    # serial-tracking detection already built — no extra cache round-trip.
    raw_currency = unwrap_unset(so.currency, None)
    # Defensive: ``unwrap_unset`` only filters the UNSET sentinel — a test
    # fixture that forgot to stub ``.currency`` leaks a MagicMock through,
    # which Pydantic rejects on ``FulfilledRowInfo.currency``. Coerce
    # anything non-string to ``None`` so the response model validates.
    # Log a warning so a wire-format regression surfaces in observability
    # instead of silently nulling.
    if raw_currency is not None and not isinstance(raw_currency, str):
        logger.warning(
            "Unexpected type for SO currency: %s (order_id=%s, order_number=%s)",
            type(raw_currency),
            request.order_id,
            order_number,
        )
        currency: str | None = None
    else:
        currency = raw_currency if isinstance(raw_currency, str) else None
    fulfilled_rows = _build_fulfilled_rows_sales(
        so_rows,
        overrides_by_row=overrides_by_row,
        sku_by_row=sku_by_row,
        display_name_by_row=display_name_by_row,
        currency=currency,
        order_id=request.order_id,
        order_number=order_number,
    )
    rows_count, total_qty, total_value = _summarize_fulfilled_rows(fulfilled_rows)
    katana_url = katana_web_url("sales_order", request.order_id)

    # Inventory-ordering guard (#787). Skip when caller didn't supply a
    # backdated picked_date — server-stamped time can't trip a deterministic
    # race the caller controls. Linked-MO IDs are read off the SO rows we
    # already fetched; one parallel fan-out resolves their done_dates.
    if request.completed_at is not None:
        linked_mo_ids = {
            mid
            for row in so_rows
            if (mid := unwrap_unset(row.linked_manufacturing_order_id, None))
            is not None
        }
        linked_mo_done_dates = await _fetch_linked_mo_done_dates(
            services, linked_mo_ids
        )
        warnings.extend(
            _build_inventory_ordering_warnings_so(
                order_number=order_number,
                so_picked_at=request.completed_at,
                linked_mo_done_dates=linked_mo_done_dates,
                acknowledged=request.acknowledge_inventory_ordering,
            )
        )

    # Shared Tier-3 reference kwargs threaded through every SO-branch
    # response constructor — preview, refusal paths, and success. Keeps
    # the customer / shipping / billing / picked_date payload consistent
    # whether the operator sees a preview card or an "already delivered"
    # refusal card.
    reference_kwargs: dict[str, Any] = {
        "customer_id": customer_id,
        "customer_name": customer_name,
        "shipping_address": shipping_address,
        "billing_address": billing_address,
        "picked_date": picked_date_iso,
    }

    if request.preview:
        has_block = any(w.startswith(BLOCK_WARNING_PREFIX) for w in warnings)
        next_actions = (
            ["Resolve the issue above (cancel and inspect via the Katana UI)"]
            if has_block
            else [
                "Review the row list above",
                "Set preview=false to create a DELIVERED fulfillment for the full order",
            ]
        )
        return FulfillOrderResponse(
            order_id=request.order_id,
            order_type="sales",
            order_number=order_number,
            status=current_status,
            is_preview=True,
            inventory_updates=inventory_updates,
            warnings=warnings,
            next_actions=next_actions,
            message=(
                f"Preview: Would fulfill sales order {order_number} "
                f"({len(so_rows)} row(s), currently {current_status})"
            ),
            fulfilled_rows=fulfilled_rows,
            rows_count=rows_count,
            total_quantity=total_qty,
            total_value=total_value,
            currency=currency,
            katana_url=katana_url,
            **reference_kwargs,
        )

    # Refuse on apply if any BLOCK warning is present — the preview would have
    # suppressed the Confirm button in the iframe, but we re-check here so
    # direct/programmatic callers (skipping the UI) get the same protection.
    has_block = any(w.startswith(BLOCK_WARNING_PREFIX) for w in warnings)
    if current_status in ("DELIVERED", "PARTIALLY_DELIVERED"):
        return FulfillOrderResponse(
            order_id=request.order_id,
            order_type="sales",
            order_number=order_number,
            status=current_status,
            is_preview=False,
            inventory_updates=[],
            warnings=warnings,
            next_actions=["No action taken — order already delivered"],
            message=(
                f"Sales order {order_number} is already {current_status}; refusing "
                "to create a duplicate fulfillment"
            ),
            katana_url=katana_url,
            **reference_kwargs,
        )
    if not so_rows:
        return FulfillOrderResponse(
            order_id=request.order_id,
            order_type="sales",
            order_number=order_number,
            status=current_status,
            is_preview=False,
            inventory_updates=[],
            warnings=warnings,
            next_actions=["No action taken — order has no rows to fulfill"],
            message=(
                f"Refused: Sales order {order_number} has no rows to fulfill; "
                "no fulfillment created."
            ),
            katana_url=katana_url,
            **reference_kwargs,
        )
    if has_block:
        return FulfillOrderResponse(
            order_id=request.order_id,
            order_type="sales",
            order_number=order_number,
            status=current_status,
            is_preview=False,
            inventory_updates=[],
            warnings=warnings,
            next_actions=[
                "Resolve the issue(s) above and retry with the corrected request"
            ],
            message=(
                f"Refused: Sales order {order_number} fulfillment blocked by "
                f"{sum(1 for w in warnings if w.startswith(BLOCK_WARNING_PREFIX))} "
                "issue(s); no fulfillment created."
            ),
            katana_url=katana_url,
            **reference_kwargs,
        )

    from katana_public_api_client.api.sales_order_fulfillment import (
        create_sales_order_fulfillment as api_create_fulfillment,
    )
    from katana_public_api_client.models import (
        CreateSalesOrderFulfillmentRequest,
        SalesOrderFulfillment,
        SalesOrderFulfillmentRowRequest,
        SalesOrderFulfillmentStatus,
    )

    fulfill_rows = [
        SalesOrderFulfillmentRowRequest(
            sales_order_row_id=row.id,
            quantity=row.quantity,
            serial_numbers=to_unset(overrides_by_row.get(row.id)),
        )
        for row in so_rows
    ]
    fulfill_request = CreateSalesOrderFulfillmentRequest(
        sales_order_id=request.order_id,
        status=SalesOrderFulfillmentStatus.DELIVERED,
        sales_order_fulfillment_rows=fulfill_rows,
        picked_date=to_unset(request.completed_at),
    )
    fulfill_response = await api_create_fulfillment.asyncio_detailed(
        client=services.client, body=fulfill_request
    )
    fulfillment = unwrap_as(fulfill_response, SalesOrderFulfillment)

    # Prefer the server-stamped ``picked_date`` over the caller's
    # ``completed_at`` (review item #7). Pre-fix the success card hid
    # the Picked Metric whenever the caller didn't pass ``completed_at``
    # despite Katana stamping a real timestamp on the fulfillment.
    # Override the ``picked_date`` slot in reference_kwargs so the spread
    # below picks up the server's value. Defensive: only override when
    # the server value is a real ``datetime`` — MagicMock fixtures leak
    # a child mock through ``unwrap_unset`` and pydantic would then
    # reject the field at construction time.
    server_picked = unwrap_unset(fulfillment.picked_date, None)
    if isinstance(server_picked, datetime):
        reference_kwargs["picked_date"] = server_picked.isoformat()

    logger.info(
        f"Created sales order fulfillment {fulfillment.id} for SO {order_number} "
        f"({len(fulfill_rows)} row(s) DELIVERED)"
    )
    return FulfillOrderResponse(
        order_id=request.order_id,
        order_type="sales",
        order_number=order_number,
        status="DELIVERED",
        is_preview=False,
        inventory_updates=[
            f"Created fulfillment {fulfillment.id} marking {len(fulfill_rows)} row(s) DELIVERED"
        ],
        warnings=warnings,
        next_actions=[
            f"Sales order {order_number} marked DELIVERED",
            "Inventory has been adjusted for shipped items",
        ],
        message=(
            f"Successfully fulfilled sales order {order_number} "
            f"({len(fulfill_rows)} row(s), fulfillment id={fulfillment.id})"
        ),
        fulfilled_rows=fulfilled_rows,
        rows_count=rows_count,
        total_quantity=total_qty,
        total_value=total_value,
        currency=currency,
        katana_url=katana_url,
        **reference_kwargs,
    )


async def _fulfill_order_impl(
    request: FulfillOrderRequest, context: Context
) -> FulfillOrderResponse:
    """Dispatch to the appropriate fulfillment handler."""
    logger.info(
        f"{'Previewing' if request.preview else 'Fulfilling'} {request.order_type} order {request.order_id}"
    )
    try:
        if request.order_type == "manufacturing":
            return await _fulfill_manufacturing_order(request, context)
        return await _fulfill_sales_order(request, context)
    except Exception as e:
        logger.error(f"Failed to fulfill {request.order_type} order: {e}")
        raise


@observe_tool
@unpack_pydantic_params
async def fulfill_order(
    request: Annotated[FulfillOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Complete a manufacturing order (mark DONE) or fulfill a sales order (ship items).

    Destructive operation that updates inventory. Two-step flow: preview=true
    (default) to preview what would happen, preview=false to execute.

    Manufacturing: marks order DONE, adds finished goods, consumes raw materials.
    Sales: creates a fulfillment record, reduces available inventory.
    """
    response = await _fulfill_order_impl(request, context)
    return _fulfill_response_to_tool_result(response, request=request)


def register_tools(mcp: FastMCP) -> None:
    """Register all order fulfillment tools with the FastMCP instance.

    Args:
        mcp: FastMCP server instance to register tools with
    """
    from mcp.types import ToolAnnotations

    from katana_mcp.tools.prefab_ui import register_preview_tool

    register_preview_tool(
        mcp,
        fulfill_order,
        tags={"orders", "write", "destructive"},
        annotations=ToolAnnotations(
            readOnlyHint=False, destructiveHint=True, openWorldHint=True
        ),
        meta=UI_META,
    )
