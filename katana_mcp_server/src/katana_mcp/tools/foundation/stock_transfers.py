"""Stock transfer management tools for Katana MCP Server.

Foundation tools covering the full stock-transfer lifecycle: create a transfer
between locations, list transfers with filters, update transfer body fields,
transition status through the four-state machine
(PENDING / IN_TRANSIT / COMPLETED / CANCELLED), and delete.

These tools provide:
- create_stock_transfer: Create a transfer with preview/confirm pattern
- list_stock_transfers: List transfers with paging, date, status filters
- update_stock_transfer: Update body fields with preview/confirm pattern
- update_stock_transfer_status: Transition state with preview/confirm pattern
- delete_stock_transfer: Delete transfer with preview/confirm pattern
"""

from __future__ import annotations

import datetime as _datetime
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, Field

from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.schemas import ConfirmationResult, require_confirmation
from katana_mcp.tools.tool_result_utils import (
    PaginationMeta,
    apply_date_window_filters,
    coerce_enum,
    enum_to_str,
    format_md_table,
    iso_or_none,
    make_simple_result,
    parse_request_dates,
)
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.domain.converters import to_unset, unwrap_unset
from katana_public_api_client.models import (
    CreateStockTransferRequest as APICreateStockTransferRequest,
    StockTransfer,
    StockTransferRowBatchTransactionsItem,
    StockTransferRowRequest,
    StockTransferStatus,
    UpdateStockTransferRequest as APIUpdateStockTransferRequest,
    UpdateStockTransferStatusRequest as APIUpdateStockTransferStatusRequest,
)
from katana_public_api_client.utils import APIError, is_success, unwrap, unwrap_as

logger = get_logger(__name__)


# Status literal shared across tools — mirrors the 4-state enum in
# StockTransferStatus while keeping the tool surface user-friendly (uppercase).
StatusLiteral = Literal["PENDING", "IN_TRANSIT", "COMPLETED", "CANCELLED"]


def _status_literal_to_enum(status: StatusLiteral) -> StockTransferStatus:
    """Map the tool-facing uppercase literal to the lowercase API enum."""
    return StockTransferStatus(status.lower())


# ============================================================================
# Shared response models
# ============================================================================


class StockTransferRowInfo(BaseModel):
    """Summary of a stock transfer line item."""

    id: int | None = None
    variant_id: int | None = None
    quantity: float | None = None
    cost_per_unit: float | None = None
    batch_transactions: list[dict[str, Any]] | None = None


class StockTransferSummary(BaseModel):
    """Summary row for a stock transfer in a list."""

    id: int
    stock_transfer_number: str | None
    source_location_id: int | None
    target_location_id: int | None
    status: str | None
    transfer_date: str | None
    expected_arrival_date: str | None
    created_at: str | None
    row_count: int
    rows: list[StockTransferRowInfo] | None = None


def _build_row_info(row: Any) -> StockTransferRowInfo:
    """Extract a StockTransferRowInfo from an attrs StockTransferRow."""
    raw_batches = unwrap_unset(row.batch_transactions, None)
    batches: list[dict[str, Any]] | None = None
    if raw_batches:
        batches = [
            {"batch_id": b.batch_id, "quantity": b.quantity} for b in raw_batches
        ]
    return StockTransferRowInfo(
        id=unwrap_unset(row.id, None),
        variant_id=unwrap_unset(row.variant_id, None),
        quantity=unwrap_unset(row.quantity, None),
        cost_per_unit=unwrap_unset(row.cost_per_unit, None),
        batch_transactions=batches,
    )


def _build_summary(transfer: Any, *, include_rows: bool) -> StockTransferSummary:
    """Convert an attrs StockTransfer into a StockTransferSummary."""
    raw_rows = unwrap_unset(transfer.stock_transfer_rows, []) or []
    row_infos = [_build_row_info(r) for r in raw_rows] if include_rows else None
    transfer_date = unwrap_unset(transfer.transfer_date, None)
    expected = unwrap_unset(transfer.expected_arrival_date, None)
    created = unwrap_unset(transfer.created_at, None)
    status = unwrap_unset(transfer.status, None)
    return StockTransferSummary(
        id=transfer.id,
        stock_transfer_number=unwrap_unset(transfer.stock_transfer_number, None),
        source_location_id=unwrap_unset(transfer.source_location_id, None),
        target_location_id=unwrap_unset(transfer.target_location_id, None),
        status=enum_to_str(status),
        transfer_date=iso_or_none(transfer_date)
        if isinstance(transfer_date, _datetime.datetime)
        else None,
        expected_arrival_date=iso_or_none(expected)
        if isinstance(expected, _datetime.datetime)
        else None,
        created_at=iso_or_none(created)
        if isinstance(created, _datetime.datetime)
        else None,
        row_count=len(raw_rows),
        rows=row_infos,
    )


