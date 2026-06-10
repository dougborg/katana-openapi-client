"""Bin transfer + bin inventory tools for Katana MCP Server.

Bin transfers move stock **between storage bins within a single location**
(contrast stock transfers, which move between locations). Foundation tools
covering the full lifecycle plus the supporting bin surfaces:

- create_bin_transfer: Create a transfer (with rows) using preview/apply
- list_bin_transfers: List transfers with paging, date, status filters
- modify_bin_transfer: Unified modification — header fields, status
  transition, and row-level CRUD in a single call. Unlike stock-transfer
  rows, bin transfer rows are fully mutable post-creation
  (``POST/PATCH/DELETE /bin_transfer_rows``).
- delete_bin_transfer: Destructive sibling of modify_bin_transfer.
- list_bin_inventory: Per-bin stock levels at VARIANT / BATCH /
  SERIAL_NUMBER granularity (live read — see note below).
- list_storage_bins / create_storage_bin: The bins themselves
  (``/bin_locations``).

Bin inventory is a live read, not a cached entity: ``GET /bin_inventory``
rows carry no ``id`` / ``updated_at``, so the typed cache's
watermark-and-upsert machinery has nothing to key on.
"""

from __future__ import annotations

import asyncio
import datetime as _datetime
from datetime import datetime
from decimal import Decimal, InvalidOperation
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
    run_delete_plan,
    run_modify_plan,
    safe_fetch_for_diff,
    unset_dict,
)
from katana_mcp.tools.list_coercion import CoercedIntListOpt
from katana_mcp.tools.tool_result_utils import (
    UI_META,
    PaginationMeta,
    apply_date_window_filters,
    coerce_enum,
    enum_to_str,
    iso_or_none,
    make_json_result,
    parse_request_dates,
    resolve_entity_name,
)
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.api.bin_transfer import (
    create_bin_transfer as api_create_bin_transfer,
    create_bin_transfer_row as api_create_bin_transfer_row,
    delete_bin_transfer as api_delete_bin_transfer,
    delete_bin_transfer_row as api_delete_bin_transfer_row,
    get_bin_transfer as api_get_bin_transfer,
    get_bin_transfer_row as api_get_bin_transfer_row,
    update_bin_transfer as api_update_bin_transfer,
    update_bin_transfer_row as api_update_bin_transfer_row,
    update_bin_transfer_status as api_update_bin_transfer_status,
)
from katana_public_api_client.api.storage_bin import (
    create_storage_bin as api_create_storage_bin,
    get_all_storage_bins as api_get_all_storage_bins,
    get_bin_inventory as api_get_bin_inventory,
)
from katana_public_api_client.client_types import UNSET
from katana_public_api_client.domain.converters import to_unset, unwrap_unset
from katana_public_api_client.models import (
    BinInventoryGranularity,
    BinTransfer,
    BinTransferRow,
    BinTransferRowCreateNested,
    BinTransferStatus,
    BinTransferTraceabilityRequest,
    CreateBinTransferRequest as APICreateBinTransferRequest,
    CreateBinTransferRowRequest as APICreateBinTransferRowRequest,
    StorageBinCreate,
    StorageBinResponse,
    UpdateBinTransferRequest as APIUpdateBinTransferRequest,
    UpdateBinTransferRowRequest as APIUpdateBinTransferRowRequest,
    UpdateBinTransferStatusRequest as APIUpdateBinTransferStatusRequest,
)
from katana_public_api_client.utils import unwrap, unwrap_as, unwrap_data

logger = get_logger(__name__)


# Status literal shared across tools. Katana's wire enum for bin transfers
# is already uppercase (``CREATED`` / ``IN_TRANSIT`` / ``DONE``) — unlike
# stock transfers, no tool-literal ↔ wire-value mapping table is needed.
StatusLiteral = Literal["CREATED", "IN_TRANSIT", "DONE"]

GranularityLiteral = Literal["VARIANT", "BATCH", "SERIAL_NUMBER"]


def _quantity_to_wire(quantity: float) -> str:
    """Emit a non-exponent decimal string for a wire quantity field.

    Same boundary conversion as the stock-transfer rows: going through
    ``Decimal(str(float))`` preserves the shortest round-trip representation,
    then ``format(..., "f")`` emits decimal form (no exponent) at full
    precision.
    """
    return format(Decimal(str(quantity)), "f")


def _decimal_or_value(value: Any) -> Any:
    """Canonicalize any numeric-ish value to ``Decimal`` for comparison.

    Verification transform for wire quantities: Katana echoes quantities as
    decimal strings that may lack a decimal point (``"3"``), which
    ``_normalize`` deliberately leaves as strings — so the requested float
    ``3.0`` would spuriously mismatch. Idempotent; non-numeric values pass
    through unchanged.
    """
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return value


def _traceability_cmp(value: Any) -> Any:
    """Canonicalize a traceability list for verification comparison.

    The requested side is a list of plain dicts (pydantic ``model_dump``);
    the echoed side is a list of attrs ``BinTransferTraceability`` objects.
    Map both to a sorted list of ``(batch_id, serial_number_id, quantity)``
    tuples so only genuine divergence flags ``verified=False``.
    """
    if not value:
        return None
    canonical = []
    for item in value:
        data = item.to_dict() if hasattr(item, "to_dict") else dict(item)
        canonical.append(
            (
                unwrap_unset(data.get("batch_id"), None),
                unwrap_unset(data.get("serial_number_id"), None),
                _decimal_or_value(unwrap_unset(data.get("quantity"), None)),
            )
        )
    return sorted(canonical, key=lambda entry: (str(entry[0]), str(entry[1])))


_ROW_VERIFY_TRANSFORMS = {
    "quantity": _decimal_or_value,
    "traceability": _traceability_cmp,
}


# ============================================================================
# Shared response models
# ============================================================================


class BinTransferRowInfo(BaseModel):
    """Summary of a bin transfer line item."""

    id: int | None = None
    variant_id: int | None = None
    quantity: float | None = None
    source_bin_location_id: int | None = None
    target_bin_location_id: int | None = None
    traceability: list[dict[str, Any]] | None = None


class BinTransferSummary(BaseModel):
    """Summary row for a bin transfer in a list."""

    id: int
    bin_transfer_number: str | None
    location_id: int | None
    status: str | None
    created_date: str | None
    departed_at: str | None
    arrived_at: str | None
    additional_info: str | None
    created_at: str | None
    row_count: int
    rows: list[BinTransferRowInfo] | None = None


# ============================================================================
# Tool 1: create_bin_transfer
# ============================================================================


