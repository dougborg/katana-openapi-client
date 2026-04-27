"""Item management tools for Katana MCP Server.

Foundation tools for searching and managing items (variants, products, materials, services).
Items are things with SKUs - they appear in the "Items" tab of the Katana UI.
"""

from __future__ import annotations

import asyncio
from enum import StrEnum
from typing import Annotated, Any, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, Field

from katana_mcp.cache import EntityType
from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.decorators import cache_read
from katana_mcp.tools.tool_result_utils import (
    UI_META,
    format_md_table,
    make_simple_result,
    make_tool_result,
)
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.domain.converters import to_unset
from katana_public_api_client.models import (
    CreateMaterialRequest,
    CreateProductRequest,
    CreateServiceRequest,
    CreateServiceVariantRequest,
    CreateVariantRequest,
)

logger = get_logger(__name__)


def _get_type_helper(client: Any, item_type: ItemType) -> Any:
    """Get the client helper for an item type (products, materials, or services)."""
    helpers = {
        ItemType.PRODUCT: "products",
        ItemType.MATERIAL: "materials",
        ItemType.SERVICE: "services",
    }
    attr = helpers.get(item_type)
    if not attr:
        raise ValueError(f"Invalid item type: {item_type}")
    return getattr(client, attr)


# ============================================================================
# Shared Models
# ============================================================================


class ItemType(StrEnum):
    """Type of item - matches Katana API discriminator."""

    PRODUCT = "product"
    MATERIAL = "material"
    SERVICE = "service"


# ============================================================================
# Tool 1: search_items
# ============================================================================


class SearchItemsRequest(BaseModel):
    """Request model for searching items."""

    query: str = Field(..., description="Search query (name, SKU, etc.)")
    limit: int = Field(default=20, description="Maximum results to return")
    format: Literal["markdown", "json"] = Field(
        default="markdown",
        description=(
            "Output format: 'markdown' (default) for human-readable tables; "
            "'json' for structured data consumable by downstream tools/aggregations."
        ),
    )


class ItemInfo(BaseModel):
    """Item information."""

    id: int
    sku: str
    name: str
    item_type: str = "unknown"
    is_sellable: bool
    stock_level: int | None = None


class SearchItemsResponse(BaseModel):
    """Response containing search results."""

    items: list[ItemInfo]
    total_count: int


def _search_response_to_tool_result(
    response: SearchItemsResponse, query: str
) -> ToolResult:
    """Convert SearchItemsResponse to ToolResult with markdown + Prefab UI."""
    from katana_mcp.tools.prefab_ui import build_search_results_ui

    # Build items table for template
    if response.items:
        items_table = "\n".join(
            f"- **{item.sku}**: {item.name} (ID: {item.id}, Sellable: {item.is_sellable})"
            for item in response.items
        )
    else:
        items_table = "No items found matching your query."

    product_count = sum(1 for item in response.items if item.item_type == "product")
    material_count = sum(1 for item in response.items if item.item_type == "material")
    service_count = sum(1 for item in response.items if item.item_type == "service")

    # Filter out items without SKU — drill-down requires SKU for get_variant_details
    items_dicts = [item.model_dump() for item in response.items if item.sku]
    ui = build_search_results_ui(items_dicts, query, response.total_count)

    return make_tool_result(
        response,
        "item_search_results",
        ui=ui,
        query=query,
        result_count=response.total_count,
        items_table=items_table,
        product_count=product_count,
        material_count=material_count,
        service_count=service_count,
    )


@cache_read(EntityType.VARIANT)
async def _search_items_impl(
    request: SearchItemsRequest, context: Context
) -> SearchItemsResponse:
    """Search variants via cached FTS5 + fuzzy fallback."""
    if not request.query or not request.query.strip():
        raise ValueError("Search query cannot be empty")
    if request.limit <= 0:
        raise ValueError("Limit must be positive")

    services = get_services(context)
    variant_dicts = await services.cache.smart_search(
        "variant", request.query, limit=request.limit
    )

    items_info = [
        ItemInfo(
            id=v["id"],
            sku=v.get("sku") or "",
            name=v.get("display_name") or v.get("sku") or "",
            item_type=v.get("type") or "unknown",
            is_sellable=v.get("type") == "product",
            stock_level=None,
        )
        for v in variant_dicts
    ]

    return SearchItemsResponse(items=items_info, total_count=len(items_info))


@observe_tool
@unpack_pydantic_params
async def search_items(
    request: Annotated[SearchItemsRequest, Unpack()], context: Context
) -> ToolResult:
    """Search for items (products, materials, services) by name or SKU — returns multiple matching items.

    Use this as the starting point when you need to find items. Returns item IDs
    and SKUs needed by other tools like create_purchase_order or check_inventory.
    For full details on a specific item, follow up with get_variant_details.

    Query must not be empty. Default limit is 20 results.
    """
    response = await _search_items_impl(request, context)
    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2),
            structured_content=response.model_dump(),
        )
    return _search_response_to_tool_result(response, request.query)


# ============================================================================
# Tool 2: create_item
# ============================================================================


