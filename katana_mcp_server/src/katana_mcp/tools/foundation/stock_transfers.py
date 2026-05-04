"""Stock transfer management tools for Katana MCP Server.

Foundation tools covering the full stock-transfer lifecycle:

- create_stock_transfer: Create a transfer with preview/apply pattern
- list_stock_transfers: List transfers with paging, date, status filters
- modify_stock_transfer: Unified modification — header (body fields) and/or
  status transition in a single call. Hides the fact that Katana exposes
  these as two separate PATCH endpoints.
- delete_stock_transfer: Destructive sibling of modify_stock_transfer.
"""

from __future__ import annotations

import asyncio
import datetime as _datetime
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Any, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, Field

from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools._modification import (
    ConfirmableRequest,
    ModificationResponse,
    compute_field_diff,
    make_response_verifier,
    to_tool_result,
)
from katana_mcp.tools._modification_dispatch import (
    ActionSpec,
    has_any_subpayload,
    make_patch_apply,
    run_delete_plan,
    run_modify_plan,
    unset_dict,
)
from katana_mcp.tools.tool_result_utils import (
    BLOCK_WARNING_PREFIX,
    PaginationMeta,
    apply_date_window_filters,
    enum_to_str,
    format_md_table,
    iso_or_none,
    make_simple_result,
    parse_request_dates,
    resolve_entity_name,
)
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_mcp.web_urls import katana_web_url
from katana_public_api_client.api.stock_transfer import (
    delete_stock_transfer as api_delete_stock_transfer,
    update_stock_transfer as api_update_stock_transfer,
    update_stock_transfer_status as api_update_stock_transfer_status,
)
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
from katana_public_api_client.utils import unwrap_as

logger = get_logger(__name__)


# Status literal shared across tools — mirrors the 3-state enum in
# StockTransferStatus while keeping the tool surface user-friendly (uppercase).
# The Katana API accepts {draft, received, inTransit} (camelCase ``inTransit``);
# verified 2026-04-28 against the live PATCH /stock_transfers/{id}/status
# endpoint. The previous {pending, in_transit, completed, cancelled} values
# were shipped in error and would 422 on every call against the live API.
StatusLiteral = Literal["DRAFT", "RECEIVED", "IN_TRANSIT"]


# Tool-facing uppercase literal → API enum value (the live Katana API uses
# lowercase + camelCase mix: ``draft``, ``received``, ``inTransit``).
_STATUS_API_VALUE: dict[StatusLiteral, StockTransferStatus] = {
    "DRAFT": StockTransferStatus.DRAFT,
    "RECEIVED": StockTransferStatus.RECEIVED,
    "IN_TRANSIT": StockTransferStatus.INTRANSIT,
}


def _status_literal_to_enum(status: StatusLiteral) -> StockTransferStatus:
    """Map the tool-facing uppercase literal to the API enum value."""
    return _STATUS_API_VALUE[status]


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
    katana_url: str | None = None


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
            "Optional transfer number (stock_transfer_number). When omitted, "
            "the MCP tool generates a timestamp-based default (``ST-<unix-ts>``) "
            "before the request is sent — Katana's API requires the field."
        ),
    )
    additional_info: str | None = Field(
        default=None, description="Additional notes (optional)"
    )
    preview: bool = Field(
        default=True,
        description="If true (default), returns preview. If false, creates the transfer.",
    )


