"""Live structured searches with cached variant and custom-field labels."""

from typing import Annotated, Any

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from mcp.types import ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field

from katana_mcp.logging import observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.custom_field_values import (
    custom_fields_read_kwargs,
    resolve_custom_field_values,
)
from katana_mcp.tools.foundation.sales_orders import (
    ListSalesOrdersResponse,
    SalesOrderRowInfo,
    SalesOrderSummary,
)
from katana_mcp.tools.tool_result_utils import (
    PaginationMeta,
    enum_to_str,
    float_or_none,
    iso_or_none,
    make_json_result,
    parse_pagination_header,
)
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_mcp.web_urls import katana_web_url
from katana_public_api_client.api.sales_order import search_sales_orders as api_orders
from katana_public_api_client.api.sales_order_row import (
    search_sales_order_rows as api_rows,
)
from katana_public_api_client.domain.converters import unwrap_unset
from katana_public_api_client.models import (
    SalesOrderRowSearchRequest as APIRowRequest,
    SalesOrderSearchRequest as APIOrderRequest,
)
from katana_public_api_client.models_pydantic._generated import CachedVariant
from katana_public_api_client.utils import unwrap_data


class SearchSalesOrdersRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filter: dict[str, Any] | None = Field(
        default=None,
        description="Structured predicates, including and/or groups. Passed to the live API without translating operators or keys.",
    )
    order: str | list[str] | None = Field(
        default=None,
        description="Sort directive or list of directives, e.g. 'created_at DESC'.",
    )
    limit: int = Field(default=50, ge=1, le=200)
    page: int = Field(default=1, ge=1)


class SearchSalesOrderRowsResponse(BaseModel):
    rows: list[SalesOrderRowInfo]
    total_count: int = Field(description="Number of rows returned on this page.")
    pagination: PaginationMeta | None = None


async def _variant_lookup(*, rows: list[Any], context: Context) -> dict[int, Any]:
    ids = {
        identifier
        for row in rows
        if (identifier := unwrap_unset(row.variant_id, None)) is not None
    }
    if not ids:
        return {}
    return await get_services(context).typed_cache.catalog.get_many_by_ids(
        CachedVariant, ids, include_deleted=True
    )


def _row_summary(*, row: Any, variants: dict[int, Any]) -> SalesOrderRowInfo:
    variant_id = unwrap_unset(row.variant_id, None)
    variant = variants.get(variant_id) if variant_id is not None else None
    return SalesOrderRowInfo(
        sales_order_id=unwrap_unset(row.sales_order_id, None),
        id=row.id,
        variant_id=variant_id,
        sku=getattr(variant, "sku", None),
        display_name=getattr(variant, "display_name", None),
        quantity=unwrap_unset(row.quantity, None),
        price_per_unit=float_or_none(unwrap_unset(row.price_per_unit, None)),
        linked_manufacturing_order_id=unwrap_unset(
            row.linked_manufacturing_order_id, None
        ),
        **custom_fields_read_kwargs(record=row),
    )


async def _search_sales_orders_impl(
    request: SearchSalesOrdersRequest, context: Context
) -> ListSalesOrdersResponse:
    response = await api_orders.asyncio_detailed(
        client=get_services(context).client,
        body=APIOrderRequest.from_dict(request.model_dump(exclude_none=True)),
    )
    raw_orders = unwrap_data(response=response, default=[])
    rows = [
        row for order in raw_orders for row in unwrap_unset(order.sales_order_rows, [])
    ]
    variants = await _variant_lookup(rows=rows, context=context)
    orders = []
    for order in raw_orders:
        row_infos = [
            _row_summary(row=row, variants=variants)
            for row in unwrap_unset(order.sales_order_rows, [])
        ]
        orders.append(
            SalesOrderSummary(
                id=order.id,
                order_no=unwrap_unset(order.order_no, None),
                customer_id=unwrap_unset(order.customer_id, None),
                location_id=unwrap_unset(order.location_id, None),
                status=enum_to_str(unwrap_unset(order.status, None)),
                production_status=enum_to_str(
                    unwrap_unset(order.production_status, None)
                ),
                invoicing_status=enum_to_str(
                    unwrap_unset(order.invoicing_status, None)
                ),
                created_at=iso_or_none(unwrap_unset(order.created_at, None)),
                delivery_date=iso_or_none(unwrap_unset(order.delivery_date, None)),
                total=float_or_none(unwrap_unset(order.total, None)),
                currency=unwrap_unset(order.currency, None),
                row_count=len(row_infos),
                rows=row_infos,
                katana_url=katana_web_url(kind="sales_order", id=order.id),
                **custom_fields_read_kwargs(record=order),
            )
        )
    await resolve_custom_field_values(
        records=[*orders, *(row for order in orders for row in (order.rows or []))],
        context=context,
    )
    pagination = parse_pagination_header(
        raw=response.headers.get("x-pagination") or response.headers.get("X-Pagination")
    )
    return ListSalesOrdersResponse(
        orders=orders, total_count=len(orders), pagination=pagination
    )


async def _search_sales_order_rows_impl(
    request: SearchSalesOrdersRequest, context: Context
) -> SearchSalesOrderRowsResponse:
    response = await api_rows.asyncio_detailed(
        client=get_services(context).client,
        body=APIRowRequest.from_dict(request.model_dump(exclude_none=True)),
    )
    raw_rows = unwrap_data(response=response, default=[])
    variants = await _variant_lookup(rows=raw_rows, context=context)
    rows = [_row_summary(row=row, variants=variants) for row in raw_rows]
    await resolve_custom_field_values(records=rows, context=context)
    pagination = parse_pagination_header(
        raw=response.headers.get("x-pagination") or response.headers.get("X-Pagination")
    )
    return SearchSalesOrderRowsResponse(
        rows=rows, total_count=len(rows), pagination=pagination
    )


@observe_tool
@unpack_pydantic_params
async def search_sales_orders(
    request: Annotated[SearchSalesOrdersRequest, Unpack()], context: Context
) -> ToolResult:
    """Search sales orders live using structured filters and sort directives.

    Each call uses API quota. Arbitrary filters bypass the order cache; results
    include cached variant names and resolved custom-field labels. For basic
    filters, list_sales_orders provides a cache-backed alternative.
    """
    return make_json_result(
        response=await _search_sales_orders_impl(request=request, context=context)
    )


@observe_tool
@unpack_pydantic_params
async def search_sales_order_rows(
    request: Annotated[SearchSalesOrdersRequest, Unpack()], context: Context
) -> ToolResult:
    """Search sales order rows live with structured filters and sort directives.

    Each call uses API quota and bypasses the order cache. Results preserve
    custom-field values and resolve labels, including historical choice labels.
    """
    return make_json_result(
        response=await _search_sales_order_rows_impl(request=request, context=context)
    )


def register_tools(mcp: FastMCP) -> None:
    annotations = ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    )
    mcp.tool(tags={"sales-orders", "read"}, annotations=annotations)(
        search_sales_orders
    )
    mcp.tool(tags={"sales-orders", "read"}, annotations=annotations)(
        search_sales_order_rows
    )