class CreateItemRequest(BaseModel):
    """Create a new item (product, material, or service).

    This is a simplified interface for creating items with a single variant.
    For complex items with multiple variants and configurations, use the
    native API models directly.
    """

    type: ItemType = Field(..., description="Type of item to create")
    name: str = Field(..., description="Item name")
    sku: str = Field(..., description="SKU for the item variant")
    uom: str = Field(
        default="pcs", description="Unit of measure (e.g., pcs, kg, hours)"
    )
    category_name: str | None = Field(None, description="Category for grouping")
    is_sellable: bool = Field(True, description="Whether item can be sold")
    sales_price: float | None = Field(None, description="Sales price per unit")
    purchase_price: float | None = Field(None, description="Purchase cost per unit")

    # Product-specific
    is_producible: bool = Field(
        False, description="Can be manufactured (products only)"
    )
    is_purchasable: bool = Field(
        True, description="Can be purchased (products/materials)"
    )

    # Optional common fields
    default_supplier_id: int | None = Field(None, description="Default supplier ID")
    additional_info: str | None = Field(None, description="Additional notes")


class CreateItemResponse(BaseModel):
    """Response from creating an item."""

    id: int
    name: str
    type: ItemType
    variant_id: int | None = None
    sku: str | None = None
    success: bool = True
    message: str = "Item created successfully"


async def _create_item_impl(
    request: CreateItemRequest, context: Context
) -> CreateItemResponse:
    """Create a product, material, or service with a variant."""
    services = get_services(context)
    cache = getattr(services, "cache", None)

    # Build variant (services use a different variant model)
    if request.type == ItemType.SERVICE:
        service_variant = CreateServiceVariantRequest(
            sku=request.sku,
            sales_price=to_unset(request.sales_price),
            default_cost=to_unset(request.purchase_price),
        )
        api_request = CreateServiceRequest(
            name=request.name,
            uom=request.uom,
            category_name=to_unset(request.category_name),
            is_sellable=request.is_sellable,
            variants=[service_variant],
        )
        result = await services.client.services.create(api_request)
    else:
        variant = CreateVariantRequest(
            sku=request.sku,
            sales_price=to_unset(request.sales_price),
            purchase_price=to_unset(request.purchase_price),
        )
        if request.type == ItemType.PRODUCT:
            api_request = CreateProductRequest(
                name=request.name,
                uom=request.uom,
                category_name=to_unset(request.category_name),
                is_sellable=request.is_sellable,
                is_producible=request.is_producible,
                is_purchasable=request.is_purchasable,
                default_supplier_id=to_unset(request.default_supplier_id),
                additional_info=to_unset(request.additional_info),
                variants=[variant],
            )
            result = await services.client.products.create(api_request)
        elif request.type == ItemType.MATERIAL:
            api_request = CreateMaterialRequest(
                name=request.name,
                uom=request.uom,
                category_name=to_unset(request.category_name),
                is_sellable=request.is_sellable,
                default_supplier_id=to_unset(request.default_supplier_id),
                additional_info=to_unset(request.additional_info),
                variants=[variant],
            )
            result = await services.client.materials.create(api_request)
        else:
            raise ValueError(f"Invalid item type: {request.type}")

    # Invalidate only the affected type + variants
    if cache:
        await cache.mark_dirty(request.type.value)
        await cache.mark_dirty(EntityType.VARIANT)

    return CreateItemResponse(
        id=result.id,
        name=result.name or "",
        type=request.type,
        sku=request.sku,
        message=f"{request.type.value.title()} '{result.name}' created successfully with SKU {request.sku}",
    )


@observe_tool
@unpack_pydantic_params
async def create_item(
    request: Annotated[CreateItemRequest, Unpack()], context: Context
) -> ToolResult:
    """Create any item type (product, material, or service) in the Katana catalog.

    General-purpose item creation. PREFER create_product for finished goods or
    create_material for raw materials — those tools have simpler, dedicated parameters.
    Use this tool only for services or when the item type is determined dynamically.

    Creates the item with a single variant. Returns the new item ID.
    """
    from katana_mcp.tools.prefab_ui import build_item_mutation_ui

    response = await _create_item_impl(request, context)
    ui = build_item_mutation_ui(response.model_dump(), "Created")

    return make_tool_result(
        response,
        "item_created",
        ui=ui,
        id=response.id,
        name=response.name,
        item_type=response.type,
        sku=response.sku or "",
        message=response.message,
    )


# ============================================================================
# Tool 3: get_item
# ============================================================================


class GetItemRequest(BaseModel):
    """Request to get an item by ID."""

    id: int = Field(..., description="Item ID")
    type: ItemType = Field(..., description="Type of item (product, material, service)")
    format: Literal["markdown", "json"] = Field(
        default="markdown",
        description=(
            "Output format: 'markdown' (default) for human-readable tables; "
            "'json' for structured data consumable by downstream tools/aggregations."
        ),
    )


class ItemSupplierInfo(BaseModel):
    """Supplier record embedded on a product or material."""

    id: int
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    currency: str | None = None
    comment: str | None = None
    default_address_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ItemConfigInfo(BaseModel):
    """Configuration attribute definition (e.g. Size / Color)."""

    id: int
    name: str
    values: list[str] = Field(default_factory=list)
    product_id: int | None = None
    material_id: int | None = None


class ItemVariantSummary(BaseModel):
    """Brief variant summary embedded in the product/material/service detail."""

    id: int
    sku: str
    sales_price: float | None = None
    purchase_price: float | None = None
    type: str | None = None


