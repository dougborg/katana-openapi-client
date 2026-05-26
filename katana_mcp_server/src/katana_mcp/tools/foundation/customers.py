"""Customer management tools for Katana MCP Server.

Foundation tools for searching, looking up, and creating customer records.
Customers can grow to thousands and contain PII, so reads go through search
tools rather than a resource; writes follow the standard preview/apply
pattern with cache write-through so the new record surfaces in
``search_customers`` immediately.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, ConfigDict, Field

from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.decorators import cache_read
from katana_mcp.tools.tool_result_utils import (
    UI_META,
    SoftDeletableResponse,
    make_json_result,
    make_tool_result,
)
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_mcp.web_urls import katana_web_url
from katana_public_api_client.models_pydantic._generated import CachedCustomer

logger = get_logger(__name__)

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


class CustomerAddressInfo(SoftDeletableResponse):
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


class GetCustomerResponse(SoftDeletableResponse):
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


# ============================================================================
# Tool 3: create_customer
# ============================================================================


AddressEntityType = Literal["billing", "shipping"]


class CreateCustomerAddressRequest(BaseModel):
    """One address (billing or shipping) to attach to the new customer.

    Mirrors the shape of ``CreateCustomerRequest.addresses[*]`` in the
    Katana OpenAPI spec — fields are optional individually so a caller
    can supply just the parts they know (e.g., a country-only address for
    a record they'll flesh out later). ``entity_type`` is the only field
    that's effectively required for the address to be useful, since the
    card and Katana both differentiate billing from shipping.
    """

    model_config = ConfigDict(extra="forbid")

    entity_type: AddressEntityType = Field(
        ...,
        description="'billing' or 'shipping'. Drives both card layout and Katana's address routing.",
    )
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    company: str | None = Field(default=None)
    phone: str | None = Field(default=None)
    line_1: str | None = Field(default=None, description="Street address line 1")
    line_2: str | None = Field(default=None, description="Street address line 2")
    city: str | None = Field(default=None)
    state: str | None = Field(default=None, description="State / province / region")
    zip: str | None = Field(default=None, description="Postal code")
    country: str | None = Field(default=None)


class CreateCustomerRequest(BaseModel):
    """Request to create a new customer.

    Mirrors ``CreateCustomerRequest`` in ``docs/katana-openapi.yaml`` — ``name``
    is the only required field; everything else is optional. Use individual
    ``first_name`` / ``last_name`` for personal contacts; use ``company`` for
    business accounts (and typically populate ``name`` to mirror the company
    name).
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ...,
        description=(
            "Display name shown in the Katana UI and on documents. For an "
            "individual contact, use the person's full name; for a business "
            "account, mirror the company name."
        ),
    )
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    company: str | None = Field(default=None)
    email: str | None = Field(default=None)
    phone: str | None = Field(default=None)
    comment: str | None = Field(
        default=None,
        description="Internal notes about the customer (not shown to them).",
    )
    currency: str | None = Field(
        default=None,
        description="ISO 4217 currency code (e.g., USD, EUR, GBP).",
    )
    reference_id: str | None = Field(
        default=None,
        description="External reference (e.g., the customer's ID in another system).",
    )
    category: str | None = Field(
        default=None,
        description="Free-form category label for segmentation/reporting.",
    )
    discount_rate: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Default percentage discount on this customer's orders (0-100).",
    )
    addresses: list[CreateCustomerAddressRequest] = Field(
        default_factory=list,
        description=(
            "Billing and/or shipping addresses. Optional — addresses can be "
            "added or edited later via Katana's UI."
        ),
    )
    preview: bool = Field(
        default=True,
        description="If true (default), returns a preview. If false, creates the customer.",
    )


class CreateCustomerAddressSnapshot(BaseModel):
    """Address fields surfaced in the create-customer response card.

    Mirrors :class:`CreateCustomerAddressRequest`'s shape on the response
    side. ``id``/``default`` are populated on the apply branch when Katana
    returns them — useful for callers that want to identify the
    server-assigned default address on a multi-address create.
    """

    model_config = ConfigDict(extra="forbid")

    entity_type: AddressEntityType | None = None
    id: int | None = None
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


