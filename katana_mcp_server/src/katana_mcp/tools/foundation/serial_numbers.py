"""Serial-number management tools for Katana MCP Server.

Three leaf-workflow primitives wrapping ``POST/GET/DELETE /serial_numbers``:

- ``add_serial_numbers`` — mint new serial numbers (ManufacturingOrder,
  PurchaseOrderRow) or transfer existing serial numbers between resources
  (SalesOrderRow, StockTransferRow, StockAdjustmentRow). Preview/apply
  pattern.
- ``list_serial_numbers`` — read serial numbers, optionally filtered by
  ``resource_type`` and/or ``resource_id``. Read-only.
- ``delete_serial_numbers`` — detach serial numbers. Idempotent (the
  endpoint returns 204 even for invalid ids). Preview/apply.

Per-resource-type semantics matter: see ``add_serial_numbers`` docstring
and ``CreateSerialNumberResourceType`` description in the OpenAPI spec
for the mint-vs-transfer distinction.
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, ConfigDict, Field

from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.tool_result_utils import make_json_result
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.api.serial_number import (
    create_serial_numbers as api_create_serial_numbers,
    delete_serial_numbers as api_delete_serial_numbers,
    get_all_serial_numbers as api_get_all_serial_numbers,
)
from katana_public_api_client.client_types import UNSET
from katana_public_api_client.domain.converters import unwrap_unset
from katana_public_api_client.models import (
    CreateSerialNumberResourceType,
    CreateSerialNumbersRequest as APICreateSerialNumbersRequest,
    CreateSerialNumbersResponse as APICreateSerialNumbersResponse,
    DeleteSerialNumbersRequest as APIDeleteSerialNumbersRequest,
    SerialNumber as APISerialNumber,
    SerialNumberListResponse,
    SerialNumberResourceType,
)
from katana_public_api_client.utils import unwrap_as

logger = get_logger(__name__)


# ============================================================================
# Tool-facing types
# ============================================================================


# Mint or transfer — the set of ``resource_type`` values the API accepts on
# ``POST /serial_numbers``. Mirrors ``CreateSerialNumberResourceType``.
# ``Production`` IS a valid write target (transfer semantics — verified live
# 2026-07-14, #980: the wire routes it to a production lookup and 422s
# ``UnknownSerialNumber`` for a string that doesn't already exist).
WriteResourceType = Literal[
    "ManufacturingOrder",
    "Production",
    "StockAdjustmentRow",
    "StockTransferRow",
    "PurchaseOrderRow",
    "SalesOrderRow",
]


# Read-side enum — the exact values the ``GET /serial_numbers``
# ``resource_type`` query parameter accepts, mirroring the
# ``SerialNumberResourceType`` schema. Verified against the live API
# 2026-06-09: the gateway 400s on anything else, returning these seven as the
# ``allowedValues``. Note ``Production`` and ``SalesOrderFulfillmentRow`` ARE
# valid filter inputs (a prior version of this enum wrongly excluded them and
# wrongly included ``ProductionIngredient`` / ``ManufacturingOrderRecipeRow`` /
# ``PurchaseOrderRecipeRow`` / ``SystemGenerated``, which the API rejects).
ReadResourceType = Literal[
    "ManufacturingOrder",
    "Production",
    "PurchaseOrderRow",
    "SalesOrderFulfillmentRow",
    "SalesOrderRow",
    "StockAdjustmentRow",
    "StockTransferRow",
]


# Mint resource types create new SerialNumber records; transfer types move
# existing serial-number strings between resources. Surfaced in tool
# docstrings + warnings so callers don't confuse them. Anchored to
# ``WriteResourceType`` to keep the two in sync.
_MINT_RESOURCE_TYPES: frozenset[WriteResourceType] = frozenset(
    {"ManufacturingOrder", "PurchaseOrderRow"}
)
_TRANSFER_RESOURCE_TYPES: frozenset[WriteResourceType] = frozenset(
    {"SalesOrderRow", "StockTransferRow", "StockAdjustmentRow", "Production"}
)


def _semantic_label(resource_type: WriteResourceType) -> Literal["mint", "transfer"]:
    """Return ``"mint"`` or ``"transfer"`` for a write resource type."""
    if resource_type in _MINT_RESOURCE_TYPES:
        return "mint"
    assert resource_type in _TRANSFER_RESOURCE_TYPES, (
        f"{resource_type} is neither a mint nor a transfer type — the two sets "
        "must together cover every WriteResourceType"
    )
    return "transfer"


# Map each write resource type to its parent typed-cache entity name so
# the cached row can be evicted after a successful add/delete. Stays
# narrow on purpose — only resource types where serial-number changes
# are agent-visible via a cached read. After eviction the next watermark
# sync repopulates from Katana; no refetch is triggered from here.
_PARENT_ENTITY_TYPES: dict[WriteResourceType, str | None] = {
    "ManufacturingOrder": "manufacturing_order",
    "SalesOrderRow": "sales_order",
    # PurchaseOrderRow / StockTransferRow / StockAdjustmentRow / Production
    # are deliberately omitted — none of CachedPurchaseOrder/PurchaseOrderRow,
    # CachedStockTransfer/StockTransferRow, the cached stock-adjustment models,
    # nor any cached production model surface a ``serial_numbers`` column, so
    # there is no cached state to invalidate on those writes. The watermark
    # sync handles convergence on subsequent reads.
}


# ============================================================================
# Shared response shape — normalized SerialNumber view
# ============================================================================


class SerialNumberRecord(BaseModel):
    """Normalized view of a SerialNumber.

    ``transaction_id`` may be the literal string ``"undefined"`` on a
    transfer response, and ``resource_id`` may be ``None`` for the same
    reason — these surface as-is, matching the Katana wire response.
    Re-fetch via ``list_serial_numbers`` for the post-landing state.
    """

    id: int
    serial_number: str
    resource_type: str | None = None
    resource_id: int | None = None
    transaction_id: str | None = None
    transaction_date: str | None = None
    quantity_change: int | None = None


def _serial_number_to_record(sn: APISerialNumber) -> SerialNumberRecord:
    """Convert an attrs ``SerialNumber`` to the tool-facing record shape."""
    txn_date = unwrap_unset(sn.transaction_date, None)
    txn_date_iso: str | None
    if txn_date is None:
        txn_date_iso = None
    elif hasattr(txn_date, "isoformat"):
        txn_date_iso = txn_date.isoformat()
    else:
        txn_date_iso = str(txn_date)

    resource_type = unwrap_unset(sn.resource_type, None)
    resource_type_str = (
        resource_type.value
        if isinstance(resource_type, SerialNumberResourceType)
        else resource_type
    )

    return SerialNumberRecord(
        id=unwrap_unset(sn.id, 0) or 0,
        serial_number=unwrap_unset(sn.serial_number, "") or "",
        resource_type=resource_type_str,
        resource_id=unwrap_unset(sn.resource_id, None),
        transaction_id=unwrap_unset(sn.transaction_id, None),
        transaction_date=txn_date_iso,
        quantity_change=unwrap_unset(sn.quantity_change, None),
    )


async def _invalidate_parent_cache(
    context: Context, resource_type: WriteResourceType, resource_id: int
) -> None:
    """Best-effort cache invalidation after a serial-number mutation.

    Serial numbers surface in different cached models depending on the
    parent type. The strategy varies accordingly:

    * **Manufacturing orders** carry ``serial_numbers`` directly on
      ``CachedManufacturingOrder``. Evict that row by id.
    * **Sales-order rows** carry ``serial_numbers`` on
      ``CachedSalesOrderRow`` (not on the parent). Evict the **row**, not
      the parent ``CachedSalesOrder`` — deleting the parent risks it
      vanishing from cache indefinitely because the typed-cache sync is
      watermark-based (``updated_at_min``) and a child-row serial change
      doesn't bump the parent's ``updated_at``.
    * **Purchase orders, stock transfers, stock adjustments** have no
      cached ``serial_numbers`` column. ``_PARENT_ENTITY_TYPES`` omits
      these resource types so the function early-returns; the next
      watermark sync handles convergence on subsequent reads.

    Failures are logged and swallowed — the API write itself succeeded
    and the cache will re-converge on the next sync window.
    """
    entity_type = _PARENT_ENTITY_TYPES.get(resource_type)
    if entity_type is None:
        return

    try:
        services = get_services(context)
        # Import per-entity cached classes lazily — the typed_cache module
        # graph eagerly imports tool code in a few places, so a top-level
        # import would risk a cycle.
        from sqlmodel import delete

        from katana_public_api_client.models_pydantic._generated import (
            CachedManufacturingOrder,
            CachedSalesOrderRow,
        )

        async with services.typed_cache.session() as session:
            if entity_type == "manufacturing_order":
                await session.exec(
                    delete(CachedManufacturingOrder).where(
                        CachedManufacturingOrder.id == resource_id
                    )
                )
            elif entity_type == "sales_order":
                # resource_id is the SOR id; SOR rows carry the
                # serial_numbers JSON column. Evict the row itself — not
                # the parent SalesOrder — so the next read repopulates
                # the row from Katana without orphaning the parent.
                await session.exec(
                    delete(CachedSalesOrderRow).where(
                        CachedSalesOrderRow.id == resource_id
                    )
                )
            await session.commit()
    except Exception as exc:
        logger.warning(
            f"Cache eviction for {entity_type} {resource_id} after serial-number "
            f"mutation failed: {type(exc).__name__}: {exc}. Cache may be stale "
            f"until next sync — does not affect the API write."
        )


# ============================================================================
# Tool 1: add_serial_numbers
# ============================================================================


class AddSerialNumbersRequest(BaseModel):
    """Request to mint or transfer serial numbers to a resource."""

    model_config = ConfigDict(extra="forbid")

    resource_type: WriteResourceType = Field(
        ...,
        description=(
            "Target resource type:\n\n"
            "- **mint**: ManufacturingOrder, PurchaseOrderRow.\n"
            "- **transfer** (move existing strings): SalesOrderRow, "
            "StockTransferRow, StockAdjustmentRow, Production.\n\n"
            "A serial-number string the tenant doesn't already know is "
            "rejected with 422 (observed live 2026-07-14 for SalesOrderRow "
            "and Production). The older 200 + ``failed`` (``reason: MISSING``) "
            "shape was not reproduced — re-verification tracked in #983."
        ),
    )
    resource_id: int = Field(
        ...,
        description=(
            "ID of the target resource (MO id, SOR id, PO row id, "
            "production id, etc.). Non-existent ids return 404 NotFoundError "
            "from the API and propagate as an ``APIError`` subclass "
            "(``katana_public_api_client.utils``)."
        ),
    )
    serial_numbers: list[str] = Field(
        ...,
        min_length=1,
        description=(
            "One or more serial-number strings to create or attach. A string "
            "the tenant doesn't already know is rejected with 422 (see #983 — "
            "the older per-string ``created`` / ``failed`` split was not "
            "reproduced on the live wire)."
        ),
    )
    preview: bool = Field(
        default=True,
        description=(
            "When true (default), returns the planned operation without "
            "calling Katana. Set to false to apply."
        ),
    )


class FailedSerialNumber(BaseModel):
    """Per-string failure block on an add_serial_numbers response."""

    serial_number: str
    reason: str = Field(
        ...,
        description=(
            "Failure code. Observed values: ``DUPLICATE`` (string already "
            "attached to this resource — mint path), ``MISSING`` (string "
            "doesn't exist anywhere in the tenant — transfer path). Other "
            "codes may exist; treat unknown values as forward-compatible "
            "failures."
        ),
    )


class AddSerialNumbersResponse(BaseModel):
    """Response from add_serial_numbers — preview or apply.

    On preview, ``created`` and ``failed`` are both empty and ``is_preview``
    is True. On apply, the response splits the wire result into ``created``
    (from ``successful[]``) and ``failed[]``.
    """

    resource_type: str
    resource_id: int
    semantic: Literal["mint", "transfer"]
    is_preview: bool
    created: list[SerialNumberRecord] = Field(default_factory=list)
    failed: list[FailedSerialNumber] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    message: str


async def _add_serial_numbers_impl(
    request: AddSerialNumbersRequest, context: Context
) -> AddSerialNumbersResponse:
    """Mint or transfer serial numbers to ``resource_id``."""
    semantic = _semantic_label(request.resource_type)
    count = len(request.serial_numbers)
    label = "Previewing" if request.preview else "Applying"
    logger.info(
        f"{label} add_serial_numbers ({semantic}): "
        f"{count} string(s) -> {request.resource_type} {request.resource_id}"
    )

    warnings: list[str] = []
    if semantic == "transfer":
        warnings.append(
            "Transfer semantic: each serial-number string MUST already "
            "exist (typically attached to a ManufacturingOrder). Missing "
            "strings will land in ``failed`` with reason=MISSING."
        )

    if request.preview:
        preview_message = (
            f"Preview: {semantic} {count} serial number(s) on "
            f"{request.resource_type} {request.resource_id}"
        )
        return AddSerialNumbersResponse(
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            semantic=semantic,
            is_preview=True,
            created=[],
            failed=[],
            warnings=warnings,
            next_actions=[
                "Review the planned operation",
                "Set preview=false to apply",
            ],
            message=preview_message,
        )

    services = get_services(context)
    api_request = APICreateSerialNumbersRequest(
        resource_type=CreateSerialNumberResourceType(request.resource_type),
        resource_id=request.resource_id,
        serial_numbers=list(request.serial_numbers),
    )
    api_response = await api_create_serial_numbers.asyncio_detailed(
        client=services.client, body=api_request
    )
    parsed = unwrap_as(api_response, APICreateSerialNumbersResponse)

    created = [_serial_number_to_record(sn) for sn in parsed.successful]
    failed = [
        FailedSerialNumber(
            serial_number=item.serial_number,
            reason=item.reason.value
            if hasattr(item.reason, "value")
            else str(item.reason),
        )
        for item in parsed.failed
    ]

    # Cache invalidation for the parent entity. Best-effort; logged on
    # failure, never re-raised.
    if created or failed:
        await _invalidate_parent_cache(
            context, request.resource_type, request.resource_id
        )

    # Pick the past-tense verb to match what Katana actually did: minted
    # for the create path (new SerialNumber records), transferred for the
    # move path (existing serials re-linked). User-facing messaging only —
    # the response field stays ``created`` for backwards-compatibility.
    verb_past = "Minted" if semantic == "mint" else "Transferred"
    verb_past_lower = verb_past.lower()

    next_actions: list[str] = []
    if created:
        ids = ", ".join(str(r.id) for r in created)
        next_actions.append(
            f"{len(created)} serial number(s) {verb_past_lower} (ids: {ids})"
        )
        if request.resource_type == "ManufacturingOrder":
            next_actions.append(
                "Use ``fulfill_order(order_type='sales', "
                "serial_numbers=[ids])`` to consume these on a sales-order "
                "fulfillment row."
            )
    if failed:
        next_actions.append(
            f"{len(failed)} serial number(s) failed — see ``failed[]`` for "
            f"per-string reasons (DUPLICATE / MISSING)."
        )

    if created and not failed:
        message = (
            f"{verb_past} {len(created)} serial number(s) on "
            f"{request.resource_type} {request.resource_id}"
        )
    elif created and failed:
        message = (
            f"Partial success: {len(created)} {verb_past_lower}, "
            f"{len(failed)} failed on {request.resource_type} "
            f"{request.resource_id}"
        )
    elif failed:
        message = (
            f"No serial numbers {verb_past_lower} — {len(failed)} string(s) "
            f"failed ({semantic} path) on {request.resource_type} "
            f"{request.resource_id}"
        )
    else:
        # API returned an empty response — surface clearly rather than
        # presenting it as success.
        message = (
            f"No serial-number records returned by the API for "
            f"{request.resource_type} {request.resource_id} — "
            f"unexpected wire response; re-fetch via list_serial_numbers."
        )
        warnings.append(message)

    return AddSerialNumbersResponse(
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        semantic=semantic,
        is_preview=False,
        created=created,
        failed=failed,
        warnings=warnings,
        next_actions=next_actions,
        message=message,
    )


@observe_tool
@unpack_pydantic_params
async def add_serial_numbers(
    request: Annotated[AddSerialNumbersRequest, Unpack()], context: Context
) -> ToolResult:
    """Add serial numbers to a resource — mint new ones or transfer existing.

    **Mint vs. transfer semantics (this is the load-bearing distinction):**

    - ``resource_type="ManufacturingOrder"`` or ``"PurchaseOrderRow"`` → **mint**.
      The supplied strings don't need to pre-exist. The API creates new
      SerialNumber records and attaches them to the target.
    - ``resource_type="SalesOrderRow"``, ``"StockTransferRow"``, or
      ``"StockAdjustmentRow"`` → **transfer**. The supplied strings MUST
      already exist (typically previously minted on a ManufacturingOrder).
      The API moves the linkage from the current parent to the target.
      Strings that don't exist anywhere land in ``failed`` with
      ``reason=MISSING`` — the call still succeeds.

    **Exception — a ``SalesOrderRow`` fulfilled from a linked manufacturing
    order:** when the target SO row's production is driven by a linked MO
    (the common serial-tracked close-out case — a finished good came off an
    MO with the serial already minted on it), Katana rejects the transfer
    outright with ``422 "SalesOrderRow <id> is linked, serial info must be
    updated on MO"``. Serials on such a row are controlled by the MO, and
    ``fulfill_order(order_type="sales", rows=[{"sales_order_row_id": <id>,
    "serial_numbers": [<sn_id>]}])`` likewise 422s ("serial numbers have
    already been assigned"). There is no
    public-API path to complete that MO→SO transfer today; perform it from
    the Katana UI ("Deliver all"), which moves the serial atomically. (The
    transfer path above works normally for SO rows *not* linked to an MO.)

    Partial failure is possible: any string the API rejects (DUPLICATE on
    the mint path, MISSING on the transfer path) lands in ``failed`` while
    the rest succeed.

    Two-step flow: preview=true (default) returns the planned operation
    without calling Katana; preview=false applies.
    """
    response = await _add_serial_numbers_impl(request, context)
    return make_json_result(response)


# ============================================================================
# Tool 2: list_serial_numbers
# ============================================================================


class ListSerialNumbersRequest(BaseModel):
    """Request to list / filter serial numbers."""

    model_config = ConfigDict(extra="forbid")

    resource_type: ReadResourceType | None = Field(
        default=None,
        description=(
            "Filter by resource type. Limited to the values Katana's "
            "``resource_type`` query parameter accepts — the response "
            "enum is broader (it can return ``Production`` and "
            "``SalesOrderFulfillmentRow`` records) but those values are "
            "not valid filter inputs. To inspect those record types, "
            "omit ``resource_type`` and pass ``resource_id``. Omit both "
            "to list across all types."
        ),
    )
    resource_id: int | None = Field(
        default=None,
        description=(
            "Filter by resource ID. Can be combined with ``resource_type`` "
            "for tight scope, or used alone to find an SN regardless of type."
        ),
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=250,
        description="Max rows to return (default 50, max 250).",
    )
    page: int = Field(default=1, ge=1, description="1-based page index.")


class ListSerialNumbersResponse(BaseModel):
    """Response with a list of serial numbers. Katana's list endpoint has
    no ``total_count`` field — clients paginate forward until ``data=[]``."""

    serial_numbers: list[SerialNumberRecord]
    page: int
    limit: int
    resource_type: str | None = None
    resource_id: int | None = None


async def _list_serial_numbers_impl(
    request: ListSerialNumbersRequest, context: Context
) -> ListSerialNumbersResponse:
    """Pass-through list query against ``GET /serial_numbers``."""
    services = get_services(context)
    api_response = await api_get_all_serial_numbers.asyncio_detailed(
        client=services.client,
        resource_type=(
            SerialNumberResourceType(request.resource_type)
            if request.resource_type is not None
            else UNSET
        ),
        resource_id=(request.resource_id if request.resource_id is not None else UNSET),
        limit=request.limit,
        page=request.page,
    )
    parsed = unwrap_as(api_response, SerialNumberListResponse)
    rows = unwrap_unset(parsed.data, [])

    return ListSerialNumbersResponse(
        serial_numbers=[_serial_number_to_record(sn) for sn in rows],
        page=request.page,
        limit=request.limit,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
    )


@observe_tool
@unpack_pydantic_params
async def list_serial_numbers(
    request: Annotated[ListSerialNumbersRequest, Unpack()], context: Context
) -> ToolResult:
    """List serial numbers, optionally filtered by resource_type and/or resource_id.

    Read-only diagnostic tool. Use to confirm which serial-number strings
    are currently attached to a manufacturing order, sales-order row, etc.,
    or to search across the tenant (omit both filters).

    Filter behavior:

    - Both filters set → scoped to that exact ``(type, id)``.
    - ``resource_type`` alone → ALL serial numbers of that type
      (paginated; never 422).
    - ``resource_id`` alone → narrows to that resource regardless of type.
    - Neither filter → all serial numbers in the tenant (paginated).
    - Page beyond data → returns an empty ``serial_numbers`` list.

    Katana's list endpoint does not return a total_count; callers paginate
    forward until ``serial_numbers`` is empty.
    """
    response = await _list_serial_numbers_impl(request, context)
    return make_json_result(response)


# ============================================================================
# Tool 3: delete_serial_numbers
# ============================================================================


class DeleteSerialNumbersRequest(BaseModel):
    """Request to detach serial numbers from a resource."""

    model_config = ConfigDict(extra="forbid")

    resource_type: WriteResourceType = Field(
        ...,
        description=(
            "Resource the serial numbers are currently attached to. The API "
            "does not validate this against the SN's actual parent — see "
            "``delete_serial_numbers`` docstring."
        ),
    )
    resource_id: int = Field(
        ..., description="ID of the resource the serial numbers belong to."
    )
    ids: list[int] = Field(
        ...,
        min_length=1,
        description=(
            "Serial-number record IDs to delete. Look up via "
            "``list_serial_numbers``. The API does not validate ids — invalid "
            "ones return 204 silently."
        ),
    )
    preview: bool = Field(
        default=True,
        description=(
            "When true (default), returns the planned operation without "
            "calling Katana. Set to false to apply."
        ),
    )


class DeleteSerialNumbersResponse(BaseModel):
    """Response from delete_serial_numbers — preview or apply.

    Echoes the requested IDs as ``deleted_ids`` because Katana's DELETE
    endpoint returns 204 No Content unconditionally — there's no way to
    detect which ids were actually present at delete time. To strongly
    verify deletion, follow up with ``list_serial_numbers(resource_id=..., resource_type=...)``
    and assert the deleted ids are absent.
    """

    resource_type: str
    resource_id: int
    deleted_ids: list[int]
    is_preview: bool
    warnings: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    message: str


async def _delete_serial_numbers_impl(
    request: DeleteSerialNumbersRequest, context: Context
) -> DeleteSerialNumbersResponse:
    """Detach serial numbers from a resource."""
    count = len(request.ids)
    label = "Previewing" if request.preview else "Applying"
    logger.info(
        f"{label} delete_serial_numbers: {count} id(s) from "
        f"{request.resource_type} {request.resource_id}"
    )

    # The DELETE endpoint returns 204 even for invalid ids, mismatched
    # parent resources, etc. Surface this loudly so callers know to verify
    # via a follow-up list call if they need strong confirmation.
    warnings = [
        "Katana's DELETE /serial_numbers does not validate the request — "
        "it returns 204 for invalid ids and mismatched parent resources. "
        "For strong confirmation, follow up with list_serial_numbers."
    ]

    if request.preview:
        return DeleteSerialNumbersResponse(
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            deleted_ids=list(request.ids),
            is_preview=True,
            warnings=warnings,
            next_actions=[
                "Review the planned deletion",
                "Set preview=false to apply",
            ],
            message=(
                f"Preview: delete {count} serial number(s) from "
                f"{request.resource_type} {request.resource_id}"
            ),
        )

    services = get_services(context)
    # ``DeleteSerialNumbersRequest`` uses the broader read enum on the wire.
    api_request = APIDeleteSerialNumbersRequest(
        resource_type=SerialNumberResourceType(request.resource_type),
        resource_id=request.resource_id,
        ids=list(request.ids),
    )
    response = await api_delete_serial_numbers.asyncio_detailed(
        client=services.client, body=api_request
    )
    # 204 No Content is the expected success — anything else flows through
    # ``unwrap_as`` and raises a typed APIError / ValidationError.
    if response.status_code not in (200, 204):
        # Use unwrap_as for its error-routing side effects (raises on 4xx/5xx).
        unwrap_as(response, type(None))

    # Best-effort cache invalidation.
    await _invalidate_parent_cache(context, request.resource_type, request.resource_id)

    return DeleteSerialNumbersResponse(
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        deleted_ids=list(request.ids),
        is_preview=False,
        warnings=warnings,
        next_actions=[
            f"{count} serial-number id(s) submitted for deletion",
            (
                "Verify via list_serial_numbers if strong confirmation "
                "is required (DELETE is unconditionally idempotent)."
            ),
        ],
        message=(
            f"Submitted {count} serial-number id(s) for deletion from "
            f"{request.resource_type} {request.resource_id} — Katana returned "
            "204 (unconditionally idempotent; cannot confirm individual ids)"
        ),
    )


@observe_tool
@unpack_pydantic_params
async def delete_serial_numbers(
    request: Annotated[DeleteSerialNumbersRequest, Unpack()], context: Context
) -> ToolResult:
    """Delete (detach) serial numbers from a resource.

    **Idempotency caveat (load-bearing):** Katana's DELETE endpoint returns
    204 No Content for every well-formed request — including invalid ids,
    already-deleted ids, mixed valid+invalid batches, and even
    ``resource_id`` / ``resource_type`` mismatches against the SN's actual
    parent. The API gives no signal for partial failure or non-existence.
    For strong confirmation, follow up with
    ``list_serial_numbers(resource_id=..., resource_type=...)`` and assert
    the deleted ids are absent.

    Destructive — surfaced via the ``destructiveHint`` annotation so hosts
    can confirm with the user before invocation.

    Two-step flow: preview=true (default), preview=false to apply.
    """
    response = await _delete_serial_numbers_impl(request, context)
    return make_json_result(response)


# ============================================================================
# Registration
# ============================================================================


def register_tools(mcp: FastMCP) -> None:
    """Register the three serial-number tools with the FastMCP instance."""
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
    _destructive = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
        openWorldHint=True,
    )

    register_preview_tool(
        mcp,
        add_serial_numbers,
        tags={"serial_numbers", "write"},
        annotations=_create,
    )
    mcp.tool(tags={"serial_numbers", "read"}, annotations=_read)(list_serial_numbers)
    register_preview_tool(
        mcp,
        delete_serial_numbers,
        tags={"serial_numbers", "write", "destructive"},
        annotations=_destructive,
    )


__all__ = [
    "AddSerialNumbersRequest",
    "AddSerialNumbersResponse",
    "DeleteSerialNumbersRequest",
    "DeleteSerialNumbersResponse",
    "FailedSerialNumber",
    "ListSerialNumbersRequest",
    "ListSerialNumbersResponse",
    "SerialNumberRecord",
    "_add_serial_numbers_impl",
    "_delete_serial_numbers_impl",
    "_list_serial_numbers_impl",
    "add_serial_numbers",
    "delete_serial_numbers",
    "list_serial_numbers",
    "register_tools",
]
