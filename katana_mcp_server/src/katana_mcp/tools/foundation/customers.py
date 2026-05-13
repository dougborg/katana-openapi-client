"""Customer management tools for Katana MCP Server.

Foundation tools for searching and looking up customer records. Customers
can grow to thousands and contain PII, so they are served via search tools
rather than exposed as a resource.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, ConfigDict, Field

from katana_mcp.logging import observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.decorators import cache_read
from katana_mcp.tools.tool_result_utils import make_json_result
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_mcp.web_urls import katana_web_url
from katana_public_api_client.models_pydantic._generated import CachedCustomer

# ============================================================================
# Tool 1: search_customers
# ============================================================================


class SearchCustomersRequest(BaseModel):
    """Request model for searching customers."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(..., description="Search query (name or email)")
    limit: int = Field(default=20, description="Maximum results to return")


class CustomerInfo(BaseModel):
    """Customer summary information."""

    id: int
    name: str
    email: str | None = None
    phone: str | None = None
    currency: str | None = None
    company: str | None = None
    katana_url: str | None = None


class SearchCustomersResponse(BaseModel):
    """Response containing customer search results."""

    customers: list[CustomerInfo]
    total_count: int


def _customer_from_cached(c: Any) -> CustomerInfo:
    """Build a ``CustomerInfo`` summary from a ``CachedCustomer`` row.

    Accepts ``Any`` so legacy test fixtures that pass plain dicts still
    work — the field accesses use ``getattr`` with sensible fallbacks.
    Production callers always pass a typed ``CachedCustomer``.
    """
    if isinstance(c, dict):
        get = c.get  # type: ignore[union-attr]
    else:

        def get(key: str, default: Any = None) -> Any:
            return getattr(c, key, default)

    customer_id = get("id")
    return CustomerInfo(
        id=customer_id or 0,
        name=get("name") or "",
        email=get("email"),
        phone=get("phone"),
        currency=get("currency"),
        company=get("company"),
        katana_url=katana_web_url("customer", customer_id),
    )


@cache_read(CachedCustomer)
async def _search_customers_impl(
    request: SearchCustomersRequest, context: Context
) -> SearchCustomersResponse:
    """Search customers via cached FTS5 + fuzzy fallback."""
    if not request.query or not request.query.strip():
        raise ValueError("Search query cannot be empty")
    if request.limit <= 0:
        raise ValueError("Limit must be positive")

    services = get_services(context)
    rows = await services.typed_cache.catalog.smart_search(
        CachedCustomer, request.query, limit=request.limit
    )
    customers = [_customer_from_cached(c) for c in rows]
    return SearchCustomersResponse(customers=customers, total_count=len(customers))


@observe_tool
@unpack_pydantic_params
async def search_customers(
    request: Annotated[SearchCustomersRequest, Unpack()], context: Context
) -> ToolResult:
    """Search for customers by name or email.

    Use this to find customer_id values needed by create_sales_order. Returns
    customer summaries (id, name, email, phone, currency). For full details
    use get_customer by id.

    Query must not be empty. Default limit is 20 results.
    """
    response = await _search_customers_impl(request, context)
    return make_json_result(response)


# ============================================================================
# Tool 2: get_customer
# ============================================================================


class GetCustomerRequest(BaseModel):
    """Request model for fetching a customer by ID."""

    model_config = ConfigDict(extra="forbid")

    customer_id: int = Field(..., description="Customer ID to look up")


class CustomerAddressInfo(BaseModel):
    """Full customer address — one entry in ``GetCustomerResponse.addresses``.

    Mirrors the wire-shape of ``katana_public_api_client.models.CustomerAddress``
    (same field names, every field surfaced) so callers don't need a follow-up
    lookup for identity fields. Field **types** intentionally diverge from the
    generated attrs model: enums (``entity_type``) are rendered as strings and
    timestamps as ISO strings, matching what JSON consumers actually see on
    the wire.
    """

    id: int
    customer_id: int
    entity_type: str | None = None
    default: bool | None = None
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    phone: str | None = None
    line_1: str | None = None
    line_2: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    country: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None


class GetCustomerResponse(BaseModel):
    """Full customer details. Exhaustive — every field Katana exposes on
    ``Customer`` is surfaced (including nested addresses) so callers don't
    need follow-up lookups for standard fields.
    """

    id: int
    katana_url: str | None = None
    name: str
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    email: str | None = None
    phone: str | None = None
    comment: str | None = None
    currency: str | None = None
    reference_id: str | None = None
    category: str | None = None
    discount_rate: float | None = None
    default_billing_id: int | None = None
    default_shipping_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None
    addresses: list[CustomerAddressInfo] = Field(default_factory=list)


def _iso_or_none(value: Any) -> str | None:
    """Return an ISO-8601 string for a datetime-or-str value, else None."""
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