class CreateCustomerResponse(BaseModel):
    """Response from creating (or previewing the creation of) a customer.

    Field set is tuned for what the create card needs to render plus the
    identity / timestamp fields Katana returns on the apply branch.
    Server-generated fields (``id``, ``katana_url``, ``default_*_id``,
    timestamps) populate only on the apply branch.
    """

    id: int | None = None
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
    addresses: list[CreateCustomerAddressSnapshot] = Field(default_factory=list)
    is_preview: bool
    warnings: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    message: str


def _customer_response_to_tool_result(
    response: CreateCustomerResponse,
    *,
    request: CreateCustomerRequest,
) -> ToolResult:
    """Convert a ``CreateCustomerResponse`` to a ``ToolResult`` with a Prefab UI.

    The preview branch wires the direct-apply rail (Confirm fires
    ``tools/call`` directly and pushes the structured result back to the
    agent via ``ui/update-model-context``). Same shape as
    ``_po_response_to_tool_result`` in ``purchase_orders.py``.
    """
    from katana_mcp.tools.prefab_ui import build_customer_create_ui

    ui = build_customer_create_ui(
        response.model_dump(mode="json"),
        confirm_request=request,
        confirm_tool="create_customer",
    )
    return make_tool_result(response, ui=ui)


def _addresses_snapshot(
    addresses: list[CreateCustomerAddressRequest],
) -> list[CreateCustomerAddressSnapshot]:
    """Project request-side addresses onto the response-side snapshot.

    Used by the preview branch (no API call yet) and as the apply-branch
    fallback when the server doesn't echo addresses on the response.
    """
    return [CreateCustomerAddressSnapshot(**addr.model_dump()) for addr in addresses]


def _addresses_from_attrs(server_addresses: Any) -> list[CreateCustomerAddressSnapshot]:
    """Project the API ``Customer.addresses`` list (attrs) onto the snapshot.

    Used on the apply branch when the server echoes addresses on the
    response — preferred over :func:`_addresses_snapshot` because the
    server-side values reflect Katana's normalization (uppercased country
    codes, trimmed whitespace) and carry the server-assigned ``id`` /
    ``default`` flag the operator may want to reference next.

    The attrs ``CustomerAddress.entity_type`` is an enum
    (:class:`AddressEntityType`); ``.value`` extracts the wire string.
    The attrs ``zip_`` field maps to the wire / snapshot name ``zip``.
    """
    from katana_public_api_client.domain.converters import unwrap_unset

    snapshots: list[CreateCustomerAddressSnapshot] = []
    for addr in server_addresses:
        entity_type_attr = unwrap_unset(addr.entity_type, None)
        entity_type_value: AddressEntityType | None = None
        if entity_type_attr is not None:
            value = getattr(entity_type_attr, "value", entity_type_attr)
            if value in ("billing", "shipping"):
                entity_type_value = value
        snapshots.append(
            CreateCustomerAddressSnapshot(
                entity_type=entity_type_value,
                id=unwrap_unset(addr.id, None),
                default=unwrap_unset(addr.default, None),
                first_name=unwrap_unset(addr.first_name, None),
                last_name=unwrap_unset(addr.last_name, None),
                company=unwrap_unset(addr.company, None),
                phone=unwrap_unset(addr.phone, None),
                line_1=unwrap_unset(addr.line_1, None),
                line_2=unwrap_unset(addr.line_2, None),
                city=unwrap_unset(addr.city, None),
                state=unwrap_unset(addr.state, None),
                zip=unwrap_unset(addr.zip_, None),
                country=unwrap_unset(addr.country, None),
            )
        )
    return snapshots