class BinTransferTraceabilityInput(BaseModel):
    """Batch/serial allocation for a tracked variant on a bin transfer row."""

    model_config = ConfigDict(extra="forbid")

    batch_id: int | None = Field(
        default=None, description="Batch ID being moved (batch-tracked variants)"
    )
    serial_number_id: int | None = Field(
        default=None,
        description="Serial number ID being moved (serial-tracked variants)",
    )
    quantity: float = Field(
        ...,
        description="Quantity drawn from this batch / serial (serials use 1)",
        gt=0,
    )


class BinTransferRowInput(BaseModel):
    """Line item for a bin transfer."""

    model_config = ConfigDict(extra="forbid")

    variant_id: int = Field(..., description="Variant ID to move")
    quantity: float = Field(..., description="Quantity to move", gt=0)
    source_bin_location_id: int | None = Field(
        default=None,
        description=(
            "Bin the stock moves from. Look up via `list_storage_bins`. "
            "None means unassigned (un-binned) stock."
        ),
    )
    target_bin_location_id: int | None = Field(
        default=None,
        description=(
            "Bin the stock moves to. Look up via `list_storage_bins`. "
            "None moves the stock to the location's unassigned pool."
        ),
    )
    traceability: list[BinTransferTraceabilityInput] | None = Field(
        default=None,
        description=(
            "Batch/serial allocations for tracked variants — each entry picks "
            "a batch_id or serial_number_id and a quantity."
        ),
    )


class CreateBinTransferRequest(BaseModel):
    """Request to create a bin transfer within one location."""

    model_config = ConfigDict(extra="forbid")

    location_id: int = Field(
        ...,
        description=(
            "Location the transfer occurs within (bins on both sides must "
            "belong to it). Look up via `list_locations`."
        ),
    )
    rows: list[BinTransferRowInput] = Field(
        ..., description="Line items to move between bins", min_length=1
    )
    bin_transfer_number: str | None = Field(
        default=None,
        description=(
            "Optional transfer number. When omitted, Katana assigns one server-side."
        ),
    )
    additional_info: str | None = Field(
        default=None, description="Additional notes (optional)"
    )
    created_date: WireDatetime | None = Field(
        default=None,
        description=(
            "Date the transfer record was created — ISO 8601 datetime. Leave "
            "None to let Katana stamp the current time server-side; supply "
            "for back-fills."
        ),
    )
    preview: bool = Field(
        default=True,
        description="If true (default), returns preview. If false, creates the transfer.",
    )


class BinTransferResponse(BaseModel):
    """Response from a bin transfer create operation."""

    id: int | None = None
    bin_transfer_number: str | None = None
    location_id: int | None = None
    location_name: str | None = None
    status: str | None = None
    item_count: int | None = None
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


def _transfer_to_response(
    transfer: BinTransfer, *, message: str, is_preview: bool = False
) -> BinTransferResponse:
    """Build a BinTransferResponse from an attrs BinTransfer."""
    rows = unwrap_unset(transfer.bin_transfer_rows, None)
    return BinTransferResponse(
        id=transfer.id,
        bin_transfer_number=transfer.bin_transfer_number,
        location_id=transfer.location_id,
        status=enum_to_str(unwrap_unset(transfer.status, None)),
        item_count=len(rows) if rows is not None else None,
        is_preview=is_preview,
        message=message,
    )


def _build_traceability_requests(
    items: list[BinTransferTraceabilityInput],
) -> list[BinTransferTraceabilityRequest]:
    """Convert pydantic traceability inputs to attrs request objects."""
    return [
        BinTransferTraceabilityRequest(
            batch_id=to_unset(item.batch_id),
            serial_number_id=to_unset(item.serial_number_id),
            quantity=_quantity_to_wire(item.quantity),
        )
        for item in items
    ]


def _build_nested_rows(
    rows: list[BinTransferRowInput],
) -> list[BinTransferRowCreateNested]:
    """Convert pydantic row inputs to attrs nested-create rows."""
    return [
        BinTransferRowCreateNested(
            variant_id=row.variant_id,
            quantity=_quantity_to_wire(row.quantity),
            source_bin_location_id=to_unset(row.source_bin_location_id),
            target_bin_location_id=to_unset(row.target_bin_location_id),
            traceability=(
                _build_traceability_requests(row.traceability)
                if row.traceability
                else UNSET
            ),
        )
        for row in rows
    ]


def _same_bin_row_warnings(rows: list[BinTransferRowInput]) -> list[str]:
    """Warn about rows whose source and target bin are the same (no-op move)."""
    offenders = [
        str(idx)
        for idx, row in enumerate(rows, start=1)
        if row.source_bin_location_id is not None
        and row.source_bin_location_id == row.target_bin_location_id
    ]
    if not offenders:
        return []
    return [
        f"Row(s) {', '.join(offenders)} have the same source and target bin — "
        "the move would be a no-op for those rows."
    ]


async def _create_bin_transfer_impl(
    request: CreateBinTransferRequest, context: Context
) -> BinTransferResponse:
    """Implementation of create_bin_transfer tool."""
    logger.info(
        f"{'Previewing' if request.preview else 'Creating'} bin transfer "
        f"{request.bin_transfer_number or '(auto)'} "
        f"(location {request.location_id}, {len(request.rows)} row(s))"
    )

    from katana_public_api_client.models_pydantic._generated import CachedLocation

    services = get_services(context)
    location_name, location_warn = await resolve_entity_name(
        services.typed_cache.catalog,
        CachedLocation,
        request.location_id,
        entity_label="Location",
    )
    warnings: list[str] = [w for w in (location_warn,) if w]
    warnings.extend(_same_bin_row_warnings(request.rows))

    location_label = (
        f"{location_name} (id={request.location_id})"
        if location_name
        else f"location id={request.location_id}"
    )
    item_count = len(request.rows)

    if request.preview:
        return BinTransferResponse(
            bin_transfer_number=request.bin_transfer_number,
            location_id=request.location_id,
            location_name=location_name,
            status="CREATED",
            item_count=item_count,
            is_preview=True,
            warnings=warnings,
            next_actions=[
                "Review the transfer details",
                "Set preview=false to create the bin transfer",
            ],
            message=(
                f"Preview: Bin transfer with {item_count} row(s) within "
                f"{location_label}"
            ),
        )

    api_request = APICreateBinTransferRequest(
        location_id=request.location_id,
        bin_transfer_number=to_unset(request.bin_transfer_number),
        additional_info=to_unset(request.additional_info),
        created_date=to_unset(request.created_date),
        bin_transfer_rows=_build_nested_rows(request.rows),
    )

    response = await api_create_bin_transfer.asyncio_detailed(
        client=services.client, body=api_request
    )
    transfer = unwrap_as(response, BinTransfer)
    logger.info(f"Created bin transfer ID {transfer.id}")

    result = _transfer_to_response(
        transfer,
        message=f"Successfully created bin transfer (ID: {transfer.id})",
    )
    result.location_name = location_name
    result.warnings = warnings
    result.next_actions = [
        f"Bin transfer created with ID {transfer.id}",
        (
            "Use modify_bin_transfer with update_status to transition it "
            "through IN_TRANSIT → DONE"
        ),
    ]
    return result


