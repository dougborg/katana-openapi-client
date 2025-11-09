"""Catalog management tools for Katana MCP Server.

Foundation tools for creating and managing products and materials in the catalog.
These are dedicated tools that simplify the more general create_item tool.
"""

from __future__ import annotations

import time
from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

from katana_mcp.logging import get_logger
from katana_mcp.services import get_services
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.client_types import UNSET
from katana_public_api_client.models import (
    CreateMaterialRequest as ApiCreateMaterialRequest,
    CreateProductRequest as ApiCreateProductRequest,
    CreateVariantRequest,
)

logger = get_logger(__name__)


# ============================================================================
# Tool 1: create_product
# ============================================================================


class CreateProductRequest(BaseModel):
    """Request model for creating a product."""

    name: str = Field(..., description="Product name")
    sku: str = Field(..., description="SKU for the product variant")
    uom: str = Field(
        default="pcs", description="Unit of measure (e.g., pcs, kg, hours)"
    )
    category_name: str | None = Field(None, description="Category for grouping")
    is_sellable: bool = Field(True, description="Whether product can be sold")
    is_producible: bool = Field(False, description="Can be manufactured")
    is_purchasable: bool = Field(True, description="Can be purchased")
    sales_price: float | None = Field(None, description="Sales price per unit")
    purchase_price: float | None = Field(None, description="Purchase cost per unit")
    default_supplier_id: int | None = Field(None, description="Default supplier ID")
    additional_info: str | None = Field(None, description="Additional notes")


class CreateProductResponse(BaseModel):
    """Response from creating a product."""

    id: int
    name: str
    sku: str
    success: bool = True
    message: str = "Product created successfully"


async def _create_product_impl(
    request: CreateProductRequest, context: Context
) -> CreateProductResponse:
    """Implementation of create_product tool.

    Args:
        request: Request with product details
        context: Server context with KatanaClient

    Returns:
        Created product details

    Raises:
        ValueError: If required fields are missing or invalid
        Exception: If API call fails
    """
    start_time = time.monotonic()
    logger.info(
        "product_create_started",
        name=request.name,
        sku=request.sku,
    )

    try:
        services = get_services(context)

        # Create variant request
        variant = CreateVariantRequest(
            sku=request.sku,
            sales_price=request.sales_price
            if request.sales_price is not None
            else UNSET,
            purchase_price=request.purchase_price
            if request.purchase_price is not None
            else UNSET,
        )

        # Create product request
        product_request = ApiCreateProductRequest(
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
            "product_create_completed",
            product_id=product.id,
            name=product.name,
            sku=request.sku,
            duration_ms=duration_ms,
        )

        return CreateProductResponse(
            id=product.id,
            name=product.name or "",
            sku=request.sku,
            message=f"Product '{product.name}' created successfully with SKU {request.sku}",
        )

    except Exception as e:
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.error(
            "product_create_failed",
            name=request.name,
            sku=request.sku,
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=duration_ms,
            exc_info=True,
        )
        raise


@unpack_pydantic_params
async def create_product(
    request: Annotated[CreateProductRequest, Unpack()], context: Context
) -> CreateProductResponse:
    """Create a new product in Katana.

    This tool creates a finished good product that can be sold and/or manufactured.
    Products are items that appear in the catalog and can have multiple variants.

    Args:
        request: Request with product details
        context: Server context with KatanaClient

    Returns:
        Created product details including ID and SKU

    Example:
        Request: {
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
            "sku": "WGT-PRO-001",
            "message": "Product 'Widget Pro' created successfully"
        }
    """
    return await _create_product_impl(request, context)


# ============================================================================
# Tool 2: create_material
# ============================================================================


class CreateMaterialRequest(BaseModel):
    """Request model for creating a material."""

    name: str = Field(..., description="Material name")
    sku: str = Field(..., description="SKU for the material variant")
    uom: str = Field(
        default="pcs", description="Unit of measure (e.g., pcs, kg, meters)"
    )
    category_name: str | None = Field(None, description="Category for grouping")
    is_sellable: bool = Field(False, description="Whether material can be sold")
    sales_price: float | None = Field(None, description="Sales price per unit")
    purchase_price: float | None = Field(None, description="Purchase cost per unit")
    default_supplier_id: int | None = Field(None, description="Default supplier ID")
    additional_info: str | None = Field(None, description="Additional notes")


class CreateMaterialResponse(BaseModel):
    """Response from creating a material."""

    id: int
    name: str
    sku: str
    success: bool = True
    message: str = "Material created successfully"


async def _create_material_impl(
    request: CreateMaterialRequest, context: Context
) -> CreateMaterialResponse:
    """Implementation of create_material tool.

    Args:
        request: Request with material details
        context: Server context with KatanaClient

    Returns:
        Created material details

    Raises:
        ValueError: If required fields are missing or invalid
        Exception: If API call fails
    """
    start_time = time.monotonic()
    logger.info(
        "material_create_started",
        name=request.name,
        sku=request.sku,
    )

    try:
        services = get_services(context)

        # Create variant request
        variant = CreateVariantRequest(
            sku=request.sku,
            sales_price=request.sales_price
            if request.sales_price is not None
            else UNSET,
            purchase_price=request.purchase_price
            if request.purchase_price is not None
            else UNSET,
        )

        # Create material request
        material_request = ApiCreateMaterialRequest(
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
            "material_create_completed",
            material_id=material.id,
            name=material.name,
            sku=request.sku,
            duration_ms=duration_ms,
        )

        return CreateMaterialResponse(
            id=material.id,
            name=material.name or "",
            sku=request.sku,
            message=f"Material '{material.name}' created successfully with SKU {request.sku}",
        )

    except Exception as e:
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.error(
            "material_create_failed",
            name=request.name,
            sku=request.sku,
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=duration_ms,
            exc_info=True,
        )
        raise


@unpack_pydantic_params
async def create_material(
    request: Annotated[CreateMaterialRequest, Unpack()], context: Context
) -> CreateMaterialResponse:
    """Create a new material in Katana.

    This tool creates a raw material or component used in manufacturing.
    Materials are items that typically cannot be sold directly but are used
    to produce finished products.

    Args:
        request: Request with material details
        context: Server context with KatanaClient

    Returns:
        Created material details including ID and SKU

    Example:
        Request: {
            "name": "Steel Rod",
            "sku": "MAT-STEEL-001",
            "uom": "kg",
            "is_sellable": false,
            "purchase_price": 5.99
        }
        Returns: {
            "id": 456,
            "name": "Steel Rod",
            "sku": "MAT-STEEL-001",
            "message": "Material 'Steel Rod' created successfully"
        }
    """
    return await _create_material_impl(request, context)


def register_tools(mcp: FastMCP) -> None:
    """Register all catalog tools with the FastMCP instance.

    Args:
        mcp: FastMCP server instance to register tools with
    """
    mcp.tool()(create_product)
    mcp.tool()(create_material)