async def _create_customer_impl(
    request: CreateCustomerRequest, context: Context
) -> CreateCustomerResponse:
    """Implementation of the ``create_customer`` tool.

    Preview branch: no API call — echoes the request fields into a
    response shape the card can render verbatim. Apply branch: POSTs to
    ``/customers``, unwraps the response into the typed ``Customer``
    attrs model, then merges the freshly-created row into the typed cache
    via :func:`merge_filtered_fetch` so a follow-up ``search_customers``
    call returns it without a ``rebuild_cache`` round-trip.
    """
    from katana_public_api_client.client_types import UNSET
    from katana_public_api_client.domain.converters import to_unset, unwrap_unset
    from katana_public_api_client.models import (
        AddressEntityType as APIAddressEntityType,
        CreateCustomerRequest as APICreateCustomerRequest,
        CreateCustomerRequestAddressesItem as APIAddressItem,
        Customer as APICustomer,
    )
    from katana_public_api_client.utils import unwrap_as

    # Validate before logging — a whitespace-only name shouldn't surface
    # as a noisy `Previewing customer '   '` line followed by the raise.
    if not request.name.strip():
        raise ValueError("Customer name cannot be empty")

    logger.info(
        "customer_create_started",
        preview=request.preview,
        name=request.name,
    )

    if request.preview:
        return CreateCustomerResponse(
            name=request.name,
            first_name=request.first_name,
            last_name=request.last_name,
            company=request.company,
            email=request.email,
            phone=request.phone,
            comment=request.comment,
            currency=request.currency,
            reference_id=request.reference_id,
            category=request.category,
            discount_rate=request.discount_rate,
            addresses=_addresses_snapshot(request.addresses),
            is_preview=True,
            warnings=[],
            next_actions=[
                "Review the customer details",
                "Set preview=false to create the customer",
            ],
            message=(
                f"Preview: customer {request.name} ready to create"
                + (
                    f" with {len(request.addresses)} address(es)"
                    if request.addresses
                    else ""
                )
            ),
        )

    services = get_services(context)

    # Build the API attrs request. ``to_unset`` maps ``None`` → ``UNSET`` for
    # every optional field so unset values don't ship as explicit nulls
    # (which Katana treats as "clear this field" on update, but on create
    # the server is forgiving; we still send the minimal payload for
    # parity with the rest of the codebase).
    address_items: list[APIAddressItem] | Any = UNSET
    if request.addresses:
        address_items = [
            APIAddressItem(
                entity_type=APIAddressEntityType(addr.entity_type),
                first_name=to_unset(addr.first_name),
                last_name=to_unset(addr.last_name),
                company=to_unset(addr.company),
                phone=to_unset(addr.phone),
                line_1=to_unset(addr.line_1),
                line_2=to_unset(addr.line_2),
                city=to_unset(addr.city),
                state=to_unset(addr.state),
                zip_=to_unset(addr.zip),
                country=to_unset(addr.country),
            )
            for addr in request.addresses
        ]

    api_request = APICreateCustomerRequest(
        name=request.name,
        first_name=to_unset(request.first_name),
        last_name=to_unset(request.last_name),
        company=to_unset(request.company),
        email=to_unset(request.email),
        phone=to_unset(request.phone),
        comment=to_unset(request.comment),
        currency=to_unset(request.currency),
        reference_id=to_unset(request.reference_id),
        category=to_unset(request.category),
        discount_rate=to_unset(request.discount_rate),
        addresses=address_items,
    )

    from katana_public_api_client.api.customer import (
        create_customer as api_create_customer,
    )

    response = await api_create_customer.asyncio_detailed(
        client=services.client, body=api_request
    )
    customer = unwrap_as(response, APICustomer)
    logger.info("customer_create_succeeded", customer_id=customer.id)

    # Prefer the API's echoed addresses (Katana's normalized values +
    # server-assigned ``id`` / ``default`` flag) over the request snapshot;
    # fall back to the request snapshot only when the field is UNSET
    # (``unwrap_unset`` → None). An echoed ``addresses: []`` is the
    # server's authoritative "no addresses persisted" — render it as
    # such, don't override with the request snapshot.
    server_addresses = unwrap_unset(customer.addresses, None)
    if server_addresses is not None:
        addresses_snapshot = _addresses_from_attrs(server_addresses)
    else:
        addresses_snapshot = _addresses_snapshot(request.addresses)

    warnings: list[str] = []
    # Write the freshly-created customer through to the typed cache so a
    # follow-up ``search_customers`` returns it without ``rebuild_cache``.
    # ``merge_filtered_fetch`` does not advance the sync watermark — exactly
    # right here: the next incremental sync will pull this same row plus
    # anything else that's changed.
    #
    # Cache-merge failure must NOT raise: the customer already exists in
    # Katana, so re-raising would push the operator into retrying and
    # creating a duplicate (Katana doesn't enforce name uniqueness).
    # Degrade to a warning; the next incremental sync recovers the row.
    from katana_mcp.typed_cache.sync import ENTITY_SPECS, merge_filtered_fetch

    try:
        await merge_filtered_fetch(
            services.typed_cache, ENTITY_SPECS["customer"], [customer]
        )
    except Exception as merge_err:
        logger.warning(
            "create_customer.cache_merge_failed",
            customer_id=customer.id,
            error=str(merge_err),
        )
        warnings.append(
            f"Customer created in Katana (ID {customer.id}), but the local cache "
            f"write-through failed ({merge_err}). The customer will appear in "
            "search_customers after the next incremental sync; do not retry the "
            "create call or you will create a duplicate."
        )

    return CreateCustomerResponse(
        id=customer.id,
        katana_url=katana_web_url("customer", customer.id),
        name=unwrap_unset(customer.name, request.name),
        first_name=unwrap_unset(customer.first_name, request.first_name),
        last_name=unwrap_unset(customer.last_name, request.last_name),
        company=unwrap_unset(customer.company, request.company),
        email=unwrap_unset(customer.email, request.email),
        phone=unwrap_unset(customer.phone, request.phone),
        comment=unwrap_unset(customer.comment, request.comment),
        currency=unwrap_unset(customer.currency, request.currency),
        reference_id=unwrap_unset(customer.reference_id, request.reference_id),
        category=unwrap_unset(customer.category, request.category),
        discount_rate=unwrap_unset(customer.discount_rate, request.discount_rate),
        default_billing_id=unwrap_unset(customer.default_billing_id, None),
        default_shipping_id=unwrap_unset(customer.default_shipping_id, None),
        created_at=_iso_or_none(unwrap_unset(customer.created_at, None)),
        updated_at=_iso_or_none(unwrap_unset(customer.updated_at, None)),
        addresses=addresses_snapshot,
        is_preview=False,
        warnings=warnings,
        next_actions=[
            f"Customer created with ID {customer.id}",
            "Use create_sales_order to draft an order for this customer",
        ],
        message=f"Successfully created customer {request.name} (ID: {customer.id})",
    )