# ============================================================================
# Tool 1: create_stock_transfer
# ============================================================================


class StockTransferBatchTransactionInput(BaseModel):
    """Batch transaction for a batch-tracked variant on a stock transfer row."""

    batch_id: int = Field(..., description="Batch ID being transferred")
    quantity: float = Field(..., description="Quantity drawn from this batch", gt=0)


class StockTransferRowInput(BaseModel):
    """Line item for a stock transfer."""

    variant_id: int = Field(..., description="Variant ID to transfer")
    quantity: float = Field(..., description="Quantity to transfer", gt=0)
    batch_transactions: list[StockTransferBatchTransactionInput] | None = Field(
        default=None,
        description=(
            "Batch transactions for batch-tracked items. Required for batch-tracked "
            "variants — each entry picks a batch_id and quantity."
        ),
    )


class CreateStockTransferRequest(BaseModel):
    """Request to create a stock transfer between two locations."""

    source_location_id: int = Field(..., description="Source location ID")
    destination_location_id: int = Field(
        ..., description="Destination location ID (target_location_id in API terms)"
    )
    expected_arrival_date: datetime = Field(
        ..., description="Expected arrival date at the destination location"
    )
    rows: list[StockTransferRowInput] = Field(
        ..., description="Line items to transfer", min_length=1
    )
    order_no: str | None = Field(
        default=None,
        description=(
            "Optional transfer number (stock_transfer_number). Katana auto-assigns "
            "one when omitted."
        ),
    )
    additional_info: str | None = Field(
        default=None, description="Additional notes (optional)"
    )
    confirm: bool = Field(
        default=False,
        description="If false, returns preview. If true, creates the transfer.",
    )


class StockTransferResponse(BaseModel):
    """Response from a stock transfer create/update/status-change operation."""

    id: int | None = None
    stock_transfer_number: str | None = None
    source_location_id: int | None = None
    target_location_id: int | None = None
    status: str | None = None
    expected_arrival_date: str | None = None
    is_preview: bool
    next_actions: list[str] = Field(default_factory=list)
    message: str


def _transfer_to_response(
    transfer: StockTransfer, *, message: str, is_preview: bool = False
) -> StockTransferResponse:
    """Build a StockTransferResponse from an attrs StockTransfer."""
    expected = unwrap_unset(transfer.expected_arrival_date, None)
    status = unwrap_unset(transfer.status, None)
    return StockTransferResponse(
        id=transfer.id,
        stock_transfer_number=unwrap_unset(transfer.stock_transfer_number, None),
        source_location_id=unwrap_unset(transfer.source_location_id, None),
        target_location_id=unwrap_unset(transfer.target_location_id, None),
        status=enum_to_str(status),
        expected_arrival_date=iso_or_none(expected)
        if isinstance(expected, _datetime.datetime)
        else None,
        is_preview=is_preview,
        message=message,
    )


def _build_row_requests(
    rows: list[StockTransferRowInput],
) -> list[StockTransferRowRequest]:
    """Convert pydantic row inputs to attrs request rows.

    The generated `StockTransferRowRequest` model exposes only `variant_id` and
    `quantity` as declared attrs fields, but Katana's API accepts
    `batch_transactions` on transfer rows (see `StockTransferRow` response).
    We stash batch transactions through the row's `additional_properties` bag
    so they flow into the serialized JSON body.
    """
    out: list[StockTransferRowRequest] = []
    for row in rows:
        api_row = StockTransferRowRequest(
            variant_id=row.variant_id,
            quantity=row.quantity,
        )
        if row.batch_transactions:
            batch_items = [
                StockTransferRowBatchTransactionsItem(
                    batch_id=bt.batch_id, quantity=bt.quantity
                )
                for bt in row.batch_transactions
            ]
            api_row.additional_properties = {
                "batch_transactions": [bi.to_dict() for bi in batch_items]
            }
        out.append(api_row)
    return out


