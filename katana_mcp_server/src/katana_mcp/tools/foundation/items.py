"""Item management tools for Katana MCP Server.

Foundation tools for searching and managing items (variants, products, materials, services).
Items are things with SKUs - they appear in the "Items" tab of the Katana UI.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any

from fastmcp import Context, FastMCP
from fastmcp.tools.tool import ToolResult
from pydantic import BaseModel, Field

from katana_mcp.cache import EntityType
from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.decorators import cache_read
from katana_mcp.tools.tool_result_utils import make_tool_result
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


class ItemInfo(BaseModel):
    """Item information."""

    id: int
    sku: str
    name: str
    is_sellable: bool
    stock_level: int | None = None


class SearchItemsResponse(BaseModel):
    """Response containing search results."""

    items: list[ItemInfo]
    total_count: int


def _search_response_to_tool_result(
    response: SearchItemsResponse, query: str
) -> ToolResult:
    """Convert SearchItemsResponse to ToolResult with markdown template."""
    # Build items table for template
    if response.items:
        items_table = "\n".join(
            f"- **{item.sku}**: {item.name} (ID: {item.id}, Sellable: {item.is_sellable})"
            for item in response.items
        )
    else:
        items_table = "No items found matching your query."

    # Count by type (we don't have type info in ItemInfo, so use placeholders)
    product_count = sum(1 for item in response.items if item.is_sellable)
    material_count = response.total_count - product_count
    service_count = 0

    return make_tool_result(
        response,
        "item_search_results",
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
    """Search for items (products, materials, services) by name or SKU.

    Use this as the starting point when you need to find items. Returns item IDs
    and SKUs needed by other tools like create_purchase_order or check_inventory.
    For full details on a specific item, follow up with get_variant_details.

    Query must not be empty. Default limit is 20 results.
    """
    response = await _search_items_impl(request, context)
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
    response = await _create_item_impl(request, context)
    return make_tool_result(
        response,
        "item_created",
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


class ItemDetailsResponse(BaseModel):
    """Detailed item information."""

    id: int
    name: str
    type: ItemType
    uom: str | None = None
    category_name: str | None = None
    is_sellable: bool | None = None
    is_producible: bool | None = None  # Products only
    is_purchasable: bool | None = None  # Products/Materials
    default_supplier_id: int | None = None
    additional_info: str | None = None


async def _get_item_impl(
    request: GetItemRequest, context: Context
) -> ItemDetailsResponse:
    """Get item details by ID and type."""
    services = get_services(context)
    helper = _get_type_helper(services.client, request.type)
    item = await helper.get(request.id)

    return ItemDetailsResponse(
        id=item.id,
        name=item.name or "",
        type=request.type,
        uom=item.uom,
        category_name=item.category_name,
        is_sellable=item.is_sellable,
        is_producible=getattr(item, "is_producible", None),
        is_purchasable=getattr(item, "is_purchasable", None),
        additional_info=getattr(item, "additional_info", None),
    )


@observe_tool
@unpack_pydantic_params
async def get_item(
    request: Annotated[GetItemRequest, Unpack()], context: Context
) -> ToolResult:
    """Get item details by ID and type (product, material, or service).

    Use when you already have an item ID and type from search_items or another tool.
    Returns item properties like name, UOM, category, and flags (sellable, producible).
    For variant-level details (pricing, barcodes, supplier codes), use get_variant_details instead.
    """
    response = await _get_item_impl(request, context)
    return make_tool_result(
        response,
        "item_details",
        sku="N/A",
        name=response.name,
        item_type=response.type,
        id=response.id,
        description=response.additional_info or "No description",
        uom=response.uom or "N/A",
        is_sellable="Yes" if response.is_sellable else "No",
        is_producible="Yes" if response.is_producible else "N/A",
        is_purchasable="Yes" if response.is_purchasable else "N/A",
        sales_price="N/A",
        cost="N/A",
        in_stock="N/A",
        available="N/A",
        allocated="N/A",
        on_order="N/A",
        supplier_info="Use get_variant_details for supplier info",
    )


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

    result = await helper.update(request.id, update_data)

    # Invalidate only the affected type + variants
    cache = getattr(services, "cache", None)
    if cache:
        await cache.mark_dirty(request.type.value)
        await cache.mark_dirty(EntityType.VARIANT)

    return UpdateItemResponse(
        id=result.id,
        name=result.name or "",
        type=request.type,
        message=f"{request.type.value.title()} '{result.name or 'Unknown'}' (ID {result.id}) updated successfully",
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
    response = await _update_item_impl(request, context)
    return make_tool_result(
        response,
        "item_updated",
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
    response = await _delete_item_impl(request, context)
    return make_tool_result(
        response,
        "item_deleted",
        id=response.id,
        item_type=response.type,
        message=response.message,
    )


# ============================================================================
# Tool 6: get_variant_details
# ============================================================================


class GetVariantDetailsRequest(BaseModel):
    """Request to get variant details by SKU."""

    sku: str = Field(..., description="SKU to look up")


class VariantDetailsResponse(BaseModel):
    """Detailed variant information including all properties."""

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


def _variant_details_to_tool_result(response: VariantDetailsResponse) -> ToolResult:
    """Convert VariantDetailsResponse to ToolResult with markdown template."""
    # Build supplier info text
    if response.supplier_item_codes:
        supplier_info = "\n".join(f"- {code}" for code in response.supplier_item_codes)
    else:
        supplier_info = "No supplier codes registered"

    # Handle None values for template - format as currency string or N/A
    sales_price = (
        f"${response.sales_price:,.2f}" if response.sales_price is not None else "N/A"
    )
    cost = (
        f"${response.purchase_price:,.2f}"
        if response.purchase_price is not None
        else "N/A"
    )
    item_type = response.type or "unknown"
    description = response.product_or_material_name or "No description"

    return make_tool_result(
        response,
        "item_details",
        sku=response.sku,
        name=response.name,
        item_type=item_type,
        id=response.id,
        description=description,
        uom="N/A",  # Not available in variant response
        is_sellable="Yes" if item_type == "product" else "No",
        is_producible="N/A",  # Not available in variant response
        is_purchasable="N/A",  # Not available in variant response
        sales_price=sales_price,
        cost=cost,
        in_stock="N/A",  # Not available in variant response
        available="N/A",
        allocated="N/A",
        on_order="N/A",
        supplier_info=supplier_info,
    )


@cache_read(EntityType.VARIANT)
async def _get_variant_details_impl(
    request: GetVariantDetailsRequest, context: Context
) -> VariantDetailsResponse:
    """Look up variant details by SKU from cache."""
    if not request.sku or not request.sku.strip():
        raise ValueError("SKU cannot be empty")

    services = get_services(context)
    v = await services.cache.get_by_sku(request.sku)

    if not v:
        raise ValueError(f"Variant with SKU '{request.sku}' not found")

    return VariantDetailsResponse(
        id=v["id"],
        sku=v.get("sku"),
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
        created_at=v.get("created_at"),
        updated_at=v.get("updated_at"),
    )


@observe_tool
@unpack_pydantic_params
async def get_variant_details(
    request: Annotated[GetVariantDetailsRequest, Unpack()], context: Context
) -> ToolResult:
    """Get comprehensive variant details by SKU — pricing, barcodes, supplier codes, and more.

    Use after search_items to get full details on a specific item. Returns the variant ID
    needed for create_purchase_order and create_sales_order line items.

    Performs an exact case-insensitive SKU match. Raises ValueError if SKU not found.
    """
    response = await _get_variant_details_impl(request, context)
    return _variant_details_to_tool_result(response)


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

    mcp.tool(tags={"catalog", "read"}, annotations=_read)(search_items)
    mcp.tool(tags={"catalog", "write"}, annotations=_write)(create_item)
    mcp.tool(tags={"catalog", "read"}, annotations=_read)(get_item)
    mcp.tool(tags={"catalog", "write"}, annotations=_update)(update_item)
    mcp.tool(tags={"catalog", "write", "destructive"}, annotations=_destructive)(
        delete_item
    )
    mcp.tool(tags={"catalog", "read"}, annotations=_read)(get_variant_details)