class ItemDetailsResponse(BaseModel):
    """Full item details. Exhaustive — every field Katana exposes on
    ``Product`` / ``Material`` / ``Service`` is surfaced per-type (the API is
    polymorphic, so not every field applies to every type; product-only and
    service-only fields stay ``None`` for the other types).

    Nested ``variants``, ``configs``, and ``supplier`` are surfaced in summary
    form so a single call can answer most catalog questions without
    drill-downs. For full per-variant detail (barcodes, supplier codes,
    custom fields), follow up with ``get_variant_details``.
    """

    # Core — present on all three types
    id: int
    name: str
    type: ItemType
    uom: str | None = None
    category_name: str | None = None
    is_sellable: bool | None = None
    additional_info: str | None = None
    custom_field_collection_id: int | None = None

    # Timestamps — present on all three
    created_at: str | None = None
    updated_at: str | None = None
    archived_at: str | None = None
    deleted_at: str | None = None

    # Product / Material only
    default_supplier_id: int | None = None
    batch_tracked: bool | None = None
    purchase_uom: str | None = None
    purchase_uom_conversion_rate: float | None = None
    serial_tracked: bool | None = None
    operations_in_sequence: bool | None = None

    # Product only
    is_producible: bool | None = None
    is_purchasable: bool | None = None
    is_auto_assembly: bool | None = None
    lead_time: int | None = None
    minimum_order_quantity: float | None = None

    # Nested collections (Product/Material carry configs + supplier;
    # all three carry variants)
    variants: list[ItemVariantSummary] = Field(default_factory=list)
    configs: list[ItemConfigInfo] = Field(default_factory=list)
    supplier: ItemSupplierInfo | None = None


def _supplier_to_info(raw: Any) -> ItemSupplierInfo | None:
    """Convert an attrs Supplier (or dict) to ItemSupplierInfo."""
    if raw is None:
        return None
    d = raw.to_dict() if hasattr(raw, "to_dict") else raw
    if not isinstance(d, dict) or "id" not in d:
        return None
    return ItemSupplierInfo(
        id=d["id"],
        name=d.get("name"),
        email=d.get("email"),
        phone=d.get("phone"),
        currency=d.get("currency"),
        comment=d.get("comment"),
        default_address_id=d.get("default_address_id"),
        created_at=_iso_or_none(d.get("created_at")),
        updated_at=_iso_or_none(d.get("updated_at")),
    )


def _config_to_info(raw: Any) -> ItemConfigInfo | None:
    """Convert an attrs ItemConfig (or dict) to ItemConfigInfo."""
    d = raw.to_dict() if hasattr(raw, "to_dict") else raw
    if not isinstance(d, dict) or "id" not in d:
        return None
    return ItemConfigInfo(
        id=d["id"],
        name=d.get("name") or "",
        values=list(d.get("values") or []),
        product_id=d.get("product_id"),
        material_id=d.get("material_id"),
    )


def _variant_to_summary(raw: Any) -> ItemVariantSummary | None:
    """Convert a nested Variant/ServiceVariant attrs (or dict) to summary."""
    d = raw.to_dict() if hasattr(raw, "to_dict") else raw
    if not isinstance(d, dict) or "id" not in d or "sku" not in d:
        return None
    return ItemVariantSummary(
        id=d["id"],
        sku=d["sku"],
        sales_price=d.get("sales_price"),
        # ServiceVariant uses default_cost; Variant uses purchase_price.
        # Explicit None-check — `or` would shadow a legitimate 0.0 price
        # (free samples, gift items) with default_cost.
        purchase_price=(
            d["purchase_price"]
            if d.get("purchase_price") is not None
            else d.get("default_cost")
        ),
        type=d.get("type") or d.get("type_"),
    )


def _item_attrs_to_dict(item: Any) -> dict[str, Any]:
    """Call ``to_dict()`` on a Product/Material/Service attrs model.

    Wraps the call so callers can rely on a plain-dict view across all three
    types without branching on instance type.
    """
    if hasattr(item, "to_dict"):
        return item.to_dict()
    return dict(item) if isinstance(item, dict) else {}


async def _fetch_item_attrs(services: Any, item_id: int, item_type: ItemType) -> Any:
    """Fetch a Product/Material/Service attrs model with supplier extension.

    Uses the raw API directly so every field on the generated model is
    surfaced. The domain helpers (``client.products.get``, etc.) return
    ``KatanaProduct`` / ``KatanaMaterial`` — curated Pydantic models that
    drop nested ``variants``, ``configs``, ``supplier``. For the exhaustive
    detail tool we need the full attrs shape.
    """
    from katana_public_api_client.api.material import get_material
    from katana_public_api_client.api.product import get_product
    from katana_public_api_client.api.services import get_service
    from katana_public_api_client.models.get_material_extend_item import (
        GetMaterialExtendItem,
    )
    from katana_public_api_client.models.get_product_extend_item import (
        GetProductExtendItem,
    )
    from katana_public_api_client.utils import unwrap

    if item_type == ItemType.PRODUCT:
        response = await get_product.asyncio_detailed(
            client=services.client,
            id=item_id,
            extend=[GetProductExtendItem.SUPPLIER],
        )
    elif item_type == ItemType.MATERIAL:
        response = await get_material.asyncio_detailed(
            client=services.client,
            id=item_id,
            extend=[GetMaterialExtendItem.SUPPLIER],
        )
    else:
        response = await get_service.asyncio_detailed(
            client=services.client, id=item_id
        )
    return unwrap(response)