async def _create_stock_transfer_impl(
    request: CreateStockTransferRequest, context: Context
) -> StockTransferResponse:
    """Implementation of create_stock_transfer tool."""
    logger.info(
        f"{'Previewing' if not request.confirm else 'Creating'} stock transfer "
        f"{request.order_no or '(auto)'} "
        f"({request.source_location_id} -> {request.destination_location_id})"
    )

    row_count = len(request.rows)
    preview_message = (
        f"Preview: Stock transfer with {row_count} row(s) from location "
        f"{request.source_location_id} to {request.destination_location_id}"
    )

    if not request.confirm:
        return StockTransferResponse(
            stock_transfer_number=request.order_no,
            source_location_id=request.source_location_id,
            target_location_id=request.destination_location_id,
            status="PENDING",
            expected_arrival_date=request.expected_arrival_date.isoformat(),
            is_preview=True,
            next_actions=[
                "Review the transfer details",
                "Set confirm=true to create the stock transfer",
            ],
            message=preview_message,
        )

    confirmation = await require_confirmation(
        context,
        f"Create stock transfer with {row_count} row(s) from location "
        f"{request.source_location_id} to {request.destination_location_id}?",
    )
    if confirmation != ConfirmationResult.CONFIRMED:
        logger.info("User did not confirm stock transfer creation")
        return StockTransferResponse(
            stock_transfer_number=request.order_no,
            source_location_id=request.source_location_id,
            target_location_id=request.destination_location_id,
            status="PENDING",
            expected_arrival_date=request.expected_arrival_date.isoformat(),
            is_preview=True,
            message=f"Stock transfer creation {confirmation} by user",
            next_actions=[
                "Review the transfer details and try again with confirm=true"
            ],
        )

    services = get_services(context)
    api_rows = _build_row_requests(request.rows)

    api_request = APICreateStockTransferRequest(
        source_location_id=request.source_location_id,
        target_location_id=request.destination_location_id,
        expected_arrival_date=request.expected_arrival_date,
        order_created_date=datetime.now(UTC),
        stock_transfer_number=to_unset(request.order_no),
        additional_info=to_unset(request.additional_info),
        stock_transfer_rows=api_rows,
    )

    from katana_public_api_client.api.stock_transfer import create_stock_transfer

    response = await create_stock_transfer.asyncio_detailed(
        client=services.client, body=api_request
    )
    transfer = unwrap_as(response, StockTransfer)
    logger.info(f"Created stock transfer ID {transfer.id}")

    result = _transfer_to_response(
        transfer,
        message=f"Successfully created stock transfer (ID: {transfer.id})",
    )
    result.next_actions = [
        f"Stock transfer created with ID {transfer.id}",
        "Use update_stock_transfer_status to transition it through IN_TRANSIT → COMPLETED",
    ]
    return result


@observe_tool
@unpack_pydantic_params
async def create_stock_transfer(
    request: Annotated[CreateStockTransferRequest, Unpack()], context: Context
) -> ToolResult:
    """Create a stock transfer moving inventory between two locations.

    Two-step flow: confirm=false to preview, confirm=true to create (prompts for
    confirmation). Requires source_location_id, destination_location_id,
    expected_arrival_date, and at least one row with variant_id + quantity.
    For batch-tracked variants, supply `batch_transactions` on the row.
    """
    response = await _create_stock_transfer_impl(request, context)

    lines = [
        f"## Stock Transfer ({'PREVIEW' if response.is_preview else 'CREATED'})",
        f"- **Message**: {response.message}",
    ]
    if response.id is not None:
        lines.append(f"- **ID**: {response.id}")
    if response.stock_transfer_number:
        lines.append(f"- **Number**: {response.stock_transfer_number}")
    if response.source_location_id is not None:
        lines.append(f"- **Source Location**: {response.source_location_id}")
    if response.target_location_id is not None:
        lines.append(f"- **Destination Location**: {response.target_location_id}")
    if response.expected_arrival_date:
        lines.append(f"- **Expected Arrival**: {response.expected_arrival_date}")
    if response.status:
        lines.append(f"- **Status**: {response.status}")
    if response.next_actions:
        lines.append("")
        lines.append("### Next Actions")
        lines.extend(f"- {action}" for action in response.next_actions)

    return make_simple_result("\n".join(lines), structured_data=response.model_dump())


