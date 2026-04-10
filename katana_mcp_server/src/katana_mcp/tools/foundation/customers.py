"""Customer management tools for Katana MCP Server.

Foundation tools for searching and looking up customer records. Customers
can grow to thousands and contain PII, so they are served via search tools
rather than exposed as a resource.
"""

from __future__ import annotations

from typing import Annotated

from fastmcp import Context, FastMCP
from fastmcp.tools.tool import ToolResult
from pydantic import BaseModel, Field

from katana_mcp.cache import EntityType
from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.decorators import cache_read
from katana_mcp.tools.tool_result_utils import make_simple_result
from katana_mcp.unpack import Unpack, unpack_pydantic_params

logger = get_logger(__name__)


# ============================================================================
# Tool 1: search_customers
# ============================================================================


class SearchCustomersRequest(BaseModel):
    """Request model for searching customers."""

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


class GetCustomerResponse(BaseModel):
    """Response containing full customer details."""

    id: int
    name: str
    email: str | None = None
    phone: str | None = None
    currency: str | None = None
    company: str | None = None
    category: str | None = None
    comment: str | None = None


@cache_read(EntityType.CUSTOMER)
async def _get_customer_impl(
    request: GetCustomerRequest, context: Context
) -> GetCustomerResponse:
    """Look up a customer by ID via the cache."""
    services = get_services(context)
    d = await services.cache.get_by_id(EntityType.CUSTOMER, request.customer_id)
    if not d:
        raise ValueError(f"Customer with ID {request.customer_id} not found")

    return GetCustomerResponse(
        id=d.get("id", request.customer_id),
        name=d.get("name") or "",
        email=d.get("email"),
        phone=d.get("phone"),
        currency=d.get("currency"),
        company=d.get("company"),
        category=d.get("category"),
        comment=d.get("comment"),
    )


@observe_tool
@unpack_pydantic_params
async def get_customer(
    request: Annotated[GetCustomerRequest, Unpack()], context: Context
) -> ToolResult:
    """Get full details for a specific customer by ID.

    Returns name, email, phone, currency, category, and comments. Use
    search_customers first to find the customer_id.
    """
    response = await _get_customer_impl(request, context)

    md_lines = [f"## {response.name}", f"**ID**: {response.id}"]
    if response.email:
        md_lines.append(f"**Email**: {response.email}")
    if response.phone:
        md_lines.append(f"**Phone**: {response.phone}")
    if response.currency:
        md_lines.append(f"**Currency**: {response.currency}")
    if response.company:
        md_lines.append(f"**Company**: {response.company}")
    if response.category:
        md_lines.append(f"**Category**: {response.category}")
    if response.comment:
        md_lines.append(f"**Comment**: {response.comment}")

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