class StockTransferResponse(BaseModel):
    """Response from a stock transfer create/update/status-change operation."""

    id: int | None = None
    stock_transfer_number: str | None = None
    source_location_id: int | None = None
    source_location_name: str | None = None
    target_location_id: int | None = None
    target_location_name: str | None = None
    status: str | None = None
    expected_arrival_date: str | None = None
    item_count: int | None = None
    is_preview: bool
    warnings: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    message: str
    katana_url: str | None = None


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
        katana_url=katana_web_url("stock_transfer", transfer.id),
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
        f"{'Previewing' if request.preview else 'Creating'} stock transfer "
        f"{request.order_no or '(auto)'} "
        f"({request.source_location_id} -> {request.destination_location_id})"
    )

    item_count = len(request.rows)

    # Resolve source/destination names + compute warnings up-front; both
    # the preview and apply paths use them. Source==destination is a
    # hard BLOCK enforced on the apply path too — defense in depth for
    # callers that skip the preview UI.
    from katana_mcp.cache import EntityType

    services = get_services(context)
    (src_name, src_warn), (dst_name, dst_warn) = await asyncio.gather(
        resolve_entity_name(
            services.cache,
            EntityType.LOCATION,
            request.source_location_id,
            entity_label="Source location",
        ),
        resolve_entity_name(
            services.cache,
            EntityType.LOCATION,
            request.destination_location_id,
            entity_label="Destination location",
        ),
    )
    warnings: list[str] = [w for w in (src_warn, dst_warn) if w]
    same_location_block: str | None = None
    if request.source_location_id == request.destination_location_id:
        same_location_block = (
            f"{BLOCK_WARNING_PREFIX} Source and destination are the same "
            f"location (id={request.source_location_id}); transfer would be a no-op."
        )
        warnings.append(same_location_block)

    src_label = (
        f"{src_name} (id={request.source_location_id})"
        if src_name
        else f"location id={request.source_location_id}"
    )
    dst_label = (
        f"{dst_name} (id={request.destination_location_id})"
        if dst_name
        else f"location id={request.destination_location_id}"
    )

    if request.preview:
        preview_message = (
            f"Preview: Stock transfer with {item_count} row(s) from "
            f"{src_label} to {dst_label}"
        )

        return StockTransferResponse(
            stock_transfer_number=request.order_no,
            source_location_id=request.source_location_id,
            source_location_name=src_name,
            target_location_id=request.destination_location_id,
            target_location_name=dst_name,
            status="DRAFT",
            expected_arrival_date=request.expected_arrival_date.isoformat(),
            item_count=item_count,
            is_preview=True,
            warnings=warnings,
            next_actions=[
                "Review the transfer details",
                "Set preview=false to create the stock transfer",
            ],
            message=preview_message,
        )

    if same_location_block is not None:
        return StockTransferResponse(
            stock_transfer_number=request.order_no,
            source_location_id=request.source_location_id,
            source_location_name=src_name,
            target_location_id=request.destination_location_id,
            target_location_name=dst_name,
            status="DRAFT",
            expected_arrival_date=request.expected_arrival_date.isoformat(),
            item_count=item_count,
            is_preview=False,
            warnings=warnings,
            next_actions=["No action taken — see warnings"],
            message=(
                f"Refused: source and destination location are the same "
                f"(id={request.source_location_id}); no transfer created."
            ),
        )

    api_rows = _build_row_requests(request.rows)

    # ``stock_transfer_number`` is required by the live API. Auto-generate a
    # timestamp-based default if the caller didn't provide one — matches the
    # pattern in ``_create_manufacturing_order_impl``.
    transfer_number = request.order_no or f"ST-{int(datetime.now(UTC).timestamp())}"

    api_request = APICreateStockTransferRequest(
        source_location_id=request.source_location_id,
        target_location_id=request.destination_location_id,
        expected_arrival_date=request.expected_arrival_date,
        order_created_date=datetime.now(UTC),
        stock_transfer_number=transfer_number,
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
        (
            "Use modify_stock_transfer with update_status to transition it "
            "through IN_TRANSIT → RECEIVED"
        ),
    ]
    return result