# ============================================================================
# Tool 2: list_stock_transfers
# ============================================================================


class ListStockTransfersRequest(BaseModel):
    """Request to list/filter stock transfers (list-tool pattern v2)."""

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
    status: StatusLiteral | None = Field(
        default=None,
        description="Filter by transfer status (PENDING, IN_TRANSIT, COMPLETED, CANCELLED)",
    )
    source_location_id: int | None = Field(
        default=None, description="Filter by source location ID"
    )
    destination_location_id: int | None = Field(
        default=None,
        description="Filter by destination location ID (target_location_id).",
    )
    stock_transfer_number: str | None = Field(
        default=None, description="Filter by exact stock transfer number"
    )

    # Time-window filters
    created_after: str | None = Field(
        default=None, description="ISO-8601 datetime lower bound on created_at."
    )
    created_before: str | None = Field(
        default=None, description="ISO-8601 datetime upper bound on created_at."
    )

    # Row inclusion
    include_rows: bool = Field(
        default=False,
        description="When true, populate row-level detail on each summary.",
    )

    # Output formatting
    format: Literal["markdown", "json"] = Field(
        default="markdown",
        description=(
            "Output format: 'markdown' (default) for human-readable tables; "
            "'json' for structured data consumable by downstream tools/aggregations."
        ),
    )


class ListStockTransfersResponse(BaseModel):
    """Response containing a list of stock transfers."""

    transfers: list[StockTransferSummary]
    total_count: int
    pagination: PaginationMeta | None = None


_STOCK_TRANSFER_DATE_FIELDS = (
    "created_after",
    "created_before",
)


def _apply_stock_transfer_filters(
    stmt: Any,
    request: ListStockTransfersRequest,
    parsed_dates: dict[str, datetime | None],
) -> Any:
    """Translate request filters into WHERE clauses on a CachedStockTransfer query.

    Shared by the data SELECT and the COUNT SELECT so pagination totals
    reflect exactly the same filter set as the data rows. The ``status``
    request field is the uppercase ``StatusLiteral`` (PENDING, etc.); the
    cache column stores the lowercase value Katana returns. ``coerce_enum``
    validates the input against ``StockTransferStatus`` (raising loudly on
    a typo rather than silently returning zero rows) before the comparison.
    """
    from katana_public_api_client.models_pydantic._generated import (
        CachedStockTransfer,
        StockTransferStatus,
    )

    if request.status is not None:
        status_enum = coerce_enum(request.status.lower(), StockTransferStatus, "status")
        stmt = stmt.where(CachedStockTransfer.status == status_enum.value)
    if request.source_location_id is not None:
        stmt = stmt.where(
            CachedStockTransfer.source_location_id == request.source_location_id
        )
    if request.destination_location_id is not None:
        stmt = stmt.where(
            CachedStockTransfer.target_location_id == request.destination_location_id
        )
    if request.stock_transfer_number is not None:
        stmt = stmt.where(
            CachedStockTransfer.stock_transfer_number == request.stock_transfer_number
        )
    stmt = stmt.where(CachedStockTransfer.deleted_at.is_(None))

    return apply_date_window_filters(
        stmt,
        parsed_dates,
        ge_pairs={"created_after": CachedStockTransfer.created_at},
        le_pairs={"created_before": CachedStockTransfer.created_at},
    )


