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
from sqlmodel import SQLModel

from katana_mcp.logging import observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.decorators import cache_read
from katana_mcp.tools.tool_result_utils import make_simple_result
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.models_pydantic._generated import (
    CachedAdditionalCost,
    CachedLocation,
    CachedOperator,
    CachedSupplier,
    CachedTaxRate,
)

# ============================================================================
# Shared helpers
# ============================================================================


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
    cached_cls: type[SQLModel],
    query: str | None,
    limit: int,
) -> tuple[list[Any], int]:
    """Return ``(rows, total_before_limit)`` for a reference list query.

    Both branches drop soft-deleted / archived rows via the
    :class:`CatalogQueries` adapter's default filters
    (``include_archived=False`` / ``include_deleted=False``) — the
    legacy cache returned every row and post-filtered in Python; the
    typed cache pushes the filter down to SQL so we get the same
    result without the round-trip.

    With ``query`` set, ``smart_search`` already caps at ``limit`` and we
    treat the filtered count as the visible total. Without a query,
    ``get_all`` returns every (filtered) row and we slice to ``limit``.

    ``query`` must already be normalized (see ``_normalize_query``).
    """
    services = get_services(context)
    catalog = services.typed_cache.catalog
    if query is not None:
        rows = await catalog.smart_search(cached_cls, query, limit=limit)
        return rows, len(rows)

    raw = await catalog.get_all(cached_cls)
    total = len(raw)
    return raw[:limit], total


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


def _supplier_summary_from_row(s: Any) -> SupplierInfo:
    """Build a ``SupplierInfo`` summary from a ``CachedSupplier`` row.

    ``code`` is preserved on the response shape for backwards
    compatibility with consumers, but the wire model
    (``CachedSupplier``) doesn't carry it — Katana never shipped a
    ``code`` field on suppliers (the legacy ``SUPPLIER_INDEX`` had
    a ``name2_key="code"`` slot that silently resolved to ``None``).
    Returns ``None`` for ``code`` until / unless Katana adds the field.
    """
    return SupplierInfo(
        id=s.id or 0,
        name=s.name or "",
        email=s.email,
        phone=s.phone,
        currency=s.currency,
        code=getattr(s, "code", None),
    )