@observe_tool
@unpack_pydantic_params
async def create_stock_transfer(
    request: Annotated[CreateStockTransferRequest, Unpack()], context: Context
) -> ToolResult:
    """Create a stock transfer moving inventory between two locations.

    Two-step flow: preview=true (default) to preview, preview=false to create
    (prompts for confirmation). Requires source_location_id,
    destination_location_id, expected_arrival_date, and at least one row with
    variant_id + quantity. For batch-tracked variants, supply
    `batch_transactions` on the row.
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
        src_label = (
            f"{response.source_location_name} (ID: {response.source_location_id})"
            if response.source_location_name
            else str(response.source_location_id)
        )
        lines.append(f"- **Source Location**: {src_label}")
    if response.target_location_id is not None:
        dst_label = (
            f"{response.target_location_name} (ID: {response.target_location_id})"
            if response.target_location_name
            else str(response.target_location_id)
        )
        lines.append(f"- **Destination Location**: {dst_label}")
    if response.item_count is not None:
        lines.append(f"- **Rows**: {response.item_count}")
    if response.expected_arrival_date:
        lines.append(f"- **Expected Arrival**: {response.expected_arrival_date}")
    if response.status:
        lines.append(f"- **Status**: {response.status}")
    if response.katana_url:
        lines.append(f"- **Katana URL**: {response.katana_url}")
    if response.warnings:
        lines.append("")
        lines.append("### Warnings")
        for w in response.warnings:
            is_block = w.startswith(BLOCK_WARNING_PREFIX)
            display = w.removeprefix(BLOCK_WARNING_PREFIX).lstrip() if is_block else w
            prefix = "**[BLOCKED]** " if is_block else ""
            lines.append(f"- {prefix}{display}")
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
        description="Filter by transfer status (DRAFT, IN_TRANSIT, RECEIVED)",
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
    request field is the uppercase ``StatusLiteral`` (DRAFT, IN_TRANSIT,
    RECEIVED); ``_STATUS_API_VALUE`` maps it to the Katana wire value
    (``draft``, ``inTransit`` (camelCase!), ``received``) which is what the
    cache column stores.
    """
    from katana_public_api_client.models_pydantic._generated import (
        CachedStockTransfer,
    )

    if request.status is not None:
        api_value = _STATUS_API_VALUE[request.status]
        stmt = stmt.where(CachedStockTransfer.status == api_value.value)
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
# Tool: modify_stock_transfer — unified modification surface
# ============================================================================


class StockTransferOperation(StrEnum):
    """Operation names emitted on ActionSpecs by ``modify_stock_transfer`` /
    ``delete_stock_transfer`` plan builders."""

    UPDATE_HEADER = "update_header"
    UPDATE_STATUS = "update_status"
    DELETE = "delete"


class StockTransferHeaderPatch(BaseModel):
    """Body fields to patch on a stock transfer.

    Status is excluded — Katana exposes it via a separate
    ``PATCH /stock_transfers/{id}/status`` endpoint, surfaced as the
    ``update_status`` sub-payload.
    """

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


class StockTransferStatusPatch(BaseModel):
    """Status-transition sub-payload — maps to the dedicated status endpoint.

    Carrying it as its own typed slot (rather than a header field) makes the
    two-endpoint reality discoverable in the schema while still letting one
    ``modify_stock_transfer`` call mutate both header and status.
    """

    new_status: StatusLiteral = Field(
        ...,
        description=(
            "Target status. Valid transitions are governed by Katana — typical "
            "flow is DRAFT → IN_TRANSIT → RECEIVED."
        ),
    )


class ModifyStockTransferRequest(ConfirmableRequest):
    """Unified modification request for a stock transfer.

    Sub-payload slots cover header body fields and status transition.
    Multiple slots can be combined; actions execute in canonical order
    (header first, then status). Stock transfer rows are immutable post-
    creation — Katana doesn't expose row-CRUD endpoints. To remove a
    transfer entirely, use ``delete_stock_transfer``.
    """

    id: int = Field(..., description="Stock transfer ID")
    update_header: StockTransferHeaderPatch | None = Field(default=None)
    update_status: StockTransferStatusPatch | None = Field(default=None)


class DeleteStockTransferRequest(ConfirmableRequest):
    """Delete a stock transfer. Destructive — removes the transfer record."""

    id: int = Field(..., description="Stock transfer ID to delete")


def _build_update_header_request(
    patch: StockTransferHeaderPatch,
) -> APIUpdateStockTransferRequest:
    return APIUpdateStockTransferRequest(**unset_dict(patch))


def _build_update_status_request(
    patch: StockTransferStatusPatch,
) -> APIUpdateStockTransferStatusRequest:
    return APIUpdateStockTransferStatusRequest(
        status=_status_literal_to_enum(patch.new_status)
    )


