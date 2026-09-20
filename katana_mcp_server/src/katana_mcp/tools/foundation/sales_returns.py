"""Sales-return discovery and deletion tools.

Katana's ``sales_order_id`` list filter is unreliable: it accepts the query
parameter but returns unrelated returns.  This module deliberately fetches the
complete collection and applies that relationship filter locally.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, ConfigDict, Field

from katana_mcp.logging import observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools._modification import ConfirmableRequest, ModificationResponse
from katana_mcp.tools._modification_dispatch import run_delete_plan, safe_fetch_for_diff
from katana_mcp.tools.tool_result_utils import (
    UI_META,
    SoftDeletableResponse,
    enum_to_str,
    iso_or_none,
    make_json_result,
    make_tool_result,
    parse_pagination_header,
)
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.api.sales_return import (
    delete_sales_return as api_delete_sales_return,
    get_all_sales_returns as api_get_all_sales_returns,
    get_sales_return as api_get_sales_return,
)
from katana_public_api_client.client_types import UNSET
from katana_public_api_client.domain.converters import unwrap_unset
from katana_public_api_client.models import (
    SalesReturn,
    SalesReturnRefundStatus,
    SalesReturnRow,
)
from katana_public_api_client.utils import unwrap_as, unwrap_data

SalesReturnStatusLiteral = Literal["NOT_RETURNED", "RESTOCKED_ALL", "RETURNED_ALL"]
SalesReturnRefundStatusLiteral = Literal[
    "NOT_REFUNDED", "PARTIALLY_REFUNDED", "REFUNDED"
]


class ListSalesReturnsRequest(BaseModel):
    """Filters for the sales-return list.

    ``limit`` caps returned matches only. The API fetch remains complete so a
    return connected to an older sales order cannot disappear behind an
    unrelated first page.
    """

    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=50, ge=1, le=250, description="Max matches to return.")
    sales_order_id: int | None = Field(
        default=None,
        description=(
            "Original sales order ID. Applied locally because Katana's "
            "sales_order_id query filter returns unrelated sales returns."
        ),
    )
    order_no: str | None = Field(
        default=None, description="Exact sales-return order number."
    )
    return_location_id: int | None = Field(
        default=None, description="Location receiving the returned items."
    )
    status: SalesReturnStatusLiteral | None = Field(
        default=None, description="Return processing status."
    )
    refund_status: SalesReturnRefundStatusLiteral | None = Field(
        default=None, description="Refund processing status."
    )
    include_deleted: bool | None = Field(
        default=None, description="Include soft-deleted sales returns."
    )


class SalesReturnSummary(SoftDeletableResponse):
    """Compact sales-return representation used by ``list_sales_returns``."""

    id: int
    sales_order_id: int | None = None
    customer_id: int | None = None
    order_no: str | None = None
    return_location_id: int | None = None
    status: str | None = None
    refund_status: str | None = None
    currency: str | None = None
    return_date: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    row_count: int = 0


class ListSalesReturnsResponse(BaseModel):
    """Complete-match count plus the capped sales-return summaries."""

    sales_returns: list[SalesReturnSummary]
    total_count: int


class SalesReturnRowDetail(BaseModel):
    """A complete row nested under a sales return."""

    id: int
    sales_return_id: int
    variant_id: int
    fulfillment_row_id: int | None = None
    sales_order_row_id: int | None = None
    quantity: str
    net_price_per_unit: str | None = None
    reason_id: int | None = None
    restock_location_id: int | None = None
    batch_transactions: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


class GetSalesReturnResponse(SalesReturnSummary):
    """Full sales-return detail, including every returned line item."""

    order_created_date: str | None = None
    additional_info: str | None = None
    tracking_number: str | None = None
    tracking_number_url: str | None = None
    tracking_carrier: str | None = None
    tracking_method: str | None = None
    rows: list[SalesReturnRowDetail] = Field(default_factory=list)


def _value(entity: Any, name: str) -> Any:
    """Read an attrs field while translating an omitted wire value to None."""
    return unwrap_unset(value=getattr(entity, name, UNSET), default=None)


def _row_to_detail(row: SalesReturnRow) -> SalesReturnRowDetail:
    batch_transactions = _value(entity=row, name="batch_transactions") or []
    return SalesReturnRowDetail(
        id=row.id,
        sales_return_id=row.sales_return_id,
        variant_id=row.variant_id,
        fulfillment_row_id=_value(entity=row, name="fulfillment_row_id"),
        sales_order_row_id=_value(entity=row, name="sales_order_row_id"),
        quantity=row.quantity,
        net_price_per_unit=_value(entity=row, name="net_price_per_unit"),
        reason_id=_value(entity=row, name="reason_id"),
        restock_location_id=_value(entity=row, name="restock_location_id"),
        batch_transactions=[item.to_dict() for item in batch_transactions],
        created_at=iso_or_none(dt=_value(entity=row, name="created_at")),
        updated_at=iso_or_none(dt=_value(entity=row, name="updated_at")),
    )


def _summary_from_attrs(sales_return: SalesReturn) -> SalesReturnSummary:
    rows = _value(entity=sales_return, name="sales_return_rows") or []
    return SalesReturnSummary(
        id=sales_return.id,
        sales_order_id=_value(entity=sales_return, name="sales_order_id"),
        customer_id=sales_return.customer_id,
        order_no=sales_return.order_no,
        return_location_id=sales_return.return_location_id,
        status=enum_to_str(value=sales_return.status),
        refund_status=enum_to_str(
            value=_value(entity=sales_return, name="refund_status")
        ),
        currency=_value(entity=sales_return, name="currency"),
        return_date=iso_or_none(dt=_value(entity=sales_return, name="return_date")),
        created_at=iso_or_none(dt=_value(entity=sales_return, name="created_at")),
        updated_at=iso_or_none(dt=_value(entity=sales_return, name="updated_at")),
        deleted_at=iso_or_none(dt=_value(entity=sales_return, name="deleted_at")),
        row_count=len(rows),
    )


def _detail_from_attrs(sales_return: SalesReturn) -> GetSalesReturnResponse:
    summary = _summary_from_attrs(sales_return=sales_return)
    rows = _value(entity=sales_return, name="sales_return_rows") or []
    return GetSalesReturnResponse(
        **summary.model_dump(),
        order_created_date=iso_or_none(
            dt=_value(entity=sales_return, name="order_created_date")
        ),
        additional_info=_value(entity=sales_return, name="additional_info"),
        tracking_number=_value(entity=sales_return, name="tracking_number"),
        tracking_number_url=_value(entity=sales_return, name="tracking_number_url"),
        tracking_carrier=_value(entity=sales_return, name="tracking_carrier"),
        tracking_method=_value(entity=sales_return, name="tracking_method"),
        rows=[_row_to_detail(row=row) for row in rows],
    )


async def _list_sales_returns_impl(
    request: ListSalesReturnsRequest, context: Context
) -> ListSalesReturnsResponse:
    """Fetch all pages, then apply the broken relationship filter locally."""
    services = get_services(context=context)
    sales_returns: list[SalesReturn] = []
    page = 1
    while True:
        # Explicit paging has no transport-side max_pages ceiling. Fetch every
        # page before applying ``sales_order_id`` locally; otherwise an older
        # matching return can be hidden behind unrelated newer records.
        response = await api_get_all_sales_returns.asyncio_detailed(
            client=services.client,
            limit=250,
            page=page,
            status=request.status if request.status is not None else UNSET,
            include_deleted=(
                request.include_deleted
                if request.include_deleted is not None
                else UNSET
            ),
            order_no=request.order_no if request.order_no is not None else UNSET,
            return_location_id=(
                request.return_location_id
                if request.return_location_id is not None
                else UNSET
            ),
            refund_status=(
                SalesReturnRefundStatus(request.refund_status)
                if request.refund_status is not None
                else UNSET
            ),
        )
        page_returns = unwrap_data(response=response, default=[])
        sales_returns.extend(page_returns)
        pagination = parse_pagination_header(raw=response.headers.get("X-Pagination"))
        if not page_returns or (pagination is not None and pagination.last_page):
            break
        page += 1

    if request.sales_order_id is not None:
        sales_returns = [
            sales_return
            for sales_return in sales_returns
            if _value(entity=sales_return, name="sales_order_id")
            == request.sales_order_id
        ]

    summaries = [
        _summary_from_attrs(sales_return=sales_return) for sales_return in sales_returns
    ]
    return ListSalesReturnsResponse(
        sales_returns=summaries[: request.limit], total_count=len(summaries)
    )


@observe_tool
@unpack_pydantic_params
async def list_sales_returns(
    request: Annotated[ListSalesReturnsRequest, Unpack()], context: Context
) -> ToolResult:
    """List sales returns and filter by their source sales order when needed.

    ``sales_order_id`` is intentionally filtered after fetching every page:
    Katana accepts that query parameter but ignores it. ``limit`` therefore
    caps output after matching, never the upstream collection scan.
    """
    response = await _list_sales_returns_impl(request=request, context=context)
    return make_json_result(response=response)


class GetSalesReturnRequest(BaseModel):
    """Request one sales return and its line items."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Sales return ID.")