async def _get_item_impl(
    request: GetItemRequest, context: Context
) -> ItemDetailsResponse:
    """Get exhaustive item details by ID and type."""
    services = get_services(context)
    item = await _fetch_item_attrs(services, request.id, request.type)
    d = _item_attrs_to_dict(item)

    variants = [
        v for v in (_variant_to_summary(raw) for raw in d.get("variants") or []) if v
    ]
    configs = [c for c in (_config_to_info(raw) for raw in d.get("configs") or []) if c]
    supplier = _supplier_to_info(d.get("supplier"))

    return ItemDetailsResponse(
        id=d.get("id", request.id),
        name=d.get("name") or "",
        type=request.type,
        uom=d.get("uom"),
        category_name=d.get("category_name"),
        is_sellable=d.get("is_sellable"),
        additional_info=d.get("additional_info"),
        custom_field_collection_id=d.get("custom_field_collection_id"),
        created_at=_iso_or_none(d.get("created_at")),
        updated_at=_iso_or_none(d.get("updated_at")),
        archived_at=_iso_or_none(d.get("archived_at")),
        deleted_at=_iso_or_none(d.get("deleted_at")),
        # Product / Material only (remain None on Service)
        default_supplier_id=d.get("default_supplier_id"),
        batch_tracked=d.get("batch_tracked"),
        purchase_uom=d.get("purchase_uom"),
        purchase_uom_conversion_rate=d.get("purchase_uom_conversion_rate"),
        serial_tracked=d.get("serial_tracked"),
        operations_in_sequence=d.get("operations_in_sequence"),
        # Product only
        is_producible=d.get("is_producible"),
        is_purchasable=d.get("is_purchasable"),
        is_auto_assembly=d.get("is_auto_assembly"),
        lead_time=d.get("lead_time"),
        minimum_order_quantity=d.get("minimum_order_quantity"),
        # Nested collections
        variants=variants,
        configs=configs,
        supplier=supplier,
    )


def _render_variant_summary_md(v: ItemVariantSummary) -> str:
    """Render a variant summary as a compact multi-line block.

    Uses canonical field names so an LLM consuming the markdown can't mistake
    a rendered value for a differently-labeled field (#346 follow-on).
    """
    lines = [f"  - **id**: {v.id}", f"    **sku**: {v.sku}"]
    for fname in ("type", "sales_price", "purchase_price"):
        val = getattr(v, fname)
        if val is not None and val != "":
            lines.append(f"    **{fname}**: {val}")
    return "\n".join(lines)


def _render_config_md(c: ItemConfigInfo) -> str:
    """Render an ItemConfig as a compact multi-line block."""
    values = ", ".join(c.values) if c.values else ""
    # Always emit `values` with explicit brackets; empty list renders as `[]`
    # rather than being omitted, so an LLM consumer can't confuse "absent"
    # with "empty" (#346 follow-on convention).
    return "\n".join(
        [
            f"  - **id**: {c.id}",
            f"    **name**: {c.name}",
            f"    **values**: [{values}]",
        ]
    )


def _render_supplier_md(s: ItemSupplierInfo) -> str:
    """Render an ItemSupplierInfo as a compact multi-line block."""
    lines = [f"  - **id**: {s.id}"]
    for fname in (
        "name",
        "email",
        "phone",
        "currency",
        "comment",
        "default_address_id",
    ):
        val = getattr(s, fname)
        if val is not None and val != "":
            lines.append(f"    **{fname}**: {val}")
    return "\n".join(lines)


def _item_details_to_tool_result(response: ItemDetailsResponse) -> ToolResult:
    """Convert ItemDetailsResponse to ToolResult with canonical-name markdown.

    Labels use the canonical Pydantic field names. Fields that don't apply
    to the item's type (e.g. ``is_producible`` on a Service) are skipped
    when ``None`` so the markdown stays compact. The Prefab UI is passed
    through unchanged.
    """
    from katana_mcp.tools.prefab_ui import build_item_detail_ui

    name_line = (
        f"## {response.name}" if response.name else f"## {response.type} {response.id}"
    )
    md_lines = [name_line]

    scalar_fields = (
        "id",
        "type",
        "uom",
        "category_name",
        "is_sellable",
        "is_producible",
        "is_purchasable",
        "is_auto_assembly",
        "batch_tracked",
        "serial_tracked",
        "operations_in_sequence",
        "default_supplier_id",
        "purchase_uom",
        "purchase_uom_conversion_rate",
        "lead_time",
        "minimum_order_quantity",
        "additional_info",
        "custom_field_collection_id",
        "created_at",
        "updated_at",
        "archived_at",
        "deleted_at",
    )
    for fname in scalar_fields:
        val = getattr(response, fname)
        if val is None or val == "":
            continue
        md_lines.append(f"**{fname}**: {val}")

    # Nested collections — always render with explicit list shape so the
    # caller can see the field even when empty. (#346 follow-on.)
    if response.variants:
        md_lines.append(f"**variants** ({len(response.variants)}):")
        for v in response.variants:
            md_lines.append(_render_variant_summary_md(v))
    else:
        md_lines.append("**variants**: []")

    if response.configs:
        md_lines.append(f"**configs** ({len(response.configs)}):")
        for c in response.configs:
            md_lines.append(_render_config_md(c))
    else:
        md_lines.append("**configs**: []")

    if response.supplier is not None:
        md_lines.append("**supplier**:")
        md_lines.append(_render_supplier_md(response.supplier))
    else:
        md_lines.append("**supplier**: None")

    ui = build_item_detail_ui(response.model_dump())

    return ToolResult(
        content="\n".join(md_lines),
        structured_content=ui,
    )