@cache_read(CachedSupplier)
async def _list_suppliers_impl(
    request: ListSuppliersRequest, context: Context
) -> ListSuppliersResponse:
    query = _normalize_query(request.query)
    rows, total = await _fetch_rows(context, CachedSupplier, query, request.limit)
    return ListSuppliersResponse(
        suppliers=[_supplier_summary_from_row(r) for r in rows],
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


@cache_read(CachedSupplier)
async def _get_supplier_impl(
    request: GetSupplierRequest, context: Context
) -> GetSupplierResponse:
    """Look up a supplier by ID via the cache.

    Surfaces archived/deleted suppliers via ``include_deleted=True`` so
    a CLI user inspecting a soft-deleted supplier still resolves the
    record (matches the legacy cache's "show everything" semantics for
    direct lookups; the response's ``deleted_at`` field tells the caller
    when applicable).

    Most "rich" supplier fields (``code``, ``default_payment_terms``,
    address parts) don't exist on the wire — Katana's ``Supplier``
    schema only carries name/email/phone/currency/comment plus an
    address list. The response model preserves the fields for API
    stability; they always resolve to ``None``.
    """
    services = get_services(context)
    s = await services.typed_cache.catalog.get_by_id(
        CachedSupplier, request.supplier_id, include_deleted=True
    )
    if s is None:
        raise ValueError(f"Supplier with ID {request.supplier_id} not found")

    return GetSupplierResponse(
        id=s.id or request.supplier_id,
        name=s.name or "",
        email=s.email,
        phone=s.phone,
        currency=s.currency,
        code=getattr(s, "code", None),
        comment=s.comment,
        default_payment_terms=getattr(s, "default_payment_terms", None),
        address_line_1=getattr(s, "address_line_1", None),
        address_line_2=getattr(s, "address_line_2", None),
        city=getattr(s, "city", None),
        state=getattr(s, "state", None),
        zip=getattr(s, "zip", None),
        country=getattr(s, "country", None),
        created_at=_iso_or_none(s.created_at),
        updated_at=_iso_or_none(s.updated_at),
        deleted_at=_iso_or_none(s.deleted_at),
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


class AddressInfo(BaseModel):
    line_1: str | None = None
    line_2: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    country: str | None = None


class LocationInfo(BaseModel):
    id: int
    name: str
    address: AddressInfo | None = None
    is_primary: bool | None = None


class ListLocationsResponse(BaseModel):
    locations: list[LocationInfo]
    total_count: int
    query: str | None = None


def _address_from_obj(addr: Any) -> AddressInfo | None:
    """Build an :class:`AddressInfo` from a typed address row or a dict.

    The ``CachedLocation`` ``address`` column is a JSON-serialized
    ``LocationAddress`` (or ``None``); the legacy cache stored it as a
    plain dict. Accept either shape for forward compatibility — Katana's
    address schemas don't always round-trip through pydantic identically
    across regen passes.
    """
    if addr is None:
        return None

    def _clean(value: Any) -> str | None:
        # Katana sometimes returns blank address parts as "" (notably line_2)
        # rather than omitting them — treat whitespace-only as missing so the
        # all-empty case below collapses to None instead of an AddressInfo
        # full of empty strings.
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    def _get(name: str) -> Any:
        if isinstance(addr, dict):
            return addr.get(name)
        return getattr(addr, name, None)

    info = AddressInfo(
        line_1=_clean(_get("line_1")),
        line_2=_clean(_get("line_2")),
        city=_clean(_get("city")),
        state=_clean(_get("state")),
        zip=_clean(_get("zip")),
        country=_clean(_get("country")),
    )
    return info if info.model_dump(exclude_none=True) else None


def _location_from_row(loc: Any) -> LocationInfo:
    return LocationInfo(
        id=loc.id or 0,
        name=loc.name or "",
        address=_address_from_obj(getattr(loc, "address", None)),
        is_primary=getattr(loc, "is_primary", None),
    )


@cache_read(CachedLocation)
async def _list_locations_impl(
    request: ListLocationsRequest, context: Context
) -> ListLocationsResponse:
    query = _normalize_query(request.query)
    rows, total = await _fetch_rows(context, CachedLocation, query, request.limit)
    return ListLocationsResponse(
        locations=[_location_from_row(r) for r in rows],
        total_count=total,
        query=query,
    )


def _render_location_md(response: ListLocationsResponse) -> str:
    if not response.locations:
        return _empty_message("locations", response.query)

    def _city_country(loc: LocationInfo) -> str:
        if not loc.address:
            return ""
        parts = [p for p in (loc.address.city, loc.address.country) if p]
        return f" — {', '.join(parts)}" if parts else ""

    lines = [
        f"- **{loc.name}** (ID: {loc.id})"
        + (" [primary]" if loc.is_primary else "")
        + _city_country(loc)
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
    """List or search warehouses and facilities. Returns id, name, the
    is_primary flag, and a nested ``address`` object
    (``line_1``, ``line_2``, ``city``, ``state``, ``zip``, ``country``) when
    one is on file. Use the ``id`` value when creating orders or filtering
    inventory queries.

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


def _tax_rate_from_row(tr: Any) -> TaxRateInfo:
    return TaxRateInfo(
        id=tr.id or 0,
        name=tr.name or "",
        rate=getattr(tr, "rate", None),
        display_name=getattr(tr, "display_name", None),
        is_default_sales=getattr(tr, "is_default_sales", None),
        is_default_purchases=getattr(tr, "is_default_purchases", None),
    )


@cache_read(CachedTaxRate)
async def _list_tax_rates_impl(
    request: ListTaxRatesRequest, context: Context
) -> ListTaxRatesResponse:
    query = _normalize_query(request.query)
    rows, total = await _fetch_rows(context, CachedTaxRate, query, request.limit)
    return ListTaxRatesResponse(
        tax_rates=[_tax_rate_from_row(r) for r in rows],
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


def _operator_from_row(op: Any) -> OperatorInfo:
    """Build an :class:`OperatorInfo` from a ``CachedOperator`` row.

    The wire schema uses ``operator_name`` rather than ``name`` — the
    response shape preserves ``name`` for caller stability.
    """
    return OperatorInfo(id=op.id or 0, name=op.operator_name or "")


@cache_read(CachedOperator)
async def _list_operators_impl(
    request: ListOperatorsRequest, context: Context
) -> ListOperatorsResponse:
    query = _normalize_query(request.query)
    rows, total = await _fetch_rows(context, CachedOperator, query, request.limit)
    return ListOperatorsResponse(
        operators=[_operator_from_row(r) for r in rows],
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


def _additional_cost_from_row(ac: Any) -> AdditionalCostInfo:
    return AdditionalCostInfo(id=ac.id or 0, name=getattr(ac, "name", None) or "")


@cache_read(CachedAdditionalCost)
async def _list_additional_costs_impl(
    request: ListAdditionalCostsRequest, context: Context
) -> ListAdditionalCostsResponse:
    query = _normalize_query(request.query)
    rows, total = await _fetch_rows(context, CachedAdditionalCost, query, request.limit)
    return ListAdditionalCostsResponse(
        additional_costs=[_additional_cost_from_row(r) for r in rows],
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