async def _list_stock_transfers_impl(
    request: ListStockTransfersRequest, context: Context
) -> ListStockTransfersResponse:
    """List stock transfers with filters via the typed cache.

    ``ensure_stock_transfers_synced`` runs an incremental
    ``updated_at_min`` delta (debounced — see :data:`_SYNC_DEBOUNCE`).
    Filters (including ``status``, which Katana doesn't expose as a
    server-side filter) translate to indexed SQL. See ADR-0018.
    """
    from sqlalchemy.orm import selectinload
    from sqlmodel import func, select

    from katana_mcp.typed_cache import ensure_stock_transfers_synced
    from katana_public_api_client.models_pydantic._generated import (
        CachedStockTransfer,
        CachedStockTransferRow,
    )

    services = get_services(context)

    await ensure_stock_transfers_synced(services.client, services.typed_cache)

    parsed_dates = parse_request_dates(request, _STOCK_TRANSFER_DATE_FIELDS)

    # When ``include_rows`` is set, ``selectinload`` eager-loads the
    # children, so ``len(transfer.stock_transfer_rows)`` is free at
    # materialization time and we skip the correlated COUNT subquery.
    if request.include_rows:
        stmt = select(CachedStockTransfer).options(
            selectinload(CachedStockTransfer.stock_transfer_rows)
        )
    else:
        row_count_subq = (
            select(func.count(CachedStockTransferRow.id))
            .where(CachedStockTransferRow.stock_transfer_id == CachedStockTransfer.id)
            .correlate(CachedStockTransfer)
            .scalar_subquery()
            .label("row_count")
        )
        stmt = select(CachedStockTransfer, row_count_subq)
    stmt = _apply_stock_transfer_filters(stmt, request, parsed_dates)
    stmt = stmt.order_by(
        CachedStockTransfer.created_at.desc(), CachedStockTransfer.id.desc()
    )
    if request.page is not None:
        stmt = stmt.offset((request.page - 1) * request.limit).limit(request.limit)
    else:
        stmt = stmt.limit(request.limit)

    async with services.typed_cache.session() as session:
        data_result = await session.exec(stmt)
        if request.include_rows:
            cached_transfers = list(data_result.all())
            transfers_with_counts: list[tuple[CachedStockTransfer, int]] = [
                (t, len(t.stock_transfer_rows)) for t in cached_transfers
            ]
        else:
            transfers_with_counts = data_result.all()

        pagination: PaginationMeta | None = None
        if request.page is not None:
            count_stmt = _apply_stock_transfer_filters(
                select(func.count()).select_from(CachedStockTransfer),
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

    # Cached rows expose fields directly (no UNSET sentinels), so we
    # don't reuse ``_build_summary`` — that helper expects the attrs API
    # shape with ``unwrap_unset``.
    summaries: list[StockTransferSummary] = []
    for transfer, row_count in transfers_with_counts:
        row_infos: list[StockTransferRowInfo] | None = None
        if request.include_rows:
            row_infos = [
                StockTransferRowInfo(
                    id=r.id,
                    variant_id=r.variant_id,
                    quantity=r.quantity,
                    cost_per_unit=r.cost_per_unit,
                    batch_transactions=None,
                )
                for r in transfer.stock_transfer_rows
            ]
        summaries.append(
            StockTransferSummary(
                id=transfer.id,
                stock_transfer_number=transfer.stock_transfer_number,
                source_location_id=transfer.source_location_id,
                target_location_id=transfer.target_location_id,
                status=transfer.status,
                transfer_date=iso_or_none(transfer.transfer_date),
                expected_arrival_date=iso_or_none(transfer.expected_arrival_date),
                created_at=iso_or_none(transfer.created_at),
                row_count=row_count,
                rows=row_infos,
            )
        )

    return ListStockTransfersResponse(
        transfers=summaries,
        total_count=len(summaries),
        pagination=pagination,
    )


@observe_tool
@unpack_pydantic_params
async def list_stock_transfers(
    request: Annotated[ListStockTransfersRequest, Unpack()], context: Context
) -> ToolResult:
    """List stock transfers with filters — returns multiple transfers for discovery or bulk review.

    Use for discovery workflows — find transfers by status, between specific
    locations, or within a date range. All filters (including `status`,
    which was a client-side post-fetch filter pre-cache) run as indexed
    SQL against the SQLModel typed cache.

    **Available filters:** `status`, `source_location_id`,
    `destination_location_id`, `stock_transfer_number`,
    `created_after`/`created_before`.

    **Paging:**
    - `limit` caps the number of rows (default 50, min 1).
    - `page=N` returns a single page; the response includes `pagination`
      metadata (total_records, total_pages, first/last flags) computed
      via SQL COUNT against the same filter predicate.

    Pass `include_rows=True` to populate per-transfer line items.
    """
    response = await _list_stock_transfers_impl(request, context)

    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2),
            structured_content=response.model_dump(),
        )

    if not response.transfers:
        md = "No stock transfers match the given filters."
    else:
        table = format_md_table(
            headers=[
                "ID",
                "Number",
                "Status",
                "Source",
                "Destination",
                "Rows",
                "Expected Arrival",
            ],
            rows=[
                [
                    t.id,
                    t.stock_transfer_number or "—",
                    t.status or "—",
                    t.source_location_id if t.source_location_id is not None else "—",
                    t.target_location_id if t.target_location_id is not None else "—",
                    t.row_count,
                    t.expected_arrival_date or "—",
                ]
                for t in response.transfers
            ],
        )
        md = f"## Stock Transfers ({response.total_count})\n\n{table}"

    return make_simple_result(md, structured_data=response.model_dump())