@observe_tool
@unpack_pydantic_params
async def get_item(
    request: Annotated[GetItemRequest, Unpack()], context: Context
) -> ToolResult:
    """Get exhaustive item details by ID and type (product, material, or service).

    Returns every field Katana exposes on the item record, plus nested
    ``variants`` (summary), ``configs``, and ``supplier``. The API is
    polymorphic: Product / Material / Service each have their own field
    set, and type-specific fields (``is_producible`` on products, etc.)
    stay ``None`` for the other types.

    Use after search_items. For variant-level detail (barcodes, supplier
    codes, custom fields), follow up with ``get_variant_details``.
    """
    response = await _get_item_impl(request, context)

    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2),
            structured_content=response.model_dump(),
        )

    return _item_details_to_tool_result(response)


# ============================================================================
# Tool 4: update_item
# ============================================================================


class UpdateItemRequest(BaseModel):
    """Request to update an item."""

    id: int = Field(..., description="Item ID")
    type: ItemType = Field(..., description="Type of item")
    name: str | None = Field(None, description="New item name")
    uom: str | None = Field(None, description="New unit of measure")
    category_name: str | None = Field(None, description="New category")
    is_sellable: bool | None = Field(None, description="Whether item can be sold")
    is_producible: bool | None = Field(
        None, description="Can be manufactured (products only)"
    )
    is_purchasable: bool | None = Field(None, description="Can be purchased")
    default_supplier_id: int | None = Field(None, description="Default supplier ID")
    additional_info: str | None = Field(None, description="Additional notes")
    # Variant-level fields — resolved automatically via SKU or first variant
    sku: str | None = Field(
        None,
        description="SKU to identify which variant to update (uses first variant if omitted)",
    )
    supplier_item_codes: list[str] | None = Field(
        None, description="Supplier item codes (replaces all existing codes)"
    )
    registered_barcode: str | None = Field(None, description="UPC / registered barcode")
    internal_barcode: str | None = Field(None, description="Internal barcode")
    sales_price: float | None = Field(None, description="Sales price")
    purchase_price: float | None = Field(None, description="Purchase price")
    lead_time: int | None = Field(None, description="Lead time in days")

    @property
    def has_variant_fields(self) -> bool:
        """Check if any variant-level fields are set."""
        return any(
            v is not None
            for v in [
                self.supplier_item_codes,
                self.registered_barcode,
                self.internal_barcode,
                self.sales_price,
                self.purchase_price,
                self.lead_time,
            ]
        )


class UpdateItemResponse(BaseModel):
    """Response from updating an item."""

    id: int
    name: str
    type: ItemType
    success: bool = True
    message: str = "Item updated successfully"


async def _update_item_impl(
    request: UpdateItemRequest, context: Context
) -> UpdateItemResponse:
    """Update an item's properties."""
    from katana_public_api_client.models import (
        UpdateMaterialRequest,
        UpdateProductRequest,
        UpdateServiceRequest,
    )

    services = get_services(context)
    helper = _get_type_helper(services.client, request.type)

    # Build type-specific update request (each type has different fields)
    common = {
        "name": to_unset(request.name),
        "uom": to_unset(request.uom),
        "category_name": to_unset(request.category_name),
        "is_sellable": to_unset(request.is_sellable),
    }

    if request.type == ItemType.PRODUCT:
        update_data = UpdateProductRequest(
            **common,
            is_producible=to_unset(request.is_producible),
            is_purchasable=to_unset(request.is_purchasable),
            default_supplier_id=to_unset(request.default_supplier_id),
            additional_info=to_unset(request.additional_info),
        )
    elif request.type == ItemType.MATERIAL:
        update_data = UpdateMaterialRequest(
            **common,
            default_supplier_id=to_unset(request.default_supplier_id),
            additional_info=to_unset(request.additional_info),
        )
    else:
        update_data = UpdateServiceRequest(**common)

    # Check if any item-level fields are set
    has_item_fields = any(
        v is not None
        for v in [
            request.name,
            request.uom,
            request.category_name,
            request.is_sellable,
            request.is_producible,
            request.is_purchasable,
            request.default_supplier_id,
            request.additional_info,
        ]
    )

    item_name = ""
    if has_item_fields:
        result = await helper.update(request.id, update_data)
        item_name = result.name or ""

    # Update variant-level fields if any are provided
    if request.has_variant_fields:
        from katana_public_api_client.api.variant import update_variant
        from katana_public_api_client.models.update_variant_request import (
            UpdateVariantRequest,
        )
        from katana_public_api_client.utils import unwrap

        # Variant-level fields require SKU to identify which variant to update.
        # request.id is the parent item ID, not a variant ID.
        if not request.sku:
            raise ValueError(
                "Variant-level updates (barcodes, supplier codes, prices) "
                "require 'sku' to identify the variant."
            )
        variant = await services.cache.get_by_sku(sku=request.sku)
        if not variant:
            raise ValueError(f"SKU '{request.sku}' not found")
        variant_id = variant["id"]

        variant_update = UpdateVariantRequest(
            supplier_item_codes=to_unset(request.supplier_item_codes),
            registered_barcode=to_unset(request.registered_barcode),
            internal_barcode=to_unset(request.internal_barcode),
            sales_price=to_unset(request.sales_price),
            purchase_price=to_unset(request.purchase_price),
            lead_time=to_unset(request.lead_time),
        )

        resp = await update_variant.asyncio_detailed(
            id=variant_id, client=services.client, body=variant_update
        )
        variant_result = unwrap(resp)
        if not item_name and variant_result:
            item_name = getattr(variant_result, "sku", "") or ""

    # Invalidate only the affected type + variants
    cache = getattr(services, "cache", None)
    if cache:
        await cache.mark_dirty(request.type.value)
        await cache.mark_dirty(EntityType.VARIANT)

    return UpdateItemResponse(
        id=request.id,
        name=item_name or "Unknown",
        type=request.type,
        message=f"{request.type.value.title()} (ID {request.id}) updated successfully",
    )


