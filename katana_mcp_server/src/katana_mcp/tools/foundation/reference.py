"""Cache-backed search tools for stable reference data — suppliers,
locations, tax rates, operators, and the additional-cost catalog. Each
``list_*`` tool accepts ``query`` (optional fuzzy name/code search,
FTS5 with difflib fallback), ``limit`` (default 50, max 250), and
``format`` (``"markdown"`` | ``"json"``). ``get_supplier(supplier_id)``
returns the full single-supplier record.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, ConfigDict, Field

from katana_mcp.cache import EntityType
from katana_mcp.logging import observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.decorators import cache_read
from katana_mcp.tools.tool_result_utils import make_simple_result
from katana_mcp.unpack import Unpack, unpack_pydantic_params

# ============================================================================
# Shared helpers
# ============================================================================


def _filter_deleted(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [e for e in entities if not e.get("deleted_at")]


def _normalize_query(query: str | None) -> str | None:
    """Strip whitespace and treat empty / whitespace-only input as no query.

    Caller-side normalization keeps a single canonical form flowing to the
    cache, the response model, and the markdown header — otherwise
    ``query="   "`` falls through to the no-query path but still renders
    "query `   `" in the header because the raw value remains truthy.
    """
    if query is None:
        return None
    stripped = query.strip()
    return stripped or None


async def _fetch_rows(
    context: Context,
    entity_type: EntityType,
    query: str | None,
    limit: int,
) -> tuple[list[dict[str, Any]], int]:
    """Return ``(rows, total_before_limit)`` for a reference list query.

    Both branches drop soft-deleted rows. With ``query`` set,
    ``smart_search`` already caps at ``limit`` and we treat the filtered
    count as the visible total. Without a query, ``get_all`` + Python-side
    soft-delete filter is the only path — the cache index has no
    ``is_deleted`` column today, so SQL pushdown is a follow-up.

    ``query`` must already be normalized (see ``_normalize_query``).
    """
    services = get_services(context)
    if query is not None:
        rows = await services.cache.smart_search(entity_type, query, limit=limit)
        rows = _filter_deleted(rows)
        return rows, len(rows)

    raw = await services.cache.get_all(entity_type)
    filtered = _filter_deleted(raw)
    total = len(filtered)
    return filtered[:limit], total


def _list_header(title: str, query: str | None, returned: int, total: int) -> str:
    if query:
        return f"## {title} — query `{query}` ({returned} of {total})"
    return f"## {title} ({returned} of {total})"


def _empty_message(entity_label: str, query: str | None) -> str:
    if query:
        return f"No {entity_label} found matching `{query}`."
    return f"No {entity_label} cached."


# ============================================================================
# Suppliers — list_suppliers + get_supplier
# ============================================================================


class ListSuppliersRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str | None = Field(
        default=None,
        description=(
            "Fuzzy search over supplier name and code (FTS5 with difflib "
            "fallback for typos). Omit to list all suppliers up to limit."
        ),
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=250,
        description="Maximum rows to return (default 50, max 250)",
    )
    format: Literal["markdown", "json"] = Field(
        default="markdown",
        description=(
            "Output format: 'markdown' (default) for human-readable bullets; "
            "'json' for structured data consumable by downstream tools."
        ),
    )


class SupplierInfo(BaseModel):
    id: int
    name: str
    email: str | None = None
    phone: str | None = None
    currency: str | None = None
    code: str | None = None


class ListSuppliersResponse(BaseModel):
    suppliers: list[SupplierInfo]
    total_count: int
    query: str | None = None


def _supplier_summary_from_dict(d: dict[str, Any]) -> SupplierInfo:
    return SupplierInfo(
        id=d.get("id") or 0,
        name=d.get("name") or "",
        email=d.get("email"),
        phone=d.get("phone"),
        currency=d.get("currency"),
        code=d.get("code"),
    )


@cache_read(EntityType.SUPPLIER)
async def _list_suppliers_impl(
    request: ListSuppliersRequest, context: Context
) -> ListSuppliersResponse:
    query = _normalize_query(request.query)
    rows, total = await _fetch_rows(context, EntityType.SUPPLIER, query, request.limit)
    return ListSuppliersResponse(
        suppliers=[_supplier_summary_from_dict(r) for r in rows],
        total_count=total,
        query=query,
    )


def _render_supplier_list_md(response: ListSuppliersResponse) -> str:
    if not response.suppliers:
        return _empty_message("suppliers", response.query)

    lines = [
        f"- **{s.name}** (ID: {s.id})"
        + (f" — {s.email}" if s.email else "")
        + (f" [{s.currency}]" if s.currency else "")
        + (f" code:{s.code}" if s.code else "")
        for s in response.suppliers
    ]
    header = _list_header(
        "Suppliers", response.query, len(response.suppliers), response.total_count
    )
    return header + "\n\n" + "\n".join(lines)


@observe_tool
@unpack_pydantic_params
async def list_suppliers(
    request: Annotated[ListSuppliersRequest, Unpack()], context: Context
) -> ToolResult:
    """List or search suppliers. Returns id, name, email, phone, currency, and
    code — enough to pick the right ``supplier_id`` for ``create_purchase_order``
    or to set ``default_supplier_id`` on a material.

    Pass ``query`` to fuzzy-match by name or code (recommended when you know
    the supplier name); omit to browse. Default limit caps output at 50 rows.
    Use ``get_supplier(supplier_id)`` for the full-detail record.
    """
    response = await _list_suppliers_impl(request, context)

    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2),
            structured_content=response.model_dump(),
        )
    return make_simple_result(
        _render_supplier_list_md(response), structured_data=response.model_dump()
    )


class GetSupplierRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supplier_id: int = Field(..., description="Supplier ID to look up")
    format: Literal["markdown", "json"] = Field(default="markdown")


class GetSupplierResponse(BaseModel):
    id: int
    name: str
    email: str | None = None
    phone: str | None = None
    currency: str | None = None
    code: str | None = None
    comment: str | None = None
    default_payment_terms: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    country: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None


def _iso_or_none(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


@cache_read(EntityType.SUPPLIER)
async def _get_supplier_impl(
    request: GetSupplierRequest, context: Context
) -> GetSupplierResponse:
    services = get_services(context)
    d = await services.cache.get_by_id(EntityType.SUPPLIER, request.supplier_id)
    if not d:
        raise ValueError(f"Supplier with ID {request.supplier_id} not found")

    return GetSupplierResponse(
        id=d.get("id", request.supplier_id),
        name=d.get("name") or "",
        email=d.get("email"),
        phone=d.get("phone"),
        currency=d.get("currency"),
        code=d.get("code"),
        comment=d.get("comment"),
        default_payment_terms=d.get("default_payment_terms"),
        address_line_1=d.get("address_line_1"),
        address_line_2=d.get("address_line_2"),
        city=d.get("city"),
        state=d.get("state"),
        zip=d.get("zip"),
        country=d.get("country"),
        created_at=_iso_or_none(d.get("created_at")),
        updated_at=_iso_or_none(d.get("updated_at")),
        deleted_at=_iso_or_none(d.get("deleted_at")),
    )


def _render_supplier_detail_md(response: GetSupplierResponse) -> str:
    md_lines = [f"## {response.name}"]
    fields = (
        "id",
        "email",
        "phone",
        "currency",
        "code",
        "default_payment_terms",
        "address_line_1",
        "address_line_2",
        "city",
        "state",
        "zip",
        "country",
        "comment",
        "created_at",
        "updated_at",
        "deleted_at",
    )
    for fname in fields:
        val = getattr(response, fname)
        if val is None or val == "":
            continue
        md_lines.append(f"**{fname}**: {val}")
    return "\n".join(md_lines)


@observe_tool
@unpack_pydantic_params
async def get_supplier(
    request: Annotated[GetSupplierRequest, Unpack()], context: Context
) -> ToolResult:
    """Get full details for a specific supplier by ID.

    Returns every field the cache holds — contact info, address, currency,
    payment terms, internal supplier code, and timestamps. Use
    ``list_suppliers(query=...)`` to find the ``supplier_id`` first; this
    tool is the single-call path to the rest.
    """
    response = await _get_supplier_impl(request, context)

    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2),
            structured_content=response.model_dump(),
        )
    return make_simple_result(
        _render_supplier_detail_md(response), structured_data=response.model_dump()
    )


# ============================================================================
# Locations — list_locations
# ============================================================================


class ListLocationsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str | None = Field(default=None, description="Fuzzy search by location name")
    limit: int = Field(default=50, ge=1, le=250)
    format: Literal["markdown", "json"] = Field(default="markdown")


class LocationInfo(BaseModel):
    id: int
    name: str
    address: str | None = None
    city: str | None = None
    country: str | None = None
    is_primary: bool | None = None


class ListLocationsResponse(BaseModel):
    locations: list[LocationInfo]
    total_count: int
    query: str | None = None


def _location_from_dict(d: dict[str, Any]) -> LocationInfo:
    return LocationInfo(
        id=d.get("id") or 0,
        name=d.get("name") or "",
        address=d.get("address"),
        city=d.get("city"),
        country=d.get("country"),
        is_primary=d.get("is_primary"),
    )


@cache_read(EntityType.LOCATION)
async def _list_locations_impl(
    request: ListLocationsRequest, context: Context
) -> ListLocationsResponse:
    query = _normalize_query(request.query)
    rows, total = await _fetch_rows(context, EntityType.LOCATION, query, request.limit)
    return ListLocationsResponse(
        locations=[_location_from_dict(r) for r in rows],
        total_count=total,
        query=query,
    )


def _render_location_md(response: ListLocationsResponse) -> str:
    if not response.locations:
        return _empty_message("locations", response.query)
    lines = [
        f"- **{loc.name}** (ID: {loc.id})"
        + (" [primary]" if loc.is_primary else "")
        + (f" — {loc.city}, {loc.country}" if loc.city or loc.country else "")
        for loc in response.locations
    ]
    header = _list_header(
        "Locations", response.query, len(response.locations), response.total_count
    )
    return header + "\n\n" + "\n".join(lines)


@observe_tool
@unpack_pydantic_params
async def list_locations(
    request: Annotated[ListLocationsRequest, Unpack()], context: Context
) -> ToolResult:
    """List or search warehouses and facilities. Returns id, name, address,
    city/country, and the is_primary flag. Use the ``id`` value when
    creating orders or filtering inventory queries.

    Pass ``query`` to fuzzy-match by name; omit to browse. Default limit
    caps output at 50 rows.
    """
    response = await _list_locations_impl(request, context)
    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2),
            structured_content=response.model_dump(),
        )
    return make_simple_result(
        _render_location_md(response), structured_data=response.model_dump()
    )


# ============================================================================
# Tax rates — list_tax_rates
# ============================================================================


class ListTaxRatesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str | None = Field(default=None, description="Fuzzy search by tax-rate name")
    limit: int = Field(default=50, ge=1, le=250)
    format: Literal["markdown", "json"] = Field(default="markdown")


class TaxRateInfo(BaseModel):
    id: int
    name: str
    rate: float | None = None
    display_name: str | None = None
    is_default_sales: bool | None = None
    is_default_purchases: bool | None = None


class ListTaxRatesResponse(BaseModel):
    tax_rates: list[TaxRateInfo]
    total_count: int
    query: str | None = None


def _tax_rate_from_dict(d: dict[str, Any]) -> TaxRateInfo:
    return TaxRateInfo(
        id=d.get("id") or 0,
        name=d.get("name") or "",
        rate=d.get("rate"),
        display_name=d.get("display_name"),
        is_default_sales=d.get("is_default_sales"),
        is_default_purchases=d.get("is_default_purchases"),
    )


@cache_read(EntityType.TAX_RATE)
async def _list_tax_rates_impl(
    request: ListTaxRatesRequest, context: Context
) -> ListTaxRatesResponse:
    query = _normalize_query(request.query)
    rows, total = await _fetch_rows(context, EntityType.TAX_RATE, query, request.limit)
    return ListTaxRatesResponse(
        tax_rates=[_tax_rate_from_dict(r) for r in rows],
        total_count=total,
        query=query,
    )


def _render_tax_rate_md(response: ListTaxRatesResponse) -> str:
    if not response.tax_rates:
        return _empty_message("tax rates", response.query)
    lines = []
    for tr in response.tax_rates:
        flags = []
        if tr.is_default_sales:
            flags.append("default-sales")
        if tr.is_default_purchases:
            flags.append("default-purchases")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        rate_str = f" — {tr.rate}%" if tr.rate is not None else ""
        display = f" ({tr.display_name})" if tr.display_name else ""
        lines.append(f"- **{tr.name}** (ID: {tr.id}){display}{rate_str}{flag_str}")
    header = _list_header(
        "Tax Rates", response.query, len(response.tax_rates), response.total_count
    )
    return header + "\n\n" + "\n".join(lines)


@observe_tool
@unpack_pydantic_params
async def list_tax_rates(
    request: Annotated[ListTaxRatesRequest, Unpack()], context: Context
) -> ToolResult:
    """List or search configured tax rates. Returns id, name, rate, display
    name, and default-for-sales / default-for-purchases flags. Use the
    ``id`` value when creating sales orders or purchase-order line items
    with explicit tax assignments.

    Pass ``query`` to fuzzy-match by name; omit to browse.
    """
    response = await _list_tax_rates_impl(request, context)
    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2),
            structured_content=response.model_dump(),
        )
    return make_simple_result(
        _render_tax_rate_md(response), structured_data=response.model_dump()
    )


# ============================================================================
# Operators — list_operators
# ============================================================================


class ListOperatorsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str | None = Field(default=None, description="Fuzzy search by operator name")
    limit: int = Field(default=50, ge=1, le=250)
    format: Literal["markdown", "json"] = Field(default="markdown")


class OperatorInfo(BaseModel):
    id: int
    name: str


class ListOperatorsResponse(BaseModel):
    operators: list[OperatorInfo]
    total_count: int
    query: str | None = None


def _operator_from_dict(d: dict[str, Any]) -> OperatorInfo:
    return OperatorInfo(id=d.get("id") or 0, name=d.get("name") or "")


@cache_read(EntityType.OPERATOR)
async def _list_operators_impl(
    request: ListOperatorsRequest, context: Context
) -> ListOperatorsResponse:
    query = _normalize_query(request.query)
    rows, total = await _fetch_rows(context, EntityType.OPERATOR, query, request.limit)
    return ListOperatorsResponse(
        operators=[_operator_from_dict(r) for r in rows],
        total_count=total,
        query=query,
    )


def _render_operator_md(response: ListOperatorsResponse) -> str:
    if not response.operators:
        return _empty_message("operators", response.query)
    lines = [f"- **{op.name}** (ID: {op.id})" for op in response.operators]
    header = _list_header(
        "Operators", response.query, len(response.operators), response.total_count
    )
    return header + "\n\n" + "\n".join(lines)


@observe_tool
@unpack_pydantic_params
async def list_operators(
    request: Annotated[ListOperatorsRequest, Unpack()], context: Context
) -> ToolResult:
    """List or search manufacturing operators. Returns id and name. Use the
    ``id`` value when assigning operators to manufacturing-order operation
    rows or naming the packer on a sales order.

    Pass ``query`` to fuzzy-match by name; omit to browse.
    """
    response = await _list_operators_impl(request, context)
    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2),
            structured_content=response.model_dump(),
        )
    return make_simple_result(
        _render_operator_md(response), structured_data=response.model_dump()
    )


# ============================================================================
# Additional costs — list_additional_costs
# ============================================================================


class ListAdditionalCostsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str | None = Field(
        default=None, description="Fuzzy search by additional-cost name"
    )
    limit: int = Field(default=50, ge=1, le=250)
    format: Literal["markdown", "json"] = Field(default="markdown")


class AdditionalCostInfo(BaseModel):
    id: int
    name: str


class ListAdditionalCostsResponse(BaseModel):
    additional_costs: list[AdditionalCostInfo]
    total_count: int
    query: str | None = None


def _additional_cost_from_dict(d: dict[str, Any]) -> AdditionalCostInfo:
    return AdditionalCostInfo(id=d.get("id") or 0, name=d.get("name") or "")


@cache_read(EntityType.ADDITIONAL_COST)
async def _list_additional_costs_impl(
    request: ListAdditionalCostsRequest, context: Context
) -> ListAdditionalCostsResponse:
    query = _normalize_query(request.query)
    rows, total = await _fetch_rows(
        context, EntityType.ADDITIONAL_COST, query, request.limit
    )
    return ListAdditionalCostsResponse(
        additional_costs=[_additional_cost_from_dict(r) for r in rows],
        total_count=total,
        query=query,
    )


def _render_additional_cost_md(response: ListAdditionalCostsResponse) -> str:
    if not response.additional_costs:
        return _empty_message("additional costs", response.query)
    lines = [f"- **{ac.name}** (ID: {ac.id})" for ac in response.additional_costs]
    header = _list_header(
        "Additional Costs",
        response.query,
        len(response.additional_costs),
        response.total_count,
    )
    return header + "\n\n" + "\n".join(lines)


@observe_tool
@unpack_pydantic_params
async def list_additional_costs(
    request: Annotated[ListAdditionalCostsRequest, Unpack()], context: Context
) -> ToolResult:
    """List or search the additional-cost catalog (freight, duties, handling
    fees, etc.). Returns id and name. Use the ``id`` value when calling
    ``modify_purchase_order`` with ``add_additional_costs=[...]``. Pair
    with ``list_tax_rates`` for the matching ``tax_rate_id``.

    Pass ``query`` to fuzzy-match by name; omit to browse.
    """
    response = await _list_additional_costs_impl(request, context)
    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2),
            structured_content=response.model_dump(),
        )
    return make_simple_result(
        _render_additional_cost_md(response), structured_data=response.model_dump()
    )


# ============================================================================
# Registration
# ============================================================================


def register_tools(mcp: FastMCP) -> None:
    """Register reference-data tools with the FastMCP instance."""
    from mcp.types import ToolAnnotations

    _read = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )

    mcp.tool(tags={"reference", "read"}, annotations=_read)(list_locations)
    mcp.tool(tags={"reference", "read"}, annotations=_read)(list_suppliers)
    mcp.tool(tags={"reference", "read"}, annotations=_read)(get_supplier)
    mcp.tool(tags={"reference", "read"}, annotations=_read)(list_tax_rates)
    mcp.tool(tags={"reference", "read"}, annotations=_read)(list_operators)
    mcp.tool(tags={"reference", "read"}, annotations=_read)(list_additional_costs)


__all__ = ["register_tools"]
