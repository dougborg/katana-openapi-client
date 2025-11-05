"""Item management tools for Katana MCP Server.

Foundation tools for searching and managing items (variants, products, materials, services).
Items are things with SKUs - they appear in the "Items" tab of the Katana UI.
"""

from __future__ import annotations

import logging
from enum import Enum

from fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

from katana_mcp.services import get_services
from katana_public_api_client.client_types import UNSET
from katana_public_api_client.models import (
    CreateMaterialRequest,
    CreateProductRequest,
    CreateServiceRequest,
    CreateServiceVariantRequest,
    CreateVariantRequest,
)

logger = logging.getLogger(__name__)


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

    logger.info(f"Searching items for query: '{request.query}' (limit={request.limit})")

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

        logger.info(f"Found {response.total_count} items matching '{request.query}'")
        return response

    except Exception as e:
        logger.error(f"Failed to search items for query '{request.query}': {e}")
        raise


async def search_items(
    request: SearchItemsRequest, context: Context
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
    logger.info(f"Creating {request.type} item: {request.name} (SKU: {request.sku})")

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
        logger.error(f"Failed to create {request.type} item '{request.name}': {e}")
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


def register_tools(mcp: FastMCP) -> None:
    """Register all item tools with the FastMCP instance.

    Args:
        mcp: FastMCP server instance to register tools with
    """
    mcp.tool()(search_items)
    mcp.tool()(create_item)