@observe_tool
@unpack_pydantic_params
async def update_item(
    request: Annotated[UpdateItemRequest, Unpack()], context: Context
) -> ToolResult:
    """Update an existing item's properties (product, material, or service).

    Only provided fields are updated; omitted fields remain unchanged.
    Requires the item ID and type. Use search_items first if you need to find the item.
    """
    from katana_mcp.tools.prefab_ui import build_item_mutation_ui

    response = await _update_item_impl(request, context)
    ui = build_item_mutation_ui(response.model_dump(), "Updated")

    return make_tool_result(
        response,
        "item_updated",
        ui=ui,
        id=response.id,
        name=response.name,
        item_type=response.type,
        message=response.message,
    )


# ============================================================================
# Tool 5: delete_item
# ============================================================================


class DeleteItemRequest(BaseModel):
    """Request to delete an item."""

    id: int = Field(..., description="Item ID")
    type: ItemType = Field(..., description="Type of item")
    confirm: bool = Field(
        False, description="If false, returns preview. If true, deletes item."
    )


class DeleteItemResponse(BaseModel):
    """Response from deleting an item."""

    id: int
    type: ItemType
    name: str | None = None
    is_preview: bool = False
    success: bool = True
    message: str = "Item deleted successfully"


async def _delete_item_impl(
    request: DeleteItemRequest, context: Context
) -> DeleteItemResponse:
    """Delete an item with two-step confirmation."""
    from katana_mcp.tools.schemas import ConfirmationResult, require_confirmation

    services = get_services(context)
    helper = _get_type_helper(services.client, request.type)

    # Fetch item name for preview/confirmation message
    item_name = f"{request.type.value} ID {request.id}"
    try:
        item = await helper.get(request.id)
        item_name = f"{request.type.value} '{item.name}' (ID {request.id})"
    except Exception:
        pass  # Use default name if fetch fails

    # Preview mode
    if not request.confirm:
        return DeleteItemResponse(
            id=request.id,
            type=request.type,
            is_preview=True,
            message=f"Preview: Would permanently delete {item_name}. Set confirm=true to proceed.",
        )

    # Confirm mode
    confirmation = await require_confirmation(
        context,
        f"Permanently delete {item_name}? This cannot be undone.",
    )

    if confirmation != ConfirmationResult.CONFIRMED:
        return DeleteItemResponse(
            id=request.id,
            type=request.type,
            is_preview=True,
            success=False,
            message=f"Deletion of {item_name} {confirmation} by user",
        )

    # Execute deletion
    await helper.delete(request.id)

    # Invalidate only the affected type + variants
    cache = getattr(services, "cache", None)
    if cache:
        await cache.mark_dirty(request.type.value)
        await cache.mark_dirty(EntityType.VARIANT)

    return DeleteItemResponse(
        id=request.id,
        type=request.type,
        message=f"{request.type.value.title()} ID {request.id} deleted successfully",
    )


@observe_tool
@unpack_pydantic_params
async def delete_item(
    request: Annotated[DeleteItemRequest, Unpack()], context: Context
) -> ToolResult:
    """Permanently delete an item (product, material, or service) from Katana.

    This is a destructive operation. Set confirm=false to preview what would be
    deleted, or confirm=true to execute (will prompt for confirmation).
    Requires the item ID and type.
    """
    from katana_mcp.tools.prefab_ui import build_item_mutation_ui

    response = await _delete_item_impl(request, context)
    ui = build_item_mutation_ui(response.model_dump(), "Deleted")

    return make_tool_result(
        response,
        "item_deleted",
        ui=ui,
        id=response.id,
        item_type=response.type,
        message=response.message,
    )


# ============================================================================
# Tool 6: get_variant_details
# ============================================================================


class GetVariantDetailsRequest(BaseModel):
    """Request to get variant details by SKU(s) or variant ID(s).

    Accepts a single sku/variant_id OR a list (skus/variant_ids) for batch lookups.
    """

    sku: str | None = Field(
        default=None,
        description="Single SKU to look up (exact case-insensitive match)",
    )
    variant_id: int | None = Field(
        default=None,
        description="Single variant ID to look up directly",
    )
    skus: list[str] | None = Field(
        default=None, description="Batch: list of SKUs to look up"
    )
    variant_ids: list[int] | None = Field(
        default=None, description="Batch: list of variant IDs to look up"
    )
    format: Literal["markdown", "json"] = Field(
        default="markdown",
        description=(
            "Output format: 'markdown' (default) for human-readable tables; "
            "'json' for structured data consumable by downstream tools/aggregations."
        ),
    )