# ============================================================================
# Tool 3: update_stock_transfer
# ============================================================================


class UpdateStockTransferRequest(BaseModel):
    """Request to update body fields on a stock transfer."""

    id: int = Field(..., description="Stock transfer ID")
    stock_transfer_number: str | None = Field(
        default=None, description="New stock transfer number"
    )
    transfer_date: datetime | None = Field(
        default=None, description="New transfer date"
    )
    expected_arrival_date: datetime | None = Field(
        default=None, description="New expected arrival date"
    )
    additional_info: str | None = Field(
        default=None, description="New additional info/notes"
    )
    confirm: bool = Field(
        default=False,
        description="If false, returns preview. If true, applies the update.",
    )


async def _update_stock_transfer_impl(
    request: UpdateStockTransferRequest, context: Context
) -> StockTransferResponse:
    """Implementation of update_stock_transfer tool."""
    updates = {
        "stock_transfer_number": request.stock_transfer_number,
        "transfer_date": (
            request.transfer_date.isoformat() if request.transfer_date else None
        ),
        "expected_arrival_date": (
            request.expected_arrival_date.isoformat()
            if request.expected_arrival_date
            else None
        ),
        "additional_info": request.additional_info,
    }
    set_fields = {k: v for k, v in updates.items() if v is not None}

    if not set_fields:
        raise ValueError(
            "At least one field must be provided to update (stock_transfer_number, "
            "transfer_date, expected_arrival_date, additional_info)"
        )

    preview_message = (
        f"Preview: Update stock transfer {request.id} — fields: "
        + ", ".join(f"{k}={v}" for k, v in set_fields.items())
    )

    if not request.confirm:
        return StockTransferResponse(
            id=request.id,
            is_preview=True,
            next_actions=[
                "Review the update details",
                "Set confirm=true to apply the update",
            ],
            message=preview_message,
        )

    confirmation = await require_confirmation(
        context,
        f"Update stock transfer {request.id}? Fields: " + ", ".join(set_fields.keys()),
    )
    if confirmation != ConfirmationResult.CONFIRMED:
        logger.info(f"User did not confirm update of stock transfer {request.id}")
        return StockTransferResponse(
            id=request.id,
            is_preview=True,
            message=f"Stock transfer update {confirmation} by user",
            next_actions=["Review the update and try again with confirm=true"],
        )

    services = get_services(context)
    api_request = APIUpdateStockTransferRequest(
        stock_transfer_number=to_unset(request.stock_transfer_number),
        transfer_date=to_unset(request.transfer_date),
        expected_arrival_date=to_unset(request.expected_arrival_date),
        additional_info=to_unset(request.additional_info),
    )

    from katana_public_api_client.api.stock_transfer import update_stock_transfer

    response = await update_stock_transfer.asyncio_detailed(
        id=request.id, client=services.client, body=api_request
    )
    transfer = unwrap_as(response, StockTransfer)
    logger.info(f"Updated stock transfer ID {transfer.id}")

    result = _transfer_to_response(
        transfer,
        message=f"Successfully updated stock transfer {transfer.id}",
    )
    result.next_actions = [f"Stock transfer {transfer.id} updated"]
    return result


@observe_tool
@unpack_pydantic_params
async def update_stock_transfer(
    request: Annotated[UpdateStockTransferRequest, Unpack()], context: Context
) -> ToolResult:
    """Update body fields on an existing stock transfer.

    Two-step flow: confirm=false to preview, confirm=true to apply. Accepts
    `stock_transfer_number`, `transfer_date`, `expected_arrival_date`, and
    `additional_info`. Use `update_stock_transfer_status` to change status.
    """
    response = await _update_stock_transfer_impl(request, context)

    lines = [
        f"## Update Stock Transfer ({'PREVIEW' if response.is_preview else 'UPDATED'})",
        f"- **ID**: {response.id}",
        f"- **Message**: {response.message}",
    ]
    if response.stock_transfer_number:
        lines.append(f"- **Number**: {response.stock_transfer_number}")
    if response.status:
        lines.append(f"- **Status**: {response.status}")
    if response.expected_arrival_date:
        lines.append(f"- **Expected Arrival**: {response.expected_arrival_date}")
    if response.next_actions:
        lines.append("")
        lines.append("### Next Actions")
        lines.extend(f"- {action}" for action in response.next_actions)

    return make_simple_result("\n".join(lines), structured_data=response.model_dump())