@observe_tool
@unpack_pydantic_params
async def create_bin_transfer(
    request: Annotated[CreateBinTransferRequest, Unpack()], context: Context
) -> ToolResult:
    """Create a bin transfer moving inventory between bins within one location.

    Two-step flow: preview=true (default) to preview, preview=false to create.
    Requires location_id and at least one row with variant_id + quantity.
    Rows can carry source/target bin IDs (see `list_storage_bins`) and
    batch/serial `traceability` entries for tracked variants.

    To move stock **between locations**, use create_stock_transfer instead.
    """
    response = await _create_bin_transfer_impl(request, context)
    return make_json_result(response)


# ============================================================================
# Tool 2: list_bin_transfers
# ============================================================================


class ListBinTransfersRequest(BaseModel):
    """Request to list/filter bin transfers (list-tool pattern v2)."""

    model_config = ConfigDict(extra="forbid")

    # Paging
    limit: int = Field(
        default=50,
        ge=1,
        description="Max rows to return (default 50, min 1). When `page` is set, acts as page size.",
    )
    page: int | None = Field(
        default=None,
        ge=1,
        description="Page number (1-based). When set, disables auto-pagination; use with `limit` as page size.",
    )

    # Domain filters
    ids: CoercedIntListOpt = Field(
        default=None,
        description=(
            "Filter by explicit list of bin transfer IDs. "
            "JSON array of integers, e.g. [101, 202, 303]."
        ),
    )
    status: StatusLiteral | None = Field(
        default=None,
        description="Filter by transfer status (CREATED, IN_TRANSIT, DONE)",
    )
    location_id: int | None = Field(
        default=None,
        description=("Filter by location ID. Look up via `list_locations`."),
    )
    bin_transfer_number: str | None = Field(
        default=None, description="Filter by exact bin transfer number"
    )
    include_deleted: bool = Field(
        default=False,
        description=(
            "When true, include soft-deleted bin transfers. Default "
            "`False` matches the peer list-tool convention (#539, #484)."
        ),
    )

    # Time-window filters
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

    # Row inclusion
    include_rows: bool = Field(
        default=False,
        description="When true, populate row-level detail on each summary.",
    )


class ListBinTransfersResponse(BaseModel):
    """Response containing a list of bin transfers."""

    transfers: list[BinTransferSummary]
    total_count: int
    pagination: PaginationMeta | None = None


_BIN_TRANSFER_DATE_FIELDS = (
    "created_after",
    "created_before",
    "updated_after",
    "updated_before",
)


def _traceability_dicts(value: Any) -> list[dict[str, Any]] | None:
    """Coerce a cached traceability JSON column to plain dicts for output."""
    if not value:
        return None
    return [
        item.model_dump() if hasattr(item, "model_dump") else dict(item)
        for item in value
    ]


def _apply_bin_transfer_filters(
    stmt: Any,
    request: ListBinTransfersRequest,
    parsed_dates: dict[str, datetime | None],
) -> Any:
    """Translate request filters into WHERE clauses on a CachedBinTransfer query.

    Shared by the data SELECT and the COUNT SELECT so pagination totals
    reflect exactly the same filter set as the data rows. The tool-facing
    ``StatusLiteral`` values equal Katana's wire enum values, so the
    filter only needs the literal coerced to the cached enum type.
    """

    from katana_public_api_client.models_pydantic._generated import (
        BinTransferStatus as CachedBinTransferStatus,
        CachedBinTransfer,
    )

    if request.ids is not None:
        stmt = stmt.where(CachedBinTransfer.id.in_(request.ids))
    if request.status is not None:
        stmt = stmt.where(
            CachedBinTransfer.status
            == coerce_enum(request.status, CachedBinTransferStatus, "status")
        )
    if request.location_id is not None:
        stmt = stmt.where(CachedBinTransfer.location_id == request.location_id)
    if request.bin_transfer_number is not None:
        stmt = stmt.where(
            CachedBinTransfer.bin_transfer_number == request.bin_transfer_number
        )
    if not request.include_deleted:
        stmt = stmt.where(CachedBinTransfer.deleted_at.is_(None))

    return apply_date_window_filters(
        stmt,
        parsed_dates,
        ge_pairs={
            "created_after": CachedBinTransfer.created_at,
            "updated_after": CachedBinTransfer.updated_at,
        },
        le_pairs={
            "created_before": CachedBinTransfer.created_at,
            "updated_before": CachedBinTransfer.updated_at,
        },
    )