class VariantDetailsResponse(BaseModel):
    """Full variant details. Exhaustive — every field Katana exposes on the
    ``Variant`` attrs model is surfaced, including nested configuration
    attributes and custom fields, so callers don't need follow-up lookups.
    """

    # Core fields
    id: int
    sku: str
    name: str

    # Pricing
    sales_price: float | None = None
    purchase_price: float | None = None

    # Classification
    type: str | None = None
    product_id: int | None = None
    material_id: int | None = None
    product_or_material_name: str | None = None

    # Barcode & Inventory
    internal_barcode: str | None = None
    registered_barcode: str | None = None
    supplier_item_codes: list[str] = Field(default_factory=list)

    # Ordering
    lead_time: int | None = None
    minimum_order_quantity: float | None = None

    # Configuration & Custom Fields
    config_attributes: list[dict[str, str]] = Field(default_factory=list)
    custom_fields: list[dict[str, str]] = Field(default_factory=list)

    # Metadata
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None


def _render_list_field_md(field_name: str, items: list[Any]) -> list[str]:
    """Render a list-shaped field with canonical label and explicit list syntax.

    Empty lists render as ``**field_name**: []`` so an LLM consumer can't
    mistake a section header for a value (#346 follow-on — supplier_item_codes
    misread as a supplier ID). Non-empty scalar lists render as
    ``**field_name**: [a, b, c]`` to keep the list shape visible.
    """
    if not items:
        return [f"**{field_name}**: []"]
    # Scalars (strings, numbers) render inline with bracket syntax.
    if all(isinstance(it, str | int | float) for it in items):
        rendered = ", ".join(str(it) for it in items)
        return [f"**{field_name}**: [{rendered}]"]
    # Dict-shaped lists (config_attributes, custom_fields) render as a
    # labeled block with per-item bullets.
    lines = [f"**{field_name}** ({len(items)}):"]
    for item in items:
        if isinstance(item, dict):
            pairs = ", ".join(
                f"{k}={v}" for k, v in item.items() if v not in (None, "")
            )
            lines.append(f"  - {pairs}" if pairs else "  - (empty)")
        else:
            lines.append(f"  - {item}")
    return lines


def _variant_details_to_tool_result(response: VariantDetailsResponse) -> ToolResult:
    """Convert VariantDetailsResponse to ToolResult with canonical-name markdown.

    Markdown labels use the Pydantic field names (``**supplier_item_codes**:
    [10654627]`` rather than a ``Supplier Info`` header with bare bullets)
    so LLM consumers can't confuse the section label with the field name.
    Motivation: #346 follow-on — the previous ``Supplier Info`` heading
    caused an LLM to misread a supplier_item_code as a supplier ID.

    The Prefab UI (for MCP-Apps clients) is passed through unchanged;
    scope boundary from #346 keeps Prefab builders untouched.
    """
    from katana_mcp.tools.prefab_ui import build_variant_details_ui

    name_line = f"## {response.name}" if response.name else f"## variant {response.id}"
    md_lines = [name_line]

    # Scalar fields render as ``**canonical_name**: value`` — skip None/empty
    # so the markdown stays compact but every populated field surfaces.
    scalar_fields = (
        "id",
        "sku",
        "type",
        "product_id",
        "material_id",
        "product_or_material_name",
        "sales_price",
        "purchase_price",
        "internal_barcode",
        "registered_barcode",
        "lead_time",
        "minimum_order_quantity",
        "created_at",
        "updated_at",
        "deleted_at",
    )
    for fname in scalar_fields:
        val = getattr(response, fname)
        if val is None or val == "":
            continue
        md_lines.append(f"**{fname}**: {val}")

    # List-shaped fields always render — empty prints as ``[]`` so the field
    # is visible in its true shape.
    md_lines.extend(
        _render_list_field_md("supplier_item_codes", response.supplier_item_codes)
    )
    md_lines.extend(
        _render_list_field_md("config_attributes", response.config_attributes)
    )
    md_lines.extend(_render_list_field_md("custom_fields", response.custom_fields))

    ui = build_variant_details_ui(response.model_dump())

    return ToolResult(
        content="\n".join(md_lines),
        structured_content=ui,
    )


def _iso_or_none(value: Any) -> str | None:
    """Return an ISO-8601 string for a datetime-or-str value, else None."""
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _dict_to_variant_details(v: dict[str, Any]) -> VariantDetailsResponse:
    """Build a VariantDetailsResponse from a cache/API variant dict.

    Surfaces every field the generated ``Variant`` attrs model exposes, so
    callers get the full shape in a single call.
    """
    return VariantDetailsResponse(
        id=v["id"],
        sku=v.get("sku") or "",
        name=v.get("display_name") or v.get("sku") or "",
        sales_price=v.get("sales_price"),
        purchase_price=v.get("purchase_price"),
        type=v.get("type") or v.get("type_"),
        product_id=v.get("product_id"),
        material_id=v.get("material_id"),
        product_or_material_name=v.get("parent_name"),
        internal_barcode=v.get("internal_barcode"),
        registered_barcode=v.get("registered_barcode"),
        supplier_item_codes=v.get("supplier_item_codes") or [],
        lead_time=v.get("lead_time"),
        minimum_order_quantity=v.get("minimum_order_quantity"),
        config_attributes=v.get("config_attributes") or [],
        custom_fields=v.get("custom_fields") or [],
        created_at=_iso_or_none(v.get("created_at")),
        updated_at=_iso_or_none(v.get("updated_at")),
        deleted_at=_iso_or_none(v.get("deleted_at")),
    )