# ============================================================================
# Tool 4: update_stock_transfer_status
# ============================================================================


class UpdateStockTransferStatusRequest(BaseModel):
    """Request to transition a stock transfer through the 4-state machine."""

    id: int = Field(..., description="Stock transfer ID")
    new_status: StatusLiteral = Field(
        ...,
        description=(
            "Target status. Valid transitions are governed by Katana — typical flow "
            "is PENDING → IN_TRANSIT → COMPLETED. CANCELLED reverses."
        ),
    )
    confirm: bool = Field(
        default=False,
        description="If false, returns preview. If true, applies the transition.",
    )


async def _update_stock_transfer_status_impl(
    request: UpdateStockTransferStatusRequest, context: Context
) -> StockTransferResponse:
    """Implementation of update_stock_transfer_status tool."""
    preview_message = (
        f"Preview: Transition stock transfer {request.id} to status "
        f"{request.new_status}"
    )

    if not request.confirm:
        return StockTransferResponse(
            id=request.id,
            status=request.new_status,
            is_preview=True,
            next_actions=[
                "Review the transition",
                "Set confirm=true to apply the status change",
            ],
            message=preview_message,
        )

    confirmation = await require_confirmation(
        context,
        f"Transition stock transfer {request.id} to {request.new_status}?",
    )
    if confirmation != ConfirmationResult.CONFIRMED:
        logger.info(
            f"User did not confirm status change of stock transfer {request.id}"
        )
        return StockTransferResponse(
            id=request.id,
            status=request.new_status,
            is_preview=True,
            message=f"Stock transfer status change {confirmation} by user",
            next_actions=["Review the transition and try again with confirm=true"],
        )

    services = get_services(context)
    api_request = APIUpdateStockTransferStatusRequest(
        status=_status_literal_to_enum(request.new_status),
    )

    from katana_public_api_client.api.stock_transfer import update_stock_transfer_status

    try:
        response = await update_stock_transfer_status.asyncio_detailed(
            id=request.id, client=services.client, body=api_request
        )
        transfer = unwrap_as(response, StockTransfer)
    except APIError as e:
        # Katana rejects invalid state transitions (e.g. COMPLETED → IN_TRANSIT)
        # with a typed error. Re-raise as ValueError so the tool surfaces a
        # clean, caller-actionable message.
        logger.warning(
            f"Invalid stock transfer status transition for ID {request.id}: {e}"
        )
        raise ValueError(
            f"Failed to transition stock transfer {request.id} to "
            f"{request.new_status}: {e}"
        ) from e

    logger.info(
        f"Transitioned stock transfer {transfer.id} to status "
        f"{enum_to_str(unwrap_unset(transfer.status, None))}"
    )

    result = _transfer_to_response(
        transfer,
        message=(
            f"Successfully transitioned stock transfer {transfer.id} to "
            f"{request.new_status}"
        ),
    )
    result.next_actions = [
        f"Stock transfer {transfer.id} now in status {request.new_status}"
    ]
    return result


@observe_tool
@unpack_pydantic_params
async def update_stock_transfer_status(
    request: Annotated[UpdateStockTransferStatusRequest, Unpack()], context: Context
) -> ToolResult:
    """Transition a stock transfer through the 4-state machine.

    Two-step flow: confirm=false to preview, confirm=true to apply. The four
    valid states are PENDING, IN_TRANSIT, COMPLETED, CANCELLED. Katana rejects
    invalid transitions (e.g. COMPLETED → IN_TRANSIT); the tool surfaces the
    API error message as a ValueError.
    """
    response = await _update_stock_transfer_status_impl(request, context)

    lines = [
        f"## Stock Transfer Status ({'PREVIEW' if response.is_preview else 'UPDATED'})",
        f"- **ID**: {response.id}",
        f"- **Status**: {response.status}",
        f"- **Message**: {response.message}",
    ]
    if response.next_actions:
        lines.append("")
        lines.append("### Next Actions")
        lines.extend(f"- {action}" for action in response.next_actions)

    return make_simple_result("\n".join(lines), structured_data=response.model_dump())