async def _list_bin_transfers_impl(
    request: ListBinTransfersRequest, context: Context
) -> ListBinTransfersResponse:
    """List bin transfers with filters via the typed cache.

    ``ensure_bin_transfers_synced`` always runs a full fetch — the
    endpoint has no ``updated_at_min`` support (see ``_BIN_TRANSFER_SPEC``).
    Filters translate to indexed SQL. See ADR-0018.
    """
    from sqlalchemy.orm import selectinload
    from sqlmodel import func, select

    from katana_mcp.typed_cache import ensure_bin_transfers_synced
    from katana_public_api_client.models_pydantic._generated import (
        CachedBinTransfer,
        CachedBinTransferRow,
    )

    services = get_services(context)

    await ensure_bin_transfers_synced(services.client, services.typed_cache)

    parsed_dates = parse_request_dates(request, _BIN_TRANSFER_DATE_FIELDS)

    # When ``include_rows`` is set, ``selectinload`` eager-loads the
    # children, so ``len(transfer.bin_transfer_rows)`` is free at
    # materialization time and we skip the correlated COUNT subquery.
    # Both paths filter ``deleted_at IS NULL`` so soft-deleted rows
    # never surface (see #803).
    if request.include_rows:
        stmt = select(CachedBinTransfer).options(
            selectinload(
                CachedBinTransfer.bin_transfer_rows.and_(
                    CachedBinTransferRow.deleted_at.is_(None)
                )
            )
        )
    else:
        row_count_subq = (
            select(func.count(CachedBinTransferRow.id))
            .where(CachedBinTransferRow.bin_transfer_id == CachedBinTransfer.id)
            .where(CachedBinTransferRow.deleted_at.is_(None))
            .correlate(CachedBinTransfer)
            .scalar_subquery()
            .label("row_count")
        )
        stmt = select(CachedBinTransfer, row_count_subq)
    stmt = _apply_bin_transfer_filters(stmt, request, parsed_dates)
    stmt = stmt.order_by(
        CachedBinTransfer.created_at.desc(),
        CachedBinTransfer.id.desc(),
    )
    if request.page is not None:
        stmt = stmt.offset((request.page - 1) * request.limit).limit(request.limit)
    else:
        stmt = stmt.limit(request.limit)

    async with services.typed_cache.session() as session:
        data_result = await session.exec(stmt)
        if request.include_rows:
            cached_transfers = list(data_result.all())
            transfers_with_counts: list[tuple[CachedBinTransfer, int]] = [
                (t, len(t.bin_transfer_rows)) for t in cached_transfers
            ]
        else:
            transfers_with_counts = data_result.all()

        pagination: PaginationMeta | None = None
        if request.page is not None:
            count_stmt = _apply_bin_transfer_filters(
                select(func.count()).select_from(CachedBinTransfer),
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

    summaries: list[BinTransferSummary] = []
    for transfer, row_count in transfers_with_counts:
        row_infos: list[BinTransferRowInfo] | None = None
        if request.include_rows:
            row_infos = [
                BinTransferRowInfo(
                    id=r.id,
                    variant_id=r.variant_id,
                    quantity=float(r.quantity) if r.quantity is not None else None,
                    source_bin_location_id=r.source_bin_location_id,
                    target_bin_location_id=r.target_bin_location_id,
                    traceability=_traceability_dicts(r.traceability),
                )
                for r in transfer.bin_transfer_rows
            ]
        summaries.append(
            BinTransferSummary(
                id=transfer.id,
                bin_transfer_number=transfer.bin_transfer_number,
                location_id=transfer.location_id,
                status=enum_to_str(transfer.status),
                created_date=iso_or_none(transfer.created_date),
                departed_at=iso_or_none(transfer.departed_at),
                arrived_at=iso_or_none(transfer.arrived_at),
                additional_info=transfer.additional_info,
                created_at=iso_or_none(transfer.created_at),
                row_count=row_count,
                rows=row_infos,
            )
        )

    return ListBinTransfersResponse(
        transfers=summaries,
        total_count=len(summaries),
        pagination=pagination,
    )


@observe_tool
@unpack_pydantic_params
async def list_bin_transfers(
    request: Annotated[ListBinTransfersRequest, Unpack()], context: Context
) -> ToolResult:
    """List bin transfers with filters — returns multiple transfers for discovery or bulk review.

    Bin transfers move stock between bins **within** a location (for
    between-location moves see list_stock_transfers).

    **Available filters:** `status` (CREATED / IN_TRANSIT / DONE),
    `location_id`, `bin_transfer_number`, `ids`,
    `created_after`/`created_before`, `updated_after`/`updated_before`.

    **Paging:**
    - `limit` caps the number of rows (default 50, min 1).
    - `page=N` returns a single page; the response includes `pagination`
      metadata (total_records, total_pages, first/last flags) computed
      via SQL COUNT against the same filter predicate.

    Pass `include_rows=True` to populate per-transfer line items
    (variant, quantity, source/target bin, batch/serial traceability).
    """
    response = await _list_bin_transfers_impl(request, context)
    return make_json_result(response)


# ============================================================================
# Tool: modify_bin_transfer — unified modification surface
# ============================================================================


class BinTransferOperation(StrEnum):
    """Operation names emitted on ActionSpecs by ``modify_bin_transfer`` /
    ``delete_bin_transfer`` plan builders."""

    UPDATE_HEADER = "update_header"
    UPDATE_STATUS = "update_status"
    ADD_ROW = "add_row"
    UPDATE_ROW = "update_row"
    DELETE_ROW = "delete_row"
    DELETE = "delete"


class BinTransferHeaderPatch(BaseModel):
    """Body fields to patch on a bin transfer.

    Status is excluded — Katana exposes it via a separate
    ``PATCH /bin_transfers/{id}/status`` endpoint, surfaced as the
    ``update_status`` sub-payload.
    """

    model_config = ConfigDict(extra="forbid")

    bin_transfer_number: str | None = Field(
        default=None, description="New bin transfer number"
    )
    location_id: int | None = Field(
        default=None,
        description=(
            "New location ID. Bins referenced by existing rows must belong "
            "to the new location — Katana rejects the move otherwise."
        ),
    )
    additional_info: str | None = Field(
        default=None, description="New additional info/notes"
    )
    created_date: WireDatetime | None = Field(
        default=None,
        description="New created date — ISO 8601 datetime (back-fills).",
    )
    departed_at: WireDatetime | None = Field(
        default=None,
        description="Timestamp the stock left the source bins — ISO 8601 datetime.",
    )
    arrived_at: WireDatetime | None = Field(
        default=None,
        description="Timestamp the stock reached the target bins — ISO 8601 datetime.",
    )


class BinTransferStatusPatch(BaseModel):
    """Status-transition sub-payload — maps to the dedicated status endpoint."""

    model_config = ConfigDict(extra="forbid")

    new_status: StatusLiteral = Field(
        ...,
        description=(
            "Target status. Valid transitions are governed by Katana — typical "
            "flow is CREATED → IN_TRANSIT → DONE."
        ),
    )


class BinTransferRowAdd(BaseModel):
    """New line item to append to an existing bin transfer."""

    model_config = ConfigDict(extra="forbid")

    variant_id: int = Field(..., description="Variant ID to move")
    quantity: float = Field(..., description="Quantity to move", gt=0)
    source_bin_location_id: int | None = Field(
        default=None,
        description="Bin the stock moves from (see `list_storage_bins`).",
    )
    target_bin_location_id: int | None = Field(
        default=None,
        description="Bin the stock moves to (see `list_storage_bins`).",
    )
    traceability: list[BinTransferTraceabilityInput] | None = Field(
        default=None,
        description="Batch/serial allocations for tracked variants.",
    )


class BinTransferRowUpdate(BaseModel):
    """Patch to an existing bin transfer row."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Bin transfer row ID to update")
    variant_id: int | None = Field(default=None, description="New variant ID")
    quantity: float | None = Field(default=None, description="New quantity", gt=0)
    source_bin_location_id: int | None = Field(
        default=None, description="New source bin ID"
    )
    target_bin_location_id: int | None = Field(
        default=None, description="New target bin ID"
    )
    traceability: list[BinTransferTraceabilityInput] | None = Field(
        default=None,
        description=(
            "Replacement batch/serial allocations. Supply the full desired "
            "list — it replaces the row's existing allocations."
        ),
    )


class ModifyBinTransferRequest(ConfirmableRequest):
    """Unified modification request for a bin transfer.

    Sub-payload slots cover header body fields, row-level CRUD, and status
    transition. Multiple slots can be combined; actions execute in
    canonical order (header → row adds → row updates → row deletes →
    status). Status runs last so a transition to DONE sees the final row
    set. To remove a transfer entirely, use ``delete_bin_transfer``.
    """

    id: int = Field(..., description="Bin transfer ID")
    update_header: BinTransferHeaderPatch | None = Field(
        default=None,
        description=(
            "Header-field patches: transfer number, location, notes, "
            "created/departed/arrived dates."
        ),
    )
    add_rows: list[BinTransferRowAdd] | None = Field(
        default=None,
        description=(
            "New line items. Each row: variant_id (int, required), quantity "
            "(float, required, >0), source/target bin IDs, traceability."
        ),
    )
    update_rows: list[BinTransferRowUpdate] | None = Field(
        default=None,
        description=(
            "Patches to existing line items. Each entry: id (int, required) "
            "+ any subset of variant_id, quantity, source/target bin IDs, "
            "traceability."
        ),
    )
    delete_row_ids: list[int] | None = Field(
        default=None,
        description="Row IDs to delete from the transfer.",
    )
    update_status: BinTransferStatusPatch | None = Field(
        default=None,
        description=(
            "Status transition (CREATED → IN_TRANSIT → DONE). Maps to the "
            "dedicated status endpoint; runs after header and row updates."
        ),
    )


class DeleteBinTransferRequest(ConfirmableRequest):
    """Delete a bin transfer. Destructive — removes the transfer record."""

    id: int = Field(..., description="Bin transfer ID to delete")


async def _fetch_bin_transfer_attrs(
    services: Any, transfer_id: int
) -> BinTransfer | None:
    """Best-effort GET /bin_transfers/{id} for diff context and cache merge."""
    return await safe_fetch_for_diff(
        api_get_bin_transfer,
        services,
        transfer_id,
        return_type=BinTransfer,
        label="bin transfer",
    )


async def _fetch_bin_transfer_row(services: Any, row_id: int) -> BinTransferRow | None:
    """Best-effort GET /bin_transfer_rows/{id} for row-update diff context."""
    return await safe_fetch_for_diff(
        api_get_bin_transfer_row,
        services,
        row_id,
        return_type=BinTransferRow,
        label="bin transfer row",
    )


def _build_update_header_request(
    patch: BinTransferHeaderPatch,
) -> APIUpdateBinTransferRequest:
    return APIUpdateBinTransferRequest(**unset_dict(patch))


def _build_update_status_request(
    patch: BinTransferStatusPatch,
) -> APIUpdateBinTransferStatusRequest:
    return APIUpdateBinTransferStatusRequest(status=BinTransferStatus(patch.new_status))


def _row_wire_transforms() -> dict[str, Any]:
    """``unset_dict`` transforms shared by the row add / update builders."""
    return {
        "quantity": _quantity_to_wire,
        "traceability": _wire_traceability_from_dumped,
    }


def _wire_traceability_from_dumped(
    items: list[dict[str, Any]],
) -> list[BinTransferTraceabilityRequest]:
    """Convert dumped traceability dicts to attrs request objects.

    ``unset_dict`` hands transforms the ``model_dump`` value — a list of
    plain dicts — rather than the typed inputs.
    """
    return [
        BinTransferTraceabilityRequest(
            batch_id=to_unset(item.get("batch_id")),
            serial_number_id=to_unset(item.get("serial_number_id")),
            quantity=(
                _quantity_to_wire(item["quantity"])
                if item.get("quantity") is not None
                else UNSET
            ),
        )
        for item in items
    ]


def _build_create_row_request(
    transfer_id: int, row: BinTransferRowAdd
) -> APICreateBinTransferRowRequest:
    return APICreateBinTransferRowRequest(
        bin_transfer_id=transfer_id,
        **unset_dict(row, transforms=_row_wire_transforms()),
    )


def _build_update_row_request(
    patch: BinTransferRowUpdate,
) -> APIUpdateBinTransferRowRequest:
    return APIUpdateBinTransferRowRequest(
        **unset_dict(patch, exclude=("id",), transforms=_row_wire_transforms())
    )


async def _plan_row_updates(
    services: Any, patches: list[BinTransferRowUpdate] | None
) -> list[ActionSpec]:
    """Build update-row ActionSpecs with wire-aware verification transforms.

    Hand-rolled instead of the generic ``plan_updates`` because the wire
    echoes ``quantity`` as a decimal string and ``traceability`` as attrs
    objects — both need canonicalizing transforms the generic helper
    doesn't thread through.
    """
    if not patches:
        return []

    existing_rows = await asyncio.gather(
        *[_fetch_bin_transfer_row(services, patch.id) for patch in patches]
    )

    specs: list[ActionSpec] = []
    for patch, existing in zip(patches, existing_rows, strict=True):
        diff = compute_field_diff(existing, patch, unknown_prior=existing is None)
        specs.append(
            ActionSpec(
                operation=BinTransferOperation.UPDATE_ROW,
                target_id=patch.id,
                diff=diff,
                apply=make_patch_apply(
                    api_update_bin_transfer_row,
                    services,
                    patch.id,
                    _build_update_row_request(patch),
                    return_type=BinTransferRow,
                ),
                verify=make_response_verifier(diff, transforms=_ROW_VERIFY_TRANSFORMS),
            )
        )
    return specs


def _collect_bin_row_variant_ids(
    existing: BinTransfer | None,
    request: ModifyBinTransferRequest,
) -> set[int]:
    """Gather every variant id the modify card's row table needs resolved.

    Union of the existing rows' variants (the snapshot the card renders) and
    the variants referenced by ``add_rows`` / ``update_rows`` so added /
    variant-swapped rows show a SKU + name, not a bare id. One set → one
    batched cache lookup in :func:`_resolve_bin_row_variants`.
    """
    ids: set[int] = set()
    if existing is not None:
        for row in unwrap_unset(existing.bin_transfer_rows, None) or []:
            ids.add(int(row.variant_id))
    for add in request.add_rows or []:
        ids.add(int(add.variant_id))
    for upd in request.update_rows or []:
        if upd.variant_id is not None:
            ids.add(int(upd.variant_id))
    return ids


async def _resolve_bin_row_variants(
    services: Any, variant_ids: set[int]
) -> dict[int, dict[str, str | None]]:
    """Batch-resolve ``{variant_id: {"sku", "display_name"}}`` via the typed
    cache for the modify card's row table. Misses degrade to ``None`` fields
    so the row still renders (``variant <id>`` fallback). Mirrors the PO
    card's ``_resolve_po_row_variants``.
    """
    if not variant_ids:
        return {}
    from katana_public_api_client.models_pydantic._generated import CachedVariant

    # Enrichment lookup by ID — include archived + deleted so a row that
    # references an archived/deleted variant still resolves its SKU + name.
    variants = await services.typed_cache.catalog.get_many_by_ids(
        CachedVariant, variant_ids, include_archived=True, include_deleted=True
    )
    resolved: dict[int, dict[str, str | None]] = {}
    for vid in variant_ids:
        v = variants.get(vid)
        if v is None:
            resolved[vid] = {"sku": None, "display_name": None}
        elif isinstance(v, dict):
            resolved[vid] = {
                "sku": v.get("sku"),
                "display_name": v.get("display_name"),
            }
        else:
            resolved[vid] = {
                "sku": getattr(v, "sku", None),
                "display_name": getattr(v, "display_name", None),
            }
    return resolved


async def _resolve_bins_for_card(
    services: Any, existing: BinTransfer | None
) -> dict[int, str]:
    """Best-effort ``{bin_id: bin_name}`` lookup for the modify card's row table.

    Storage bins aren't cached (live-only endpoint), so this issues one live
    GET scoped to the transfer's location — every bin a row can legally
    reference belongs to that location. Failures (or an unfetchable parent)
    degrade to an empty map and the card falls back to ``bin <id>`` cells.
    """
    if existing is None:
        return {}
    try:
        response = await api_get_all_storage_bins.asyncio_detailed(
            client=services.client,
            location_id=existing.location_id,
            include_deleted=True,
        )
        parsed = unwrap(response)
        bins = parsed if isinstance(parsed, list) else []
    except Exception as exc:
        logger.info(
            f"Could not fetch storage bins for card rendering: {exc} — "
            "row table will show bare bin ids."
        )
        return {}
    return {b.id: b.bin_name for b in bins}


async def _modify_bin_transfer_impl(
    request: ModifyBinTransferRequest, context: Context
) -> ModificationResponse:
    """Build the action plan from sub-payloads and either preview or execute."""
    services = get_services(context)

    if not has_any_subpayload(request):
        raise ValueError(
            "At least one sub-payload must be set: update_header, add_rows, "
            "update_rows, delete_row_ids, or update_status. To remove the "
            "bin transfer entirely, use delete_bin_transfer."
        )

    existing = await _fetch_bin_transfer_attrs(services, request.id)

    plan: list[ActionSpec] = []

    if request.update_header is not None:
        diff = compute_field_diff(
            existing, request.update_header, unknown_prior=existing is None
        )
        plan.append(
            ActionSpec(
                operation=BinTransferOperation.UPDATE_HEADER,
                target_id=request.id,
                diff=diff,
                apply=make_patch_apply(
                    api_update_bin_transfer,
                    services,
                    request.id,
                    _build_update_header_request(request.update_header),
                    return_type=BinTransfer,
                ),
                verify=make_response_verifier(diff),
            )
        )

    plan.extend(
        plan_creates(
            request.add_rows,
            BinTransferOperation.ADD_ROW,
            lambda row: _build_create_row_request(request.id, row),
            lambda body: make_post_apply(
                api_create_bin_transfer_row,
                services,
                body,
                return_type=BinTransferRow,
            ),
        )
    )
    plan.extend(await _plan_row_updates(services, request.update_rows))
    plan.extend(
        plan_deletes(
            request.delete_row_ids,
            BinTransferOperation.DELETE_ROW,
            lambda rid: make_delete_apply(api_delete_bin_transfer_row, services, rid),
        )
    )

    if request.update_status is not None:
        # Status runs last so a DONE transition sees the final row set.
        # The patch field is ``new_status`` while the response attr is
        # ``status``; the tool literal equals Katana's wire value
        # (CREATED / IN_TRANSIT / DONE), so no value transform is needed —
        # ``_normalize`` already collapses the echoed enum to its value.
        diff = compute_field_diff(
            existing,
            request.update_status,
            field_map={"new_status": "status"},
            unknown_prior=existing is None,
        )
        plan.append(
            ActionSpec(
                operation=BinTransferOperation.UPDATE_STATUS,
                target_id=request.id,
                diff=diff,
                apply=make_patch_apply(
                    api_update_bin_transfer_status,
                    services,
                    request.id,
                    _build_update_status_request(request.update_status),
                    return_type=BinTransfer,
                ),
                verify=make_response_verifier(diff, field_map={"new_status": "status"}),
            )
        )

    # Resolve variant SKU / name (typed cache) + bin names (one live GET,
    # storage bins aren't cached) for the card's row table — user-facing
    # identities, not bare ids. Skipped for header-/status-only plans: the
    # card short-circuits and never renders the row table.
    has_row_crud = bool(
        request.add_rows or request.update_rows or request.delete_row_ids
    )
    if has_row_crud:
        resolved_variants, resolved_bins = await asyncio.gather(
            _resolve_bin_row_variants(
                services, _collect_bin_row_variant_ids(existing, request)
            ),
            _resolve_bins_for_card(services, existing),
        )
    else:
        resolved_variants, resolved_bins = {}, {}

    response = await run_modify_plan(
        request=request,
        naming=EntityNaming(
            entity_type="bin_transfer",
            entity_label=f"bin transfer {request.id}",
            tool_name="modify_bin_transfer",
        ),
        # No Katana web view path is known for bin transfers — katana_url
        # stays None until one is verified.
        web_url_kind=None,
        existing=existing,
        plan=plan,
        extras={
            "resolved_variants": resolved_variants,
            "resolved_bins": resolved_bins,
        },
        cache_merge=CacheMerge(
            cache=services.typed_cache,
            # Deliberately NOT setting ``parent_from_outcome``: like the PO
            # modify (#905), the PATCH response may embed no rows, and
            # ``_BIN_TRANSFER_SPEC.reconcile_children=True`` would then
            # reconcile the cached rows to the empty set. The GET-by-id
            # refetch embeds the full row set.
            refetch_for_merge=lambda eid: _fetch_bin_transfer_attrs(services, eid),
        ),
    )

    # Apply-path: synthesize NOT-RUN entries for the unattempted plan tail.
    # ``execute_plan`` is fail-fast — without these the card's row-table
    # morph would silently hide every planned row action past a failure.
    # Mirrors the PO / SO / BOM fail-fast handling.
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
async def modify_bin_transfer(
    request: Annotated[ModifyBinTransferRequest, Unpack()], context: Context
) -> ToolResult:
    """Modify a bin transfer — unified surface across header fields, rows,
    and status transition.

    Sub-payloads (any subset, all optional):

    - ``update_header`` — patch body fields (bin_transfer_number,
      location_id, additional_info, created/departed/arrived dates)
    - ``add_rows`` / ``update_rows`` / ``delete_row_ids`` — line item CRUD
      (bin transfer rows are fully mutable, unlike stock-transfer rows)
    - ``update_status`` — transition through the 3-state machine
      (CREATED / IN_TRANSIT / DONE). Katana rejects invalid transitions
      with a 400; the action surfaces the API error in the response.

    Two-step flow: ``preview=true`` (default) returns a per-action preview
    with diffs; ``preview=false`` executes the plan in canonical order
    (header → row adds → row updates → row deletes → status — status last
    so a DONE transition sees the final row set). Fail-fast on error; the
    response carries a ``prior_state`` snapshot for manual revert.

    To remove a transfer entirely, use the sibling ``delete_bin_transfer``
    tool.
    """
    response = await _modify_bin_transfer_impl(request, context)
    return to_tool_result(
        response, confirm_request=request, confirm_tool="modify_bin_transfer"
    )


# ============================================================================
# Tool: delete_bin_transfer
# ============================================================================


async def _delete_bin_transfer_impl(
    request: DeleteBinTransferRequest, context: Context
) -> ModificationResponse:
    """One-action plan that removes the bin transfer. Katana cascades the
    rows server-side; ``prior_state`` carries the pre-delete snapshot."""
    return await run_delete_plan(
        request=request,
        services=get_services(context),
        entity_type="bin_transfer",
        entity_label=f"bin transfer {request.id}",
        web_url_kind=None,
        fetcher=_fetch_bin_transfer_attrs,
        delete_endpoint=api_delete_bin_transfer,
        operation=BinTransferOperation.DELETE,
    )


@observe_tool
@unpack_pydantic_params
async def delete_bin_transfer(
    request: Annotated[DeleteBinTransferRequest, Unpack()], context: Context
) -> ToolResult:
    """Delete a bin transfer. Destructive — the transfer record is removed.

    Two-step flow: ``preview=true`` (default) returns a preview with a
    ``prior_state`` snapshot of the transfer (including rows) so callers
    can verify the target before applying; ``preview=false`` deletes it.
    """
    response = await _delete_bin_transfer_impl(request, context)
    return to_tool_result(
        response, confirm_request=request, confirm_tool="delete_bin_transfer"
    )


# ============================================================================
# Tool: list_bin_inventory
# ============================================================================


class ListBinInventoryRequest(BaseModel):
    """Request to list per-bin inventory levels (live read)."""

    model_config = ConfigDict(extra="forbid")

    granularity: GranularityLiteral = Field(
        default="VARIANT",
        description=(
            "Row granularity: VARIANT (default) aggregates per variant+bin; "
            "BATCH and SERIAL_NUMBER break rows out per batch / serial."
        ),
    )
    location_id: int | None = Field(
        default=None,
        description="Filter by location ID. Look up via `list_locations`.",
    )
    variant_id: int | None = Field(
        default=None,
        description="Filter by variant ID. Look up via `search_items`.",
    )
    bin_location_id: str | None = Field(
        default=None,
        pattern=r"^(\d+|null)$",
        description=(
            "Filter by bin ID (see `list_storage_bins`), or the literal "
            "string 'null' to match stock not assigned to any bin."
        ),
    )
    batch_id: str | None = Field(
        default=None,
        pattern=r"^(\d+|null)$",
        description=(
            "Filter by batch ID, or 'null' for rows without batch "
            "attribution. Most useful with granularity=BATCH."
        ),
    )
    serial_number_id: str | None = Field(
        default=None,
        pattern=r"^(\d+|null)$",
        description=(
            "Filter by serial number ID, or 'null' for rows without serial "
            "attribution. Most useful with granularity=SERIAL_NUMBER."
        ),
    )
    limit: int = Field(
        default=50,
        ge=1,
        description="Max rows to return (default 50, min 1).",
    )
    page: int | None = Field(
        default=None,
        ge=1,
        description="Page number (1-based).",
    )


class BinInventoryEntry(BaseModel):
    """One per-bin inventory level row."""

    location_id: int | None = None
    variant_id: int | None = None
    bin_location_id: int | None = Field(
        default=None, description="Bin holding the stock; None means unassigned."
    )
    batch_id: int | None = None
    serial_number_id: int | None = None
    quantity_in_stock: float | None = None
    quantity_committed: float | None = None
    quantity_expected: float | None = None


class ListBinInventoryResponse(BaseModel):
    """Response containing per-bin inventory levels."""

    entries: list[BinInventoryEntry]
    total_count: int
    granularity: str


def _float_or_none(value: Any) -> float | None:
    """Coerce a wire decimal-string quantity (or UNSET) to float."""
    unwrapped = unwrap_unset(value, None)
    return float(unwrapped) if unwrapped is not None else None


async def _list_bin_inventory_impl(
    request: ListBinInventoryRequest, context: Context
) -> ListBinInventoryResponse:
    """List per-bin inventory levels straight from the live API."""
    services = get_services(context)

    response = await api_get_bin_inventory.asyncio_detailed(
        client=services.client,
        granularity=BinInventoryGranularity(request.granularity),
        location_id=to_unset(request.location_id),
        variant_id=to_unset(request.variant_id),
        bin_location_id=to_unset(request.bin_location_id),
        batch_id=to_unset(request.batch_id),
        serial_number_id=to_unset(request.serial_number_id),
        limit=request.limit,
        page=to_unset(request.page),
    )
    rows = unwrap_data(response, default=[])

    entries = [
        BinInventoryEntry(
            location_id=unwrap_unset(row.location_id, None),
            variant_id=unwrap_unset(row.variant_id, None),
            bin_location_id=unwrap_unset(row.bin_location_id, None),
            batch_id=unwrap_unset(row.batch_id, None),
            serial_number_id=unwrap_unset(row.serial_number_id, None),
            quantity_in_stock=_float_or_none(row.quantity_in_stock),
            quantity_committed=_float_or_none(row.quantity_committed),
            quantity_expected=_float_or_none(row.quantity_expected),
        )
        for row in rows
    ]

    return ListBinInventoryResponse(
        entries=entries,
        total_count=len(entries),
        granularity=request.granularity,
    )


@observe_tool
@unpack_pydantic_params
async def list_bin_inventory(
    request: Annotated[ListBinInventoryRequest, Unpack()], context: Context
) -> ToolResult:
    """List per-bin inventory levels — which bins hold which stock.

    Live read against `GET /bin_inventory` (not cached). Quantities come
    back per (variant, bin) at the requested `granularity`:

    - `VARIANT` (default) — one row per variant per bin
    - `BATCH` — broken out per batch (batch_id populated)
    - `SERIAL_NUMBER` — broken out per serial (serial_number_id populated)

    `bin_location_id=null` (the string) finds stock not assigned to any
    bin. For location-level totals use `check_inventory` instead.
    """
    response = await _list_bin_inventory_impl(request, context)
    return make_json_result(response)


# ============================================================================
# Tools: list_storage_bins / create_storage_bin
# ============================================================================


class ListStorageBinsRequest(BaseModel):
    """Request to list storage bins (live read)."""

    model_config = ConfigDict(extra="forbid")

    location_id: int | None = Field(
        default=None,
        description="Filter by location ID. Look up via `list_locations`.",
    )
    bin_name: str | None = Field(default=None, description="Filter by exact bin name.")
    include_deleted: bool = Field(
        default=False,
        description="When true, include soft-deleted bins.",
    )
    limit: int = Field(
        default=50,
        ge=1,
        description="Max rows to return (default 50, min 1).",
    )
    page: int | None = Field(
        default=None,
        ge=1,
        description="Page number (1-based).",
    )


class StorageBinInfo(BaseModel):
    """Summary of one storage bin."""

    id: int
    bin_name: str
    location_id: int
    created_at: str | None = None
    deleted_at: str | None = None


class ListStorageBinsResponse(BaseModel):
    """Response containing storage bins."""

    bins: list[StorageBinInfo]
    total_count: int


def _bin_to_info(bin_: StorageBinResponse) -> StorageBinInfo:
    created = unwrap_unset(bin_.created_at, None)
    deleted = unwrap_unset(bin_.deleted_at, None)
    return StorageBinInfo(
        id=bin_.id,
        bin_name=bin_.bin_name,
        location_id=bin_.location_id,
        created_at=iso_or_none(created)
        if isinstance(created, _datetime.datetime)
        else None,
        deleted_at=iso_or_none(deleted)
        if isinstance(deleted, _datetime.datetime)
        else None,
    )


async def _list_storage_bins_impl(
    request: ListStorageBinsRequest, context: Context
) -> ListStorageBinsResponse:
    """List storage bins straight from the live API.

    ``GET /bin_locations`` is one of the two documented bare-array
    endpoints (no ``{"data": [...]}`` envelope) — the generated parser
    returns ``list[StorageBinResponse]`` directly, so this unwraps the
    response body itself rather than a ``data`` field.
    """
    services = get_services(context)

    response = await api_get_all_storage_bins.asyncio_detailed(
        client=services.client,
        location_id=to_unset(request.location_id),
        bin_name=to_unset(request.bin_name),
        include_deleted=request.include_deleted,
        limit=request.limit,
        page=to_unset(request.page),
    )
    parsed = unwrap(response)
    # ``unwrap`` raises on error statuses, but its return type keeps the
    # ErrorResponse union member — narrow to the success shape.
    bins = parsed if isinstance(parsed, list) else []

    infos = [_bin_to_info(b) for b in bins]
    return ListStorageBinsResponse(bins=infos, total_count=len(infos))


@observe_tool
@unpack_pydantic_params
async def list_storage_bins(
    request: Annotated[ListStorageBinsRequest, Unpack()], context: Context
) -> ToolResult:
    """List storage bins (bin locations) — the named bins within each location.

    Use to look up bin IDs for `create_bin_transfer` /
    `modify_bin_transfer` rows and `list_bin_inventory` filters.
    Filter by `location_id` or exact `bin_name`.
    """
    response = await _list_storage_bins_impl(request, context)
    return make_json_result(response)


class CreateStorageBinRequest(BaseModel):
    """Request to create a storage bin."""

    model_config = ConfigDict(extra="forbid")

    bin_name: str = Field(..., description="Name of the new bin (e.g. 'A-01-02')")
    location_id: int = Field(
        ...,
        description="Location the bin belongs to. Look up via `list_locations`.",
    )
    preview: bool = Field(
        default=True,
        description="If true (default), returns preview. If false, creates the bin.",
    )


class CreateStorageBinResponse(BaseModel):
    """Response from a storage bin create operation."""

    id: int | None = None
    bin_name: str
    location_id: int
    location_name: str | None = None
    is_preview: bool
    warnings: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    message: str


async def _create_storage_bin_impl(
    request: CreateStorageBinRequest, context: Context
) -> CreateStorageBinResponse:
    """Implementation of create_storage_bin tool."""
    from katana_public_api_client.models_pydantic._generated import CachedLocation

    services = get_services(context)
    location_name, location_warn = await resolve_entity_name(
        services.typed_cache.catalog,
        CachedLocation,
        request.location_id,
        entity_label="Location",
    )
    warnings = [w for w in (location_warn,) if w]
    location_label = (
        f"{location_name} (id={request.location_id})"
        if location_name
        else f"location id={request.location_id}"
    )

    if request.preview:
        return CreateStorageBinResponse(
            bin_name=request.bin_name,
            location_id=request.location_id,
            location_name=location_name,
            is_preview=True,
            warnings=warnings,
            next_actions=[
                "Review the bin details",
                "Set preview=false to create the storage bin",
            ],
            message=(f"Preview: storage bin '{request.bin_name}' in {location_label}"),
        )

    response = await api_create_storage_bin.asyncio_detailed(
        client=services.client,
        body=StorageBinCreate(
            bin_name=request.bin_name, location_id=request.location_id
        ),
    )
    created = unwrap_as(response, StorageBinResponse)
    logger.info(f"Created storage bin ID {created.id} ('{created.bin_name}')")

    return CreateStorageBinResponse(
        id=created.id,
        bin_name=created.bin_name,
        location_id=created.location_id,
        location_name=location_name,
        is_preview=False,
        warnings=warnings,
        next_actions=[
            f"Storage bin created with ID {created.id}",
            "Move stock into it with create_bin_transfer",
        ],
        message=f"Successfully created storage bin (ID: {created.id})",
    )


@observe_tool
@unpack_pydantic_params
async def create_storage_bin(
    request: Annotated[CreateStorageBinRequest, Unpack()], context: Context
) -> ToolResult:
    """Create a storage bin (bin location) within a location.

    Two-step flow: preview=true (default) to preview, preview=false to
    create. Requires bin_name and location_id.
    """
    response = await _create_storage_bin_impl(request, context)
    return make_json_result(response)


# ============================================================================
# Registration
# ============================================================================


def register_tools(mcp: FastMCP) -> None:
    """Register all bin-transfer + bin-inventory tools with the FastMCP instance.

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
        readOnlyHint=False, destructiveHint=True, openWorldHint=True
    )

    register_preview_tool(
        mcp,
        create_bin_transfer,
        tags={"inventory", "bin_transfer", "write"},
        annotations=_create,
    )
    mcp.tool(tags={"inventory", "bin_transfer", "read"}, annotations=_read)(
        list_bin_transfers
    )
    register_preview_tool(
        mcp,
        modify_bin_transfer,
        tags={"inventory", "bin_transfer", "write"},
        annotations=_modify,
        meta=UI_META,
    )
    register_preview_tool(
        mcp,
        delete_bin_transfer,
        tags={"inventory", "bin_transfer", "write", "destructive"},
        annotations=_destructive,
        meta=UI_META,
    )
    mcp.tool(tags={"inventory", "bin_transfer", "read"}, annotations=_read)(
        list_bin_inventory
    )
    mcp.tool(tags={"inventory", "bin_transfer", "read"}, annotations=_read)(
        list_storage_bins
    )
    register_preview_tool(
        mcp,
        create_storage_bin,
        tags={"inventory", "bin_transfer", "write"},
        annotations=_create,
    )