async def _fetch_variant_by_id(services: Any, variant_id: int) -> dict[str, Any] | None:
    """Look up a variant by ID — cache first, then API fallback.

    Returns None if the variant is not found. Uses ``raise_on_error=False``
    so a 404 (or an ErrorResponse body) becomes ``None`` instead of a raw
    ``APIError``, which is what callers expect as the "not found" sentinel.
    """
    v = await services.cache.get_by_id(EntityType.VARIANT, variant_id)
    if v:
        return v
    # Cache miss — fetch from API
    from katana_public_api_client.api.variant import get_variant
    from katana_public_api_client.models import ErrorResponse
    from katana_public_api_client.utils import unwrap

    response = await get_variant.asyncio_detailed(id=variant_id, client=services.client)
    variant_obj = unwrap(response, raise_on_error=False)
    if variant_obj is None or isinstance(variant_obj, ErrorResponse):
        return None
    return variant_obj.to_dict()


@cache_read(EntityType.VARIANT)
async def _get_variant_details_impl(
    request: GetVariantDetailsRequest, context: Context
) -> list[VariantDetailsResponse]:
    """Look up one or more variants by SKU(s) or variant ID(s).

    Returns a list of matching variants. Raises ValueError if any are not found.
    """
    skus: list[str] = []
    variant_ids: list[int] = []

    if request.sku is not None:
        # Validate explicit single SKU (even empty string)
        if not request.sku.strip():
            raise ValueError("SKU cannot be empty")
        skus.append(request.sku)
    if request.skus:
        skus.extend(request.skus)
    if request.variant_id is not None:
        variant_ids.append(request.variant_id)
    if request.variant_ids:
        variant_ids.extend(request.variant_ids)

    if not skus and not variant_ids:
        raise ValueError(
            "Must provide at least one of: sku, variant_id, skus, variant_ids"
        )

    services = get_services(context)

    # Validate SKUs aren't blank before dispatching
    sku_cleaned = [s.strip() for s in skus]
    if any(not clean for clean in sku_cleaned):
        raise ValueError("SKU cannot be empty")

    # Parallelize both groups of lookups
    sku_variants, id_variants = await asyncio.gather(
        asyncio.gather(*(services.cache.get_by_sku(s) for s in sku_cleaned)),
        asyncio.gather(*(_fetch_variant_by_id(services, v) for v in variant_ids)),
    )

    results: list[VariantDetailsResponse] = []
    for sku, v in zip(sku_cleaned, sku_variants, strict=True):
        if not v:
            raise ValueError(f"Variant with SKU '{sku}' not found")
        results.append(_dict_to_variant_details(v))
    for variant_id, v in zip(variant_ids, id_variants, strict=True):
        if v is None:
            raise ValueError(f"Variant ID {variant_id} not found")
        results.append(_dict_to_variant_details(v))

    return results


@observe_tool
@unpack_pydantic_params
async def get_variant_details(
    request: Annotated[GetVariantDetailsRequest, Unpack()], context: Context
) -> ToolResult:
    """Get comprehensive variant details by SKU(s) or variant ID(s).

    Pass one or more values via ``skus`` / ``variant_ids`` (or the singular
    ``sku`` / ``variant_id``). A single item returns a rich detail card; multiple
    items return a summary table. Batching N lookups in one call beats N
    separate invocations.

    Returns pricing, barcodes, supplier codes, and more.

    Use after search_items, or pass variant IDs from other sources (PO line
    items, MO recipe rows) to resolve them to SKUs and full details.

    Tries the cache first; falls back to the API for variant IDs not in cache.
    Raises ValueError if any requested variant is not found.
    """
    responses = await _get_variant_details_impl(request, context)

    if request.format == "json":
        payload = {"variants": [r.model_dump() for r in responses]}
        import json as _json

        return ToolResult(
            content=_json.dumps(payload, indent=2, default=str),
            structured_content=payload,
        )

    # If a single-variant request, return the single-variant markdown + UI.
    # Treat a single-element batch list (skus=[X] or variant_ids=[X]) the same
    # as the singular form to honor the docstring's "single item" promise.
    is_single = len(responses) == 1 and (
        request.sku is not None
        or request.variant_id is not None
        or len(request.skus or []) == 1
        or len(request.variant_ids or []) == 1
    )
    if is_single:
        return _variant_details_to_tool_result(responses[0])

    # Batch response: summary + table
    table = format_md_table(
        headers=["ID", "SKU", "Name", "Sales Price", "Purchase Price"],
        rows=[
            [
                v.id,
                v.sku,
                v.name,
                f"${v.sales_price:,.2f}" if v.sales_price is not None else "N/A",
                f"${v.purchase_price:,.2f}" if v.purchase_price is not None else "N/A",
            ]
            for v in responses
        ],
    )
    markdown = f"## Variant Details ({len(responses)} variants)\n\n{table}"

    return make_simple_result(
        markdown,
        structured_data={"variants": [v.model_dump() for v in responses]},
    )


def register_tools(mcp: FastMCP) -> None:
    """Register all item tools with the FastMCP instance.

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
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
        openWorldHint=True,
    )

    mcp.tool(tags={"catalog", "read"}, annotations=_read, meta=UI_META)(search_items)
    mcp.tool(tags={"catalog", "write"}, annotations=_write, meta=UI_META)(create_item)
    mcp.tool(tags={"catalog", "read"}, annotations=_read, meta=UI_META)(get_item)
    mcp.tool(tags={"catalog", "write"}, annotations=_update, meta=UI_META)(update_item)
    mcp.tool(
        tags={"catalog", "write", "destructive"},
        annotations=_destructive,
        meta=UI_META,
    )(delete_item)
    mcp.tool(tags={"catalog", "read"}, annotations=_read, meta=UI_META)(
        get_variant_details
    )