@observe_tool
@unpack_pydantic_params
async def create_customer(
    request: Annotated[CreateCustomerRequest, Unpack()], context: Context
) -> ToolResult:
    """Create a new customer in Katana.

    Two-step flow: ``preview=true`` (default) returns a preview card showing
    the customer about to be created; ``preview=false`` actually creates it.
    Use for non-Shopify channels (eBay, Amazon, Etsy, direct-website) where
    buyers don't pre-exist in Katana — Shopify-synced workflows usually see
    the customer arrive on their own.

    Required: ``name`` (display name). Everything else is optional; pass
    ``addresses=[{entity_type: "billing", line_1: "...", ...}]`` to attach
    one or more billing / shipping addresses on the same call. ``currency``
    should be an ISO 4217 code (USD, EUR, GBP, etc.). On apply, the new
    record writes through to the typed cache so a follow-up
    ``search_customers`` returns it immediately.
    """
    response = await _create_customer_impl(request, context)
    return _customer_response_to_tool_result(response, request=request)


def register_tools(mcp: FastMCP) -> None:
    """Register all customer tools with the FastMCP instance."""
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

    mcp.tool(tags={"customers", "read"}, annotations=_read)(search_customers)
    mcp.tool(tags={"customers", "read"}, annotations=_read)(get_customer)
    register_preview_tool(
        mcp,
        create_customer,
        tags={"customers", "write"},
        annotations=_create,
        meta=UI_META,
    )


__all__ = ["register_tools"]