async def _fetch_customer_addresses(
    services: Any, customer_id: int
) -> list[CustomerAddressInfo]:
    """Fetch all addresses for a customer via the /customer_addresses endpoint.

    Best-effort — the cache epic (#342) will fold addresses into the cache
    sync. Until then, a transient failure shouldn't crash ``get_customer``
    when the cache already has the customer record. Both transport-level
    exceptions (timeouts, connection errors, unexpected statuses) and
    API-error response bodies degrade to an empty list.
    """
    import httpx

    from katana_public_api_client.api.customer_address import (
        get_all_customer_addresses,
    )
    from katana_public_api_client.errors import UnexpectedStatus
    from katana_public_api_client.utils import unwrap_data

    try:
        response = await get_all_customer_addresses.asyncio_detailed(
            client=services.client,
            customer_ids=[customer_id],
            limit=250,
        )
    except (httpx.HTTPError, UnexpectedStatus):
        return []
    rows = unwrap_data(response, default=[], raise_on_error=False)
    result: list[CustomerAddressInfo] = []
    for row in rows:
        row_dict = row.to_dict() if hasattr(row, "to_dict") else row
        # The attrs model uses `zip_` as a Python keyword workaround; the API
        # wire format is `zip`. `to_dict()` emits the wire name.
        result.append(
            CustomerAddressInfo(
                id=row_dict.get("id", 0),
                customer_id=row_dict.get("customer_id", customer_id),
                entity_type=row_dict.get("entity_type"),
                default=row_dict.get("default"),
                first_name=row_dict.get("first_name"),
                last_name=row_dict.get("last_name"),
                company=row_dict.get("company"),
                phone=row_dict.get("phone"),
                line_1=row_dict.get("line_1"),
                line_2=row_dict.get("line_2"),
                city=row_dict.get("city"),
                state=row_dict.get("state"),
                zip=row_dict.get("zip"),
                country=row_dict.get("country"),
                created_at=_iso_or_none(row_dict.get("created_at")),
                updated_at=_iso_or_none(row_dict.get("updated_at")),
                deleted_at=_iso_or_none(row_dict.get("deleted_at")),
            )
        )
    return result


@cache_read(CachedCustomer)
async def _get_customer_impl(
    request: GetCustomerRequest, context: Context
) -> GetCustomerResponse:
    """Look up a customer by ID via the cache, with addresses from the API.

    Passes ``include_deleted=True`` so a soft-deleted customer record
    still resolves to its cached fields — matches the legacy cache's
    behavior of returning every row regardless of soft-state. Tools
    that need to surface "this customer was deleted" use the
    ``deleted_at`` field on the response.
    """
    services = get_services(context)
    row = await services.typed_cache.catalog.get_by_id(
        CachedCustomer, request.customer_id, include_deleted=True
    )
    if row is None:
        raise ValueError(f"Customer with ID {request.customer_id} not found")

    # Addresses live on a separate endpoint; no cache entity for them yet
    # (tracked in #342). Fetch-on-demand — one extra HTTP call per get_customer.
    addresses = await _fetch_customer_addresses(services, request.customer_id)

    # ``getattr`` keeps the path tolerant of legacy dict fixtures that
    # exist in some tests; production callers always pass a typed
    # ``CachedCustomer`` and the access reduces to a normal attribute read.
    if isinstance(row, dict):
        get = row.get  # type: ignore[union-attr]
    else:

        def get(key: str, default: Any = None) -> Any:
            return getattr(row, key, default)

    customer_id = get("id") or request.customer_id
    return GetCustomerResponse(
        id=customer_id,
        katana_url=katana_web_url("customer", customer_id),
        name=get("name") or "",
        first_name=get("first_name"),
        last_name=get("last_name"),
        company=get("company"),
        email=get("email"),
        phone=get("phone"),
        comment=get("comment"),
        currency=get("currency"),
        reference_id=get("reference_id"),
        category=get("category"),
        discount_rate=get("discount_rate"),
        default_billing_id=get("default_billing_id"),
        default_shipping_id=get("default_shipping_id"),
        created_at=_iso_or_none(get("created_at")),
        updated_at=_iso_or_none(get("updated_at")),
        deleted_at=_iso_or_none(get("deleted_at")),
        addresses=addresses,
    )


@observe_tool
@unpack_pydantic_params
async def get_customer(
    request: Annotated[GetCustomerRequest, Unpack()], context: Context
) -> ToolResult:
    """Get full details for a specific customer by ID.

    Returns every field Katana exposes on the customer record — identity,
    contact details, pricing (discount_rate), default address IDs, timestamps,
    and the full list of associated billing/shipping addresses. Use
    search_customers first to find the customer_id; this tool is the
    single-call path to the rest.
    """
    response = await _get_customer_impl(request, context)
    return make_json_result(response)


def register_tools(mcp: FastMCP) -> None:
    """Register all customer tools with the FastMCP instance."""
    from mcp.types import ToolAnnotations

    _read = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )

    mcp.tool(tags={"customers", "read"}, annotations=_read)(search_customers)
    mcp.tool(tags={"customers", "read"}, annotations=_read)(get_customer)


__all__ = ["register_tools"]