# ============================================================================
# Tool 5: delete_stock_transfer
# ============================================================================


class DeleteStockTransferRequest(BaseModel):
    """Request to delete a stock transfer."""

    id: int = Field(..., description="Stock transfer ID to delete")
    confirm: bool = Field(
        default=False,
        description="If false, returns preview. If true, deletes the transfer.",
    )


class DeleteStockTransferResponse(BaseModel):
    """Response from a stock transfer delete operation."""

    id: int
    is_preview: bool
    next_actions: list[str] = Field(default_factory=list)
    message: str


async def _delete_stock_transfer_impl(
    request: DeleteStockTransferRequest, context: Context
) -> DeleteStockTransferResponse:
    """Implementation of delete_stock_transfer tool."""
    preview_message = f"Preview: Delete stock transfer {request.id}"

    if not request.confirm:
        return DeleteStockTransferResponse(
            id=request.id,
            is_preview=True,
            next_actions=[
                "Review the deletion",
                "Set confirm=true to delete the stock transfer",
            ],
            message=preview_message,
        )

    confirmation = await require_confirmation(
        context, f"Delete stock transfer {request.id}? This action is destructive."
    )
    if confirmation != ConfirmationResult.CONFIRMED:
        logger.info(f"User did not confirm deletion of stock transfer {request.id}")
        return DeleteStockTransferResponse(
            id=request.id,
            is_preview=True,
            message=f"Stock transfer deletion {confirmation} by user",
            next_actions=["Review the deletion and try again with confirm=true"],
        )

    services = get_services(context)
    from katana_public_api_client.api.stock_transfer import delete_stock_transfer

    response = await delete_stock_transfer.asyncio_detailed(
        id=request.id, client=services.client
    )
    if not is_success(response):
        unwrap(response)

    logger.info(f"Deleted stock transfer ID {request.id}")
    return DeleteStockTransferResponse(
        id=request.id,
        is_preview=False,
        message=f"Successfully deleted stock transfer {request.id}",
        next_actions=[f"Stock transfer {request.id} has been deleted"],
    )


@observe_tool
@unpack_pydantic_params
async def delete_stock_transfer(
    request: Annotated[DeleteStockTransferRequest, Unpack()], context: Context
) -> ToolResult:
    """Delete a stock transfer.

    Two-step flow: confirm=false to preview, confirm=true to delete (prompts
    for confirmation). Destructive — the transfer record is removed.
    """
    response = await _delete_stock_transfer_impl(request, context)

    lines = [
        f"## Delete Stock Transfer ({'PREVIEW' if response.is_preview else 'DELETED'})",
        f"- **ID**: {response.id}",
        f"- **Message**: {response.message}",
    ]
    if response.next_actions:
        lines.append("")
        lines.append("### Next Actions")
        lines.extend(f"- {action}" for action in response.next_actions)

    return make_simple_result("\n".join(lines), structured_data=response.model_dump())


# ============================================================================
# Registration
# ============================================================================


def register_tools(mcp: FastMCP) -> None:
    """Register all stock-transfer tools with the FastMCP instance.

    Args:
        mcp: FastMCP server instance to register tools with
    """
    from mcp.types import ToolAnnotations

    _read = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )
    _write = ToolAnnotations(
        readOnlyHint=False, destructiveHint=False, openWorldHint=True
    )
    _destructive = ToolAnnotations(
        readOnlyHint=False, destructiveHint=True, openWorldHint=True
    )

    mcp.tool(tags={"inventory", "stock_transfer", "write"}, annotations=_write)(
        create_stock_transfer
    )
    mcp.tool(tags={"inventory", "stock_transfer", "read"}, annotations=_read)(
        list_stock_transfers
    )
    mcp.tool(tags={"inventory", "stock_transfer", "write"}, annotations=_write)(
        update_stock_transfer
    )
    mcp.tool(tags={"inventory", "stock_transfer", "write"}, annotations=_write)(
        update_stock_transfer_status
    )
    mcp.tool(tags={"inventory", "stock_transfer", "write"}, annotations=_destructive)(
        delete_stock_transfer
    )
