"""Item management tools for Katana MCP Server.

Foundation tools for searching and managing items (variants, products, materials, services).
Items are things with SKUs - they appear in the "Items" tab of the Katana UI.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

from katana_mcp.logging import get_logger
from katana_mcp.services import get_services
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.client_types import UNSET
from katana_public_api_client.models import (
    CreateMaterialRequest,
    CreateProductRequest,
    CreateServiceRequest,
    CreateServiceVariantRequest,
    CreateVariantRequest,
)

logger = get_logger(__name__)


# ============================================================================
# Shared Models
# ============================================================================


class ItemType(str, Enum):
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


async def _search_items_impl(
    request: SearchItemsRequest, context: Context
) -> SearchItemsResponse:
    """Implementation of search_items tool.

    Args:
        request: Request with search query and limit
        context: Server context with KatanaClient

    Returns:
        List of matching item variants with extended names

    Raises:
        ValueError: If query is empty or limit is invalid
        Exception: If API call fails
    """
    if not request.query or not request.query.strip():
        raise ValueError("Search query cannot be empty")
    if request.limit <= 0:
        raise ValueError("Limit must be positive")

    start_time = time.monotonic()
    logger.info("item_search_started", query=request.query, limit=request.limit)

    try:
        # Access services using helper
        services = get_services(context)

        # Search variants (which have SKUs) with parent product/material info
        variants = await services.client.variants.search(
            request.query, limit=request.limit
        )

        # Build response - format names matching Katana UI
        items_info = []
        for variant in variants:
            # Build variant name using domain model method
            # Format: "Product Name / Config1 / Config2 / ..."
            name = variant.get_display_name()

            # Determine if variant is sellable (products are sellable, materials are not)
            is_sellable = variant.type_ == "product" if variant.type_ else False

            items_info.append(
                ItemInfo(
                    id=variant.id,
                    sku=variant.sku or "",
                    name=name,
                    is_sellable=is_sellable,
                    stock_level=None,  # Variants don't have stock_level directly
                )
            )

        response = SearchItemsResponse(
            items=items_info,
            total_count=len(items_info),
        )

        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.info(
            "item_search_completed",
            query=request.query,
            result_count=response.total_count,
            duration_ms=duration_ms,
        )
        return response

    except Exception as e:
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.error(
            "item_search_failed",
            query=request.query,
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=duration_ms,
            exc_info=True,
        )
        raise


@unpack_pydantic_params
async def search_items(
    request: Annotated[SearchItemsRequest, Unpack()], context: Context
) -> SearchItemsResponse:
    """Search for items by name or SKU.

    Searches across all SKU-bearing items (variants, products, materials, services)
    to find matches. Items are things that appear in the "Items" tab of Katana UI.

    Args:
        request: Request with search query and limit
        context: Server context with KatanaClient

    Returns:
        List of matching items with basic info

    Example:
        Request: {"query": "widget", "limit": 10}
        Returns: {"items": [...], "total_count": 5}
    """
    return await _search_items_impl(request, context)


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
    """Implementation of create_item tool.

    Args:
        request: Request with item details
        context: Server context with KatanaClient

    Returns:
        Created item details

    Raises:
        ValueError: If type is invalid or required fields missing
        Exception: If API call fails
    """
    start_time = time.monotonic()
    logger.info(
        "item_create_started",
        item_type=request.type,
        name=request.name,
        sku=request.sku,
    )

    try:
        services = get_services(context)

        # Create variant request (common to products/materials)
        variant = CreateVariantRequest(
            sku=request.sku,
            sales_price=request.sales_price
            if request.sales_price is not None
            else UNSET,
            purchase_price=request.purchase_price
            if request.purchase_price is not None
            else UNSET,
        )

        # Route based on item type
        if request.type == ItemType.PRODUCT:
            product_request = CreateProductRequest(
                name=request.name,
                uom=request.uom,
                category_name=request.category_name
                if request.category_name is not None
                else UNSET,
                is_sellable=request.is_sellable,
                is_producible=request.is_producible,
                is_purchasable=request.is_purchasable,
                default_supplier_id=request.default_supplier_id
                if request.default_supplier_id is not None
                else UNSET,
                additional_info=request.additional_info
                if request.additional_info is not None
                else UNSET,
                variants=[variant],
            )
            product = await services.client.products.create(product_request)
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            logger.info(
                "item_create_completed",
                item_type=ItemType.PRODUCT,
                item_id=product.id,
                name=product.name,
                sku=request.sku,
                duration_ms=duration_ms,
            )
            return CreateItemResponse(
                id=product.id,
                name=product.name or "",
                type=ItemType.PRODUCT,
                sku=request.sku,
                message=f"Product '{product.name}' created successfully with SKU {request.sku}",
            )

        elif request.type == ItemType.MATERIAL:
            material_request = CreateMaterialRequest(
                name=request.name,
                uom=request.uom,
                category_name=request.category_name
                if request.category_name is not None
                else UNSET,
                is_sellable=request.is_sellable,
                default_supplier_id=request.default_supplier_id
                if request.default_supplier_id is not None
                else UNSET,
                additional_info=request.additional_info
                if request.additional_info is not None
                else UNSET,
                variants=[variant],
            )
            material = await services.client.materials.create(material_request)
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            logger.info(
                "item_create_completed",
                item_type=ItemType.MATERIAL,
                item_id=material.id,
                name=material.name,
                sku=request.sku,
                duration_ms=duration_ms,
            )
            return CreateItemResponse(
                id=material.id,
                name=material.name or "",
                type=ItemType.MATERIAL,
                sku=request.sku,
                message=f"Material '{material.name}' created successfully with SKU {request.sku}",
            )

        elif request.type == ItemType.SERVICE:
            # Services use a different variant model
            service_variant = CreateServiceVariantRequest(
                sku=request.sku,
                sales_price=request.sales_price
                if request.sales_price is not None
                else UNSET,
                default_cost=request.purchase_price
                if request.purchase_price is not None
                else UNSET,
            )
            service_request = CreateServiceRequest(
                name=request.name,
                uom=request.uom,
                category_name=request.category_name
                if request.category_name is not None
                else UNSET,
                is_sellable=request.is_sellable,
                variants=[service_variant],
            )
            service = await services.client.services.create(service_request)
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            logger.info(
                "item_create_completed",
                item_type=ItemType.SERVICE,
                item_id=service.id,
                name=service.name,
                sku=request.sku,
                duration_ms=duration_ms,
            )
            return CreateItemResponse(
                id=service.id,
                name=service.name or "",
                type=ItemType.SERVICE,
                sku=request.sku,
                message=f"Service '{service.name}' created successfully with SKU {request.sku}",
            )

        else:
            raise ValueError(f"Invalid item type: {request.type}")

    except Exception as e:
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.error(
            "item_create_failed",
            item_type=request.type,
            name=request.name,
            sku=request.sku,
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=duration_ms,
            exc_info=True,
        )
        raise


async def create_item(
    request: CreateItemRequest, context: Context
) -> CreateItemResponse:
    """Create a new item (product, material, or service).

    This tool provides a unified interface for creating items with a single variant.
    The tool routes to the appropriate API based on the item type.

    Supported types:
    - PRODUCT: Finished goods that can be sold and/or manufactured
    - MATERIAL: Raw materials and components used in manufacturing
    - SERVICE: External services used in operations

    Args:
        request: Request with item details and type
        context: Server context with KatanaClient

    Returns:
        Created item details including ID and variant information

    Example:
        Request: {
            "type": "product",
            "name": "Widget Pro",
            "sku": "WGT-PRO-001",
            "uom": "pcs",
            "is_sellable": true,
            "is_producible": true,
            "sales_price": 29.99
        }
        Returns: {
            "id": 123,
            "name": "Widget Pro",
            "type": "product",
            "variant_id": 456,
            "sku": "WGT-PRO-001",
            "message": "Product 'Widget Pro' created successfully"
        }
    """
    return await _create_item_impl(request, context)


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
    """Implementation of get_item tool.

    Args:
        request: Request with item ID and type
        context: Server context with KatanaClient

    Returns:
        Item details

    Raises:
        ValueError: If type is invalid
        Exception: If API call fails or item not found
    """
    start_time = time.monotonic()
    logger.info("item_get_started", item_type=request.type, item_id=request.id)

    try:
        services = get_services(context)

        # Route based on item type
        if request.type == ItemType.PRODUCT:
            product = await services.client.products.get(request.id)
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            logger.info(
                "item_get_completed",
                item_type=ItemType.PRODUCT,
                item_id=product.id,
                name=product.name,
                duration_ms=duration_ms,
            )
            return ItemDetailsResponse(
                id=product.id,
                name=product.name,
                type=ItemType.PRODUCT,
                uom=product.uom,
                category_name=product.category_name,
                is_sellable=product.is_sellable,
                is_producible=product.is_producible,
                is_purchasable=product.is_purchasable,
                additional_info=product.additional_info,
            )

        elif request.type == ItemType.MATERIAL:
            material = await services.client.materials.get(request.id)
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            logger.info(
                "item_get_completed",
                item_type=ItemType.MATERIAL,
                item_id=material.id,
                name=material.name,
                duration_ms=duration_ms,
            )
            return ItemDetailsResponse(
                id=material.id,
                name=material.name,
                type=ItemType.MATERIAL,
                uom=material.uom,
                category_name=material.category_name,
                is_sellable=material.is_sellable,
                additional_info=material.additional_info,
            )

        elif request.type == ItemType.SERVICE:
            service = await services.client.services.get(request.id)
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            logger.info(
                "item_get_completed",
                item_type=ItemType.SERVICE,
                item_id=service.id,
                name=service.name,
                duration_ms=duration_ms,
            )
            return ItemDetailsResponse(
                id=service.id,
                name=service.name or "",
                type=ItemType.SERVICE,
                uom=service.uom,
                category_name=service.category_name,
                is_sellable=service.is_sellable,
            )

        else:
            raise ValueError(f"Invalid item type: {request.type}")

    except Exception as e:
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.error(
            "item_get_failed",
            item_type=request.type,
            item_id=request.id,
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=duration_ms,
            exc_info=True,
        )
        raise


async def get_item(request: GetItemRequest, context: Context) -> ItemDetailsResponse:
    """Get item details by ID and type.

    Retrieves detailed information about a specific item.

    Args:
        request: Request with item ID and type
        context: Server context with KatanaClient

    Returns:
        Detailed item information

    Example:
        Request: {"id": 123, "type": "product"}
        Returns: {"id": 123, "name": "Widget Pro", "type": "product", ...}
    """
    return await _get_item_impl(request, context)


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
    """Implementation of update_item tool.

    Args:
        request: Request with item ID, type, and fields to update
        context: Server context with KatanaClient

    Returns:
        Updated item confirmation

    Raises:
        ValueError: If type is invalid
        Exception: If API call fails
    """
    start_time = time.monotonic()
    logger.info("item_update_started", item_type=request.type, item_id=request.id)

    try:
        services = get_services(context)

        # Import update models
        from katana_public_api_client.models import (
            UpdateMaterialRequest,
            UpdateProductRequest,
            UpdateServiceRequest,
        )

        # Route based on item type
        if request.type == ItemType.PRODUCT:
            update_data = UpdateProductRequest(
                name=request.name if request.name is not None else UNSET,
                uom=request.uom if request.uom is not None else UNSET,
                category_name=request.category_name
                if request.category_name is not None
                else UNSET,
                is_sellable=request.is_sellable
                if request.is_sellable is not None
                else UNSET,
                is_producible=request.is_producible
                if request.is_producible is not None
                else UNSET,
                is_purchasable=request.is_purchasable
                if request.is_purchasable is not None
                else UNSET,
                default_supplier_id=request.default_supplier_id
                if request.default_supplier_id is not None
                else UNSET,
                additional_info=request.additional_info
                if request.additional_info is not None
                else UNSET,
            )
            product = await services.client.products.update(request.id, update_data)
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            logger.info(
                "item_update_completed",
                item_type=ItemType.PRODUCT,
                item_id=product.id,
                name=product.name,
                duration_ms=duration_ms,
            )
            return UpdateItemResponse(
                id=product.id,
                name=product.name,
                type=ItemType.PRODUCT,
                message=f"Product '{product.name}' (ID {product.id}) updated successfully",
            )

        elif request.type == ItemType.MATERIAL:
            material_update_data = UpdateMaterialRequest(
                name=request.name if request.name is not None else UNSET,
                uom=request.uom if request.uom is not None else UNSET,
                category_name=request.category_name
                if request.category_name is not None
                else UNSET,
                is_sellable=request.is_sellable
                if request.is_sellable is not None
                else UNSET,
                default_supplier_id=request.default_supplier_id
                if request.default_supplier_id is not None
                else UNSET,
                additional_info=request.additional_info
                if request.additional_info is not None
                else UNSET,
            )
            material = await services.client.materials.update(
                request.id, material_update_data
            )
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            logger.info(
                "item_update_completed",
                item_type=ItemType.MATERIAL,
                item_id=material.id,
                name=material.name,
                duration_ms=duration_ms,
            )
            return UpdateItemResponse(
                id=material.id,
                name=material.name or "",
                type=ItemType.MATERIAL,
                message=f"Material '{material.name or 'Unknown'}' (ID {material.id}) updated successfully",
            )

        elif request.type == ItemType.SERVICE:
            service_update_data = UpdateServiceRequest(
                name=request.name if request.name is not None else UNSET,
                uom=request.uom if request.uom is not None else UNSET,
                category_name=request.category_name
                if request.category_name is not None
                else UNSET,
                is_sellable=request.is_sellable
                if request.is_sellable is not None
                else UNSET,
            )
            service = await services.client.services.update(
                request.id, service_update_data
            )
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            logger.info(
                "item_update_completed",
                item_type=ItemType.SERVICE,
                item_id=service.id,
                name=service.name,
                duration_ms=duration_ms,
            )
            return UpdateItemResponse(
                id=service.id,
                name=service.name or "",
                type=ItemType.SERVICE,
                message=f"Service '{service.name or 'Unknown'}' (ID {service.id}) updated successfully",
            )

        else:
            raise ValueError(f"Invalid item type: {request.type}")

    except Exception as e:
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.error(
            "item_update_failed",
            item_type=request.type,
            item_id=request.id,
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=duration_ms,
            exc_info=True,
        )
        raise


async def update_item(
    request: UpdateItemRequest, context: Context
) -> UpdateItemResponse:
    """Update an existing item.

    Updates fields for a product, material, or service. Only provided fields
    are updated; omitted fields remain unchanged.

    Args:
        request: Request with item ID, type, and fields to update
        context: Server context with KatanaClient

    Returns:
        Updated item confirmation

    Example:
        Request: {"id": 123, "type": "product", "name": "Widget Pro v2", "sales_price": 34.99}
        Returns: {"id": 123, "name": "Widget Pro v2", "type": "product", "message": "..."}
    """
    return await _update_item_impl(request, context)


# ============================================================================
# Tool 5: delete_item
# ============================================================================


class DeleteItemRequest(BaseModel):
    """Request to delete an item."""

    id: int = Field(..., description="Item ID")
    type: ItemType = Field(..., description="Type of item")


class DeleteItemResponse(BaseModel):
    """Response from deleting an item."""

    id: int
    type: ItemType
    success: bool = True
    message: str = "Item deleted successfully"


async def _delete_item_impl(
    request: DeleteItemRequest, context: Context
) -> DeleteItemResponse:
    """Implementation of delete_item tool.

    Args:
        request: Request with item ID and type
        context: Server context with KatanaClient

    Returns:
        Deletion confirmation

    Raises:
        ValueError: If type is invalid
        Exception: If API call fails
    """
    start_time = time.monotonic()
    logger.info("item_delete_started", item_type=request.type, item_id=request.id)

    try:
        services = get_services(context)

        # Route based on item type
        if request.type == ItemType.PRODUCT:
            await services.client.products.delete(request.id)
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            logger.info(
                "item_delete_completed",
                item_type=ItemType.PRODUCT,
                item_id=request.id,
                duration_ms=duration_ms,
            )
            return DeleteItemResponse(
                id=request.id,
                type=ItemType.PRODUCT,
                message=f"Product ID {request.id} deleted successfully",
            )

        elif request.type == ItemType.MATERIAL:
            await services.client.materials.delete(request.id)
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            logger.info(
                "item_delete_completed",
                item_type=ItemType.MATERIAL,
                item_id=request.id,
                duration_ms=duration_ms,
            )
            return DeleteItemResponse(
                id=request.id,
                type=ItemType.MATERIAL,
                message=f"Material ID {request.id} deleted successfully",
            )

        elif request.type == ItemType.SERVICE:
            await services.client.services.delete(request.id)
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            logger.info(
                "item_delete_completed",
                item_type=ItemType.SERVICE,
                item_id=request.id,
                duration_ms=duration_ms,
            )
            return DeleteItemResponse(
                id=request.id,
                type=ItemType.SERVICE,
                message=f"Service ID {request.id} deleted successfully",
            )

        else:
            raise ValueError(f"Invalid item type: {request.type}")

    except Exception as e:
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.error(
            "item_delete_failed",
            item_type=request.type,
            item_id=request.id,
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=duration_ms,
            exc_info=True,
        )
        raise


async def delete_item(
    request: DeleteItemRequest, context: Context
) -> DeleteItemResponse:
    """Delete an item by ID and type.

    Permanently removes a product, material, or service from the system.

    Args:
        request: Request with item ID and type
        context: Server context with KatanaClient

    Returns:
        Deletion confirmation

    Example:
        Request: {"id": 123, "type": "product"}
        Returns: {"id": 123, "type": "product", "message": "Product ID 123 deleted successfully"}
    """
    return await _delete_item_impl(request, context)


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


async def _get_variant_details_impl(
    request: GetVariantDetailsRequest, context: Context
) -> VariantDetailsResponse:
    """Implementation of get_variant_details tool.

    Args:
        request: Request with SKU
        context: Server context with KatanaClient

    Returns:
        Detailed variant information

    Raises:
        ValueError: If SKU is empty, invalid, or variant not found
        Exception: If API call fails for other reasons
    """
    if not request.sku or not request.sku.strip():
        raise ValueError("SKU cannot be empty")

    start_time = time.monotonic()
    logger.info("variant_details_started", sku=request.sku)

    try:
        services = get_services(context)

        # Search for the variant by SKU
        # The search method returns a list, we need to find exact match
        variants = await services.client.variants.search(request.sku, limit=100)

        # Find exact SKU match (case-insensitive)
        matching_variant = None
        for variant in variants:
            if variant.sku and variant.sku.lower() == request.sku.lower():
                matching_variant = variant
                break

        if not matching_variant:
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            logger.info(
                "variant_details_not_found",
                sku=request.sku,
                duration_ms=duration_ms,
            )
            raise ValueError(f"Variant with SKU '{request.sku}' not found")

        # Build detailed response from KatanaVariant domain model
        response = VariantDetailsResponse(
            id=matching_variant.id,
            sku=matching_variant.sku,
            name=matching_variant.get_display_name(),
            sales_price=matching_variant.sales_price,
            purchase_price=matching_variant.purchase_price,
            type=matching_variant.type_,
            product_id=matching_variant.product_id,
            material_id=matching_variant.material_id,
            product_or_material_name=matching_variant.product_or_material_name,
            internal_barcode=matching_variant.internal_barcode,
            registered_barcode=matching_variant.registered_barcode,
            supplier_item_codes=matching_variant.supplier_item_codes,
            lead_time=matching_variant.lead_time,
            minimum_order_quantity=matching_variant.minimum_order_quantity,
            config_attributes=matching_variant.config_attributes,
            custom_fields=matching_variant.custom_fields,
            created_at=matching_variant.created_at.isoformat()
            if matching_variant.created_at
            else None,
            updated_at=matching_variant.updated_at.isoformat()
            if matching_variant.updated_at
            else None,
        )

        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.info(
            "variant_details_completed",
            sku=request.sku,
            variant_id=matching_variant.id,
            name=matching_variant.get_display_name(),
            duration_ms=duration_ms,
        )
        return response

    except ValueError:
        # Re-raise validation errors
        raise
    except Exception as e:
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.error(
            "variant_details_failed",
            sku=request.sku,
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=duration_ms,
            exc_info=True,
        )
        raise


async def get_variant_details(
    request: GetVariantDetailsRequest, context: Context
) -> VariantDetailsResponse:
    """Get detailed variant information by SKU.

    Retrieves comprehensive details about a specific variant including pricing,
    barcodes, configuration attributes, custom fields, and more.

    Args:
        request: Request with SKU to look up
        context: Server context with KatanaClient

    Returns:
        Detailed variant information including all properties

    Example:
        Request: {"sku": "WIDGET-001"}
        Returns: {
            "id": 123,
            "sku": "WIDGET-001",
            "name": "Widget Pro / Large / Blue",
            "sales_price": 29.99,
            "purchase_price": 15.00,
            "type": "product",
            "config_attributes": [
                {"config_name": "Size", "config_value": "Large"},
                {"config_name": "Color", "config_value": "Blue"}
            ],
            ...
        }
    """
    return await _get_variant_details_impl(request, context)


def register_tools(mcp: FastMCP) -> None:
    """Register all item tools with the FastMCP instance.

    Args:
        mcp: FastMCP server instance to register tools with
    """
    mcp.tool()(search_items)
    mcp.tool()(create_item)
    mcp.tool()(get_item)
    mcp.tool()(update_item)
    mcp.tool()(delete_item)
    mcp.tool()(get_variant_details)
