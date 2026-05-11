"""Order fulfillment tools for Katana MCP Server.

Foundation tools for fulfilling manufacturing orders and sales orders.

These tools provide:
- fulfill_order: Complete manufacturing orders or fulfill sales orders
"""

from __future__ import annotations

import asyncio
from collections import Counter
from typing import Annotated, Any, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, ConfigDict, Field

from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.tool_result_utils import (
    BLOCK_WARNING_PREFIX,
    UI_META,
    make_tool_result,
)
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.domain.converters import to_unset, unwrap_unset
from katana_public_api_client.models import (
    ManufacturingOrder,
    SalesOrder,
    UpdateManufacturingOrderRequest,
)
from katana_public_api_client.models_pydantic._generated import (
    CachedMaterial,
    CachedProduct,
    CachedVariant,
)
from katana_public_api_client.utils import unwrap_as

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


def _fulfill_response_to_tool_result(response: FulfillOrderResponse) -> ToolResult:
    """Convert FulfillOrderResponse to ToolResult with the appropriate Prefab UI."""
    from katana_mcp.tools.prefab_ui import (
        build_fulfill_preview_ui,
        build_fulfill_success_ui,
    )

    response_dict = response.model_dump()
    if response.is_preview:
        ui = build_fulfill_preview_ui(response_dict)
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

    is_serial_tracked, sku = await _resolve_variant_serial_info(services, variant_id)

    inventory_updates = [
        "Manufacturing order completion will update inventory based on BOM",
        "Finished goods will be added to stock",
        "Raw materials will be consumed from inventory",
    ]
    if is_serial_tracked and request.serial_numbers:
        inventory_updates.append(
            f"Finished-good serials to attach: {request.serial_numbers}"
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
        )

    from katana_public_api_client.api.manufacturing_order import (
        update_manufacturing_order as api_update_manufacturing_order,
    )
    from katana_public_api_client.models.manufacturing_order_status import (
        ManufacturingOrderStatus,
    )

    update_req = UpdateManufacturingOrderRequest(
        status=ManufacturingOrderStatus.DONE,
        serial_numbers=to_unset(request.serial_numbers),
    )
    update_response = await api_update_manufacturing_order.asyncio_detailed(
        id=request.order_id, client=services.client, body=update_req
    )
    updated_mo = unwrap_as(update_response, ManufacturingOrder)
    new_status = updated_mo.status.value if updated_mo.status else "UNKNOWN"

    logger.info(f"Successfully marked manufacturing order {order_number} as DONE")
    return FulfillOrderResponse(
        order_id=request.order_id,
        order_type="manufacturing",
        order_number=order_number,
        status=new_status,
        is_preview=False,
        inventory_updates=inventory_updates,
        warnings=warnings,
        next_actions=[
            f"Manufacturing order {order_number} completed",
            "Inventory has been updated",
            "Check stock levels for finished goods",
        ],
        message=f"Successfully marked manufacturing order {order_number} as DONE",
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
    from katana_public_api_client.utils import unwrap

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
) -> tuple[dict[int, bool], dict[int, str]]:
    """Return ``(serial_tracked_by_row, sku_by_row)`` from cache + API fallback.

    The ``serial_tracked`` flag lives on the parent Product/Material, not on
    Variant — so we fan out variant-by-id, then group parent IDs by type
    and bulk-resolve. Cache misses fall back to a per-ID API fetch (parallel)
    so a cold / stale cache doesn't silently mis-classify a serial-tracked
    row as "OK to ship without serials" and surface the original Katana 422
    on apply. IDs that resolve neither in cache nor via API stay marked
    ``serial_tracked=False`` and ``"variant {id}"`` for SKUs (best-effort,
    same as if the entity didn't exist). The two parent maps are kept
    separate per CLAUDE.md "Cache IDs are not globally unique".
    """
    if not so_rows:
        return {}, {}
    from katana_public_api_client.api.material import get_material
    from katana_public_api_client.api.product import get_product
    from katana_public_api_client.api.variant import get_variant

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
    for row in so_rows:
        variant = variants_by_id.get(row.variant_id)
        sku = _attr(variant, "sku") if variant is not None else None
        skus[row.id] = sku or f"variant {row.variant_id}"
        if variant is None:
            serial_tracked[row.id] = False
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
    return serial_tracked, skus


async def _resolve_variant_serial_info(
    services: Any, variant_id: int | None
) -> tuple[bool, str]:
    """Return ``(is_serial_tracked, sku)`` for a single variant.

    Single-variant counterpart to ``_resolve_row_serial_info`` used by the
    manufacturing-order path (MOs reference one variant, not per-row). Cache
    misses fall back to a per-ID API fetch so a cold / stale cache doesn't
    silently mis-classify a serial-tracked MO as "OK to mark DONE without
    serials" and surface the original Katana 422 on apply. If the variant
    can't be resolved at all, returns ``(False, f"variant {id}")`` —
    best-effort, same as if the entity didn't exist.
    """
    if variant_id is None:
        return False, "variant ?"
    from katana_public_api_client.api.material import get_material
    from katana_public_api_client.api.product import get_product
    from katana_public_api_client.api.variant import get_variant

    catalog = services.typed_cache.catalog
    variants_by_id: dict[int, Any] = await catalog.get_many_by_ids(
        CachedVariant, {variant_id}, include_deleted=True
    )
    await _fetch_missing_from_api(services, variants_by_id, {variant_id}, get_variant)
    variant = variants_by_id.get(variant_id)
    sku_val = _attr(variant, "sku") if variant is not None else None
    sku = sku_val or f"variant {variant_id}"
    if variant is None:
        return False, sku

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
    return bool(parent and _attr(parent, "serial_tracked")), sku


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

    serial_tracked_by_row, sku_by_row = await _resolve_row_serial_info(
        services, so_rows
    )

    inventory_updates: list[str] = []
    for row in so_rows:
        rid = row.id
        vid = row.variant_id
        qty = row.quantity
        serials = overrides_by_row.get(rid)
        suffix = f" with serials {serials}" if serials else ""
        inventory_updates.append(
            f"Row {rid}: ship {qty} of variant {vid} (full ordered quantity){suffix}"
        )
    if not inventory_updates:
        inventory_updates.append("(no rows on this sales order)")

    warnings: list[str] = []
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
    )
    fulfill_response = await api_create_fulfillment.asyncio_detailed(
        client=services.client, body=fulfill_request
    )
    fulfillment = unwrap_as(fulfill_response, SalesOrderFulfillment)

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
    return _fulfill_response_to_tool_result(response)


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