async def _get_sales_return_impl(
    request: GetSalesReturnRequest, context: Context
) -> GetSalesReturnResponse:
    response = await api_get_sales_return.asyncio_detailed(
        id=request.id, client=get_services(context=context).client
    )
    sales_return = unwrap_as(response=response, expected_type=SalesReturn)
    return _detail_from_attrs(sales_return=sales_return)


@observe_tool
@unpack_pydantic_params
async def get_sales_return(
    request: Annotated[GetSalesReturnRequest, Unpack()], context: Context
) -> ToolResult:
    """Get a sales return by ID, including its returned rows."""
    response = await _get_sales_return_impl(request=request, context=context)
    return make_json_result(response=response)


class SalesReturnOperation(StrEnum):
    """Operation names used in the delete preview/apply response."""

    DELETE = "delete"


class DeleteSalesReturnRequest(ConfirmableRequest):
    """Delete one sales return through the standard preview/apply rail."""

    id: int = Field(..., description="Sales return ID to delete.")


async def _fetch_sales_return_attrs(
    services: Any, sales_return_id: int
) -> SalesReturn | None:
    """Best-effort prior-state fetch for deletion previews."""
    return await safe_fetch_for_diff(
        api_get_sales_return,
        services,
        sales_return_id,
        return_type=SalesReturn,
        label="sales return",
    )