async def _modify_stock_transfer_impl(
    request: ModifyStockTransferRequest, context: Context
) -> ModificationResponse:
    """Build the action plan from sub-payloads and either preview or execute.

    The Katana stock-transfer API has no GET-by-id endpoint, so prior-state
    capture flows through ``unknown_prior=True`` — diff entries show
    ``(prior unknown) → new`` for every field.
    """
    services = get_services(context)

    if not has_any_subpayload(request):
        raise ValueError(
            "At least one sub-payload must be set: update_header or update_status. "
            "To remove the stock transfer entirely, use delete_stock_transfer."
        )

    plan: list[ActionSpec] = []

    if request.update_header is not None:
        diff = compute_field_diff(None, request.update_header, unknown_prior=True)
        plan.append(
            ActionSpec(
                operation=StockTransferOperation.UPDATE_HEADER,
                target_id=request.id,
                diff=diff,
                apply=make_patch_apply(
                    api_update_stock_transfer,
                    services,
                    request.id,
                    _build_update_header_request(request.update_header),
                    return_type=StockTransfer,
                ),
                verify=make_response_verifier(diff),
            )
        )

    if request.update_status is not None:
        diff = compute_field_diff(None, request.update_status, unknown_prior=True)
        plan.append(
            ActionSpec(
                operation=StockTransferOperation.UPDATE_STATUS,
                target_id=request.id,
                diff=diff,
                apply=make_patch_apply(
                    api_update_stock_transfer_status,
                    services,
                    request.id,
                    _build_update_status_request(request.update_status),
                    return_type=StockTransfer,
                ),
                # No verify — status returned by the API uses Katana's wire
                # value (``inTransit``) while the request carries the tool-
                # facing literal (``IN_TRANSIT``); the response-verifier would
                # report a spurious mismatch. The action's success/error is
                # still reflected in ``ActionResult.succeeded``.
            )
        )

    return await run_modify_plan(
        request=request,
        entity_type="stock_transfer",
        entity_label=f"stock transfer {request.id}",
        tool_name="modify_stock_transfer",
        web_url_kind="stock_transfer",
        existing=None,
        plan=plan,
        # Katana exposes no GET /stock_transfers/{id}; ``existing=None`` is
        # the steady state, not a fetch failure — suppress the warning.
        has_get_endpoint=False,
    )


@observe_tool
@unpack_pydantic_params
async def modify_stock_transfer(
    request: Annotated[ModifyStockTransferRequest, Unpack()], context: Context
) -> ToolResult:
    """Modify a stock transfer — unified surface across header body fields
    and status transition.

    Sub-payloads (any subset, all optional):

    - ``update_header`` — patch body fields (stock_transfer_number,
      transfer_date, expected_arrival_date, additional_info)
    - ``update_status`` — transition through the 3-state machine
      (DRAFT / IN_TRANSIT / RECEIVED). Katana rejects invalid transitions
      with a 400; the action surfaces the API error in the response.

    Stock-transfer rows are immutable after creation — the Katana API does
    not expose row-CRUD endpoints. To remove a transfer entirely, use the
    sibling ``delete_stock_transfer`` tool.

    Two-step flow: ``preview=true`` (default) returns a per-action preview;
    ``preview=false`` executes the plan in canonical order (header before
    status). Fail-fast on error.

    Note: Katana doesn't expose a GET-by-id endpoint for stock transfers,
    so previews show every supplied field as ``(prior unknown) → new``.
    """
    response = await _modify_stock_transfer_impl(request, context)
    return to_tool_result(response)


# ============================================================================
# Tool: delete_stock_transfer
# ============================================================================


async def _delete_stock_transfer_impl(
    request: DeleteStockTransferRequest, context: Context
) -> ModificationResponse:
    """One-action plan that removes the stock transfer.

    Stock transfers have no GET-by-id endpoint, so ``fetcher=None`` skips
    prior-state capture; the response carries ``prior_state=None``.
    """
    return await run_delete_plan(
        request=request,
        services=get_services(context),
        entity_type="stock_transfer",
        entity_label=f"stock transfer {request.id}",
        web_url_kind="stock_transfer",
        fetcher=None,
        delete_endpoint=api_delete_stock_transfer,
        operation=StockTransferOperation.DELETE,
    )


@observe_tool
@unpack_pydantic_params
async def delete_stock_transfer(
    request: Annotated[DeleteStockTransferRequest, Unpack()], context: Context
) -> ToolResult:
    """Delete a stock transfer. Destructive — the transfer record is removed.

    The response's ``prior_state`` is ``None`` for stock transfers since
    Katana exposes no GET-by-id endpoint (other entities populate it
    with a snapshot for manual revert).
    """
    response = await _delete_stock_transfer_impl(request, context)
    return to_tool_result(response)


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
    _update = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
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
    mcp.tool(tags={"inventory", "stock_transfer", "write"}, annotations=_update)(
        modify_stock_transfer
    )
    mcp.tool(
        tags={"inventory", "stock_transfer", "write", "destructive"},
        annotations=_destructive,
    )(delete_stock_transfer)
