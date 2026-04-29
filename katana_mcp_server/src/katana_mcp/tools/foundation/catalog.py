"""Catalog management tools for Katana MCP Server.

Foundation tools for creating and managing products and materials in the catalog.
These are dedicated tools that simplify the more general create_item tool.
"""

from __future__ import annotations

import time
from typing import Annotated

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, Field

from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.tool_result_utils import UI_META, make_tool_result
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_mcp.web_urls import katana_web_url
from katana_public_api_client.domain.converters import to_unset
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
    type: str = "product"
    success: bool = True
    message: str = "Product created successfully"
    katana_url: str | None = None


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
            sales_price=to_unset(request.sales_price),
            purchase_price=to_unset(request.purchase_price),
        )

        # Create product request
        product_request = ApiCreateProductRequest(
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
            katana_url=katana_web_url("product", product.id),
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


@observe_tool
@unpack_pydantic_params
async def create_product(
    request: Annotated[CreateProductRequest, Unpack()], context: Context
) -> ToolResult:
    """Create a finished good product in the Katana catalog.

    PREFER this over create_item when creating products — simpler, dedicated parameters.
    Products are sellable items (finished goods). For raw materials and components,
    use create_material. Creates the product with a single variant.
    """
    from katana_mcp.tools.prefab_ui import build_item_mutation_ui

    response = await _create_product_impl(request, context)
    ui = build_item_mutation_ui(response.model_dump(), "Created")

    return make_tool_result(response, ui=ui)


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
    type: str = "material"
    success: bool = True
    message: str = "Material created successfully"
    katana_url: str | None = None


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
            sales_price=to_unset(request.sales_price),
            purchase_price=to_unset(request.purchase_price),
        )

        # Create material request
        material_request = ApiCreateMaterialRequest(
            name=request.name,
            uom=request.uom,
            category_name=to_unset(request.category_name),
            is_sellable=request.is_sellable,
            default_supplier_id=to_unset(request.default_supplier_id),
            additional_info=to_unset(request.additional_info),
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
            katana_url=katana_web_url("material", material.id),
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


@observe_tool
@unpack_pydantic_params
async def create_material(
    request: Annotated[CreateMaterialRequest, Unpack()], context: Context
) -> ToolResult:
    """Create a raw material or component in the Katana catalog.

    PREFER this over create_item when creating materials — simpler, dedicated parameters.
    Materials are items used in manufacturing (not typically sold directly).
    For finished goods, use create_product. Creates the material with a single variant.
    """
    from katana_mcp.tools.prefab_ui import build_item_mutation_ui

    response = await _create_material_impl(request, context)
    ui = build_item_mutation_ui(response.model_dump(), "Created")

    return make_tool_result(response, ui=ui)


def register_tools(mcp: FastMCP) -> None:
    """Register all catalog tools with the FastMCP instance.

    Args:
        mcp: FastMCP server instance to register tools with
    """
    from mcp.types import ToolAnnotations

    _write = ToolAnnotations(
        readOnlyHint=False, destructiveHint=False, openWorldHint=True
    )

    mcp.tool(tags={"catalog", "write"}, annotations=_write, meta=UI_META)(
        create_product
    )
    mcp.tool(tags={"catalog", "write"}, annotations=_write, meta=UI_META)(
        create_material
    )
