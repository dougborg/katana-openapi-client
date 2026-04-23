"""Customer management tools for Katana MCP Server.

Foundation tools for searching and looking up customer records. Customers
can grow to thousands and contain PII, so they are served via search tools
rather than exposed as a resource.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools.tool import ToolResult
from pydantic import BaseModel, Field

from katana_mcp.cache import EntityType
from katana_mcp.logging import observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.decorators import cache_read
from katana_mcp.tools.tool_result_utils import make_simple_result
from katana_mcp.unpack import Unpack, unpack_pydantic_params

# ============================================================================
# Tool 1: search_customers
# ============================================================================


class SearchCustomersRequest(BaseModel):
    """Request model for searching customers."""

    query: str = Field(..., description="Search query (name or email)")
    limit: int = Field(default=20, description="Maximum results to return")
    format: Literal["markdown", "json"] = Field(
        default="markdown",
        description=(
            "Output format: 'markdown' (default) for human-readable tables; "
            "'json' for structured data consumable by downstream tools/aggregations."
        ),
    )


class CustomerInfo(BaseModel):
    """Customer summary information."""

    id: int
    name: str
    email: str | None = None
    phone: str | None = None
    currency: str | None = None
    company: str | None = None


class SearchCustomersResponse(BaseModel):
    """Response containing customer search results."""

    customers: list[CustomerInfo]
    total_count: int


def _customer_from_dict(d: dict) -> CustomerInfo:
    return CustomerInfo(
        id=d.get("id", 0),
        name=d.get("name") or "",
        email=d.get("email"),
        phone=d.get("phone"),
        currency=d.get("currency"),
        company=d.get("company"),
    )


@cache_read(EntityType.CUSTOMER)
async def _search_customers_impl(
    request: SearchCustomersRequest, context: Context
) -> SearchCustomersResponse:
    """Search customers via cached FTS5 + fuzzy fallback."""
    if not request.query or not request.query.strip():
        raise ValueError("Search query cannot be empty")
    if request.limit <= 0:
        raise ValueError("Limit must be positive")

    services = get_services(context)
    customer_dicts = await services.cache.smart_search(
        EntityType.CUSTOMER, request.query, limit=request.limit
    )
    customers = [_customer_from_dict(c) for c in customer_dicts]
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

    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2),
            structured_content=response.model_dump(),
        )

    if response.customers:
        lines = [
            f"- **{c.name}** (ID: {c.id})"
            + (f" — {c.email}" if c.email else "")
            + (f" [{c.currency}]" if c.currency else "")
            for c in response.customers
        ]
        md = (
            f"## Customer Search Results\n\n"
            f"Query: `{request.query}` — {response.total_count} results\n\n"
            + "\n".join(lines)
        )
    else:
        md = f"No customers found matching `{request.query}`."

    return make_simple_result(md, structured_data=response.model_dump())


# ============================================================================
# Tool 2: get_customer
# ============================================================================


class GetCustomerRequest(BaseModel):
    """Request model for fetching a customer by ID."""

    customer_id: int = Field(..., description="Customer ID to look up")
    format: Literal["markdown", "json"] = Field(
        default="markdown",
        description=(
            "Output format: 'markdown' (default) for human-readable tables; "
            "'json' for structured data consumable by downstream tools/aggregations."
        ),
    )


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


@cache_read(EntityType.CUSTOMER)
async def _get_customer_impl(
    request: GetCustomerRequest, context: Context
) -> GetCustomerResponse:
    """Look up a customer by ID via the cache, with addresses from the API."""
    services = get_services(context)
    d = await services.cache.get_by_id(EntityType.CUSTOMER, request.customer_id)
    if not d:
        raise ValueError(f"Customer with ID {request.customer_id} not found")

    # Addresses live on a separate endpoint; no cache entity for them yet
    # (tracked in #342). Fetch-on-demand — one extra HTTP call per get_customer.
    addresses = await _fetch_customer_addresses(services, request.customer_id)

    return GetCustomerResponse(
        id=d.get("id", request.customer_id),
        name=d.get("name") or "",
        first_name=d.get("first_name"),
        last_name=d.get("last_name"),
        company=d.get("company"),
        email=d.get("email"),
        phone=d.get("phone"),
        comment=d.get("comment"),
        currency=d.get("currency"),
        reference_id=d.get("reference_id"),
        category=d.get("category"),
        discount_rate=d.get("discount_rate"),
        default_billing_id=d.get("default_billing_id"),
        default_shipping_id=d.get("default_shipping_id"),
        created_at=_iso_or_none(d.get("created_at")),
        updated_at=_iso_or_none(d.get("updated_at")),
        deleted_at=_iso_or_none(d.get("deleted_at")),
        addresses=addresses,
    )


def _render_address_md(addr: CustomerAddressInfo) -> str:
    """Render a single address as a compact multi-line block.

    Uses canonical field names so an LLM consuming the markdown can't mistake
    a rendered value for a differently-labeled field.
    """
    lines = [f"  - **id**: {addr.id}"]
    for fname in (
        "entity_type",
        "default",
        "first_name",
        "last_name",
        "company",
        "phone",
        "line_1",
        "line_2",
        "city",
        "state",
        "zip",
        "country",
    ):
        val = getattr(addr, fname)
        if val is not None and val != "":
            lines.append(f"    **{fname}**: {val}")
    return "\n".join(lines)


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

    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2),
            structured_content=response.model_dump(),
        )

    # Labels use the canonical Pydantic field names so LLM consumers can't
    # confuse a section header with the field name (see #346 follow-on).
    md_lines = [f"## {response.name}"]
    scalar_fields = (
        "id",
        "first_name",
        "last_name",
        "company",
        "email",
        "phone",
        "currency",
        "reference_id",
        "category",
        "discount_rate",
        "default_billing_id",
        "default_shipping_id",
        "comment",
        "created_at",
        "updated_at",
        "deleted_at",
    )
    for fname in scalar_fields:
        val = getattr(response, fname)
        if val is None or val == "":
            continue
        md_lines.append(f"**{fname}**: {val}")

    if response.addresses:
        md_lines.append("")
        md_lines.append(f"**addresses** ({len(response.addresses)}):")
        for addr in response.addresses:
            md_lines.append(_render_address_md(addr))
    else:
        md_lines.append("**addresses**: []")

    return make_simple_result(
        "\n".join(md_lines), structured_data=response.model_dump()
    )


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