async def _delete_sales_return_impl(
    request: DeleteSalesReturnRequest, context: Context
) -> ModificationResponse:
    """Preview or delete a return; upstream 412/422 messages propagate intact."""
    return await run_delete_plan(
        request=request,
        services=get_services(context=context),
        entity_type="sales_return",
        entity_label=f"sales return {request.id}",
        web_url_kind=None,
        fetcher=_fetch_sales_return_attrs,
        delete_endpoint=api_delete_sales_return,
        operation=SalesReturnOperation.DELETE,
    )


@observe_tool
@unpack_pydantic_params
async def delete_sales_return(
    request: Annotated[DeleteSalesReturnRequest, Unpack()], context: Context
) -> ToolResult:
    """Delete a sales return with preview/apply confirmation.

    Use the default ``preview=true`` first. On ``preview=false``, Katana's
    error message is returned verbatim; imported returns commonly reject the
    delete with a 422 explaining that they cannot be changed in Katana.
    """
    from katana_mcp.tools.prefab_ui import build_sales_return_delete_ui

    response = await _delete_sales_return_impl(request=request, context=context)
    ui = build_sales_return_delete_ui(
        response.model_dump(),
        confirm_request=request,
        confirm_tool="delete_sales_return",
    )
    return make_tool_result(response=response, ui=ui)


def register_tools(mcp: FastMCP) -> None:
    """Register sales-return read and destructive tools."""
    from mcp.types import ToolAnnotations

    from katana_mcp.tools.prefab_ui import register_preview_tool

    read = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )
    destructive = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
        openWorldHint=True,
    )
    mcp.tool(tags={"orders", "sales_return", "read"}, annotations=read)(
        list_sales_returns
    )
    mcp.tool(tags={"orders", "sales_return", "read"}, annotations=read)(
        get_sales_return
    )
    register_preview_tool(
        mcp,
        delete_sales_return,
        tags={"orders", "sales_return", "write", "destructive"},
        annotations=destructive,
        meta=UI_META,
    )
