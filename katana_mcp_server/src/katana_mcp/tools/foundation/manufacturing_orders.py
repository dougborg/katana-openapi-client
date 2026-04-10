"""Manufacturing order management tools for Katana MCP Server.

Foundation tools for creating manufacturing orders to initiate production.

These tools provide:
- create_manufacturing_order: Create manufacturing orders with preview/confirm pattern
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastmcp import Context, FastMCP
from fastmcp.tools.tool import ToolResult
from pydantic import BaseModel, Field

from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.schemas import ConfirmationResult, require_confirmation
from katana_mcp.tools.tool_result_utils import make_tool_result
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.client_types import UNSET
from katana_public_api_client.domain.converters import to_unset, unwrap_unset
from katana_public_api_client.models import (
    CreateManufacturingOrderRequest as APICreateManufacturingOrderRequest,
    ManufacturingOrder,
)
from katana_public_api_client.utils import unwrap_as

logger = get_logger(__name__)

# ============================================================================
# Tool 1: create_manufacturing_order
# ============================================================================


class CreateManufacturingOrderRequest(BaseModel):
    """Request to create a manufacturing order."""

    variant_id: int = Field(..., description="Variant ID to manufacture")
    planned_quantity: float = Field(
        ..., description="Planned quantity to produce", gt=0
    )
    location_id: int = Field(..., description="Production location ID")
    order_created_date: datetime | None = Field(
        None, description="Order creation date (defaults to current time)"
    )
    production_deadline_date: datetime | None = Field(
        None, description="Production deadline date (optional)"
    )
    additional_info: str | None = Field(None, description="Additional notes (optional)")
    confirm: bool = Field(
        False, description="If false, returns preview. If true, creates order."
    )


class ManufacturingOrderResponse(BaseModel):
    """Response from creating a manufacturing order.

    Attributes:
        id: Manufacturing order ID (None in preview mode)
        order_no: Manufacturing order number
        variant_id: Variant ID to manufacture
        planned_quantity: Planned quantity to produce
        location_id: Production location ID
        status: Order status (e.g., "NOT_STARTED")
        order_created_date: Order creation timestamp
        production_deadline_date: Production deadline
        additional_info: Additional notes
        is_preview: True if preview mode, False if order created
        warnings: List of warnings (e.g., missing optional fields)
        next_actions: Suggested next steps
        message: Human-readable summary message
    """

    id: int | None = None
    order_no: str | None = None
    variant_id: int
    planned_quantity: float
    location_id: int
    status: str | None = None
    order_created_date: datetime | None = None
    production_deadline_date: datetime | None = None
    additional_info: str | None = None
    is_preview: bool
    warnings: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    message: str


async def _create_manufacturing_order_impl(
    request: CreateManufacturingOrderRequest, context: Context
) -> ManufacturingOrderResponse:
    """Implementation of create_manufacturing_order tool.

    Args:
        request: Request with manufacturing order details
        context: Server context with KatanaClient

    Returns:
        Manufacturing order response with details

    Raises:
        ValueError: If validation fails
        Exception: If API call fails
    """
    logger.info(
        f"{'Previewing' if not request.confirm else 'Creating'} manufacturing order for variant {request.variant_id}"
    )

    # Preview mode - just return details without API call
    if not request.confirm:
        logger.info(
            f"Preview mode: MO for variant {request.variant_id}, quantity {request.planned_quantity}"
        )

        # Generate warnings for missing optional fields
        warnings = []
        if request.production_deadline_date is None:
            warnings.append(
                "No production_deadline_date specified - order will have no deadline"
            )
        if request.additional_info is None:
            warnings.append(
                "No additional_info specified - consider adding notes for context"
            )

        return ManufacturingOrderResponse(
            variant_id=request.variant_id,
            planned_quantity=request.planned_quantity,
            location_id=request.location_id,
            order_created_date=request.order_created_date,
            production_deadline_date=request.production_deadline_date,
            additional_info=request.additional_info,
            is_preview=True,
            warnings=warnings,
            next_actions=[
                "Review the order details",
                "Set confirm=true to create the manufacturing order",
            ],
            message=f"Preview: Manufacturing order for variant {request.variant_id}, quantity {request.planned_quantity}",
        )

    # Confirm mode - use elicitation to get user confirmation before creating
    confirmation = await require_confirmation(
        context,
        f"Create manufacturing order for variant {request.variant_id} with quantity {request.planned_quantity}?",
    )

    if confirmation != ConfirmationResult.CONFIRMED:
        logger.info(
            f"User did not confirm creation of manufacturing order for variant {request.variant_id}"
        )
        return ManufacturingOrderResponse(
            variant_id=request.variant_id,
            planned_quantity=request.planned_quantity,
            location_id=request.location_id,
            order_created_date=request.order_created_date,
            production_deadline_date=request.production_deadline_date,
            additional_info=request.additional_info,
            is_preview=True,
            message=f"Manufacturing order creation {confirmation} by user",
            next_actions=["Review the order details and try again with confirm=true"],
        )

    # User confirmed - create the manufacturing order via API
    try:
        services = get_services(context)

        # Build API request
        api_request = APICreateManufacturingOrderRequest(
            variant_id=request.variant_id,
            planned_quantity=request.planned_quantity,
            location_id=request.location_id,
            order_created_date=to_unset(request.order_created_date),
            production_deadline_date=to_unset(request.production_deadline_date),
            additional_info=to_unset(request.additional_info),
        )

        # Call API
        from katana_public_api_client.api.manufacturing_order import (
            create_manufacturing_order as api_create_manufacturing_order,
        )

        response = await api_create_manufacturing_order.asyncio_detailed(
            client=services.client, body=api_request
        )

        # unwrap_as() raises typed exceptions on error, returns typed ManufacturingOrder
        mo = unwrap_as(response, ManufacturingOrder)
        logger.info(f"Successfully created manufacturing order ID {mo.id}")

        # Extract values using unwrap_unset for clean UNSET handling
        order_no = unwrap_unset(mo.order_no, None)
        variant_id = unwrap_unset(mo.variant_id, request.variant_id)
        planned_quantity = unwrap_unset(mo.planned_quantity, request.planned_quantity)
        location_id = unwrap_unset(mo.location_id, request.location_id)
        order_created_date = unwrap_unset(mo.order_created_date, None)
        production_deadline_date = unwrap_unset(mo.production_deadline_date, None)
        additional_info = unwrap_unset(mo.additional_info, None)
        mo_status = unwrap_unset(mo.status, None)
        status = mo_status.value if mo_status else None

        return ManufacturingOrderResponse(
            id=mo.id,
            order_no=order_no,
            variant_id=variant_id,
            planned_quantity=planned_quantity,
            location_id=location_id,
            status=status,
            order_created_date=order_created_date,
            production_deadline_date=production_deadline_date,
            additional_info=additional_info,
            is_preview=False,
            next_actions=[
                f"Manufacturing order created with ID {mo.id}",
                "Use production tools to track and complete the order",
            ],
            message=f"Successfully created manufacturing order {order_no or mo.id} (ID: {mo.id})",
        )

    except Exception as e:
        logger.error(f"Failed to create manufacturing order: {e}")
        raise


@observe_tool
@unpack_pydantic_params
async def create_manufacturing_order(
    request: Annotated[CreateManufacturingOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Create a manufacturing order to produce items.

    Two-step flow: confirm=false to preview, confirm=true to create (prompts
    for confirmation). Requires variant_id of the product to manufacture,
    planned_quantity, and location_id. Recipe and operation rows are created
    automatically from the product's recipe. Use search_items to find variant IDs.
    """
    from katana_mcp.tools.prefab_ui import (
        build_order_created_ui,
        build_order_preview_ui,
    )

    response = await _create_manufacturing_order_impl(request, context)

    next_actions_text = "\n".join(f"- {a}" for a in response.next_actions) or "None"

    order_dict = response.model_dump()
    if response.is_preview:
        ui = build_order_preview_ui(order_dict, "Manufacturing Order")
    else:
        ui = build_order_created_ui(order_dict, "Manufacturing Order")

    return make_tool_result(
        response,
        "manufacturing_order_created",
        ui=ui,
        id=response.id or "N/A",
        order_no=response.order_no or "N/A",
        variant_id=response.variant_id,
        planned_quantity=response.planned_quantity,
        location_id=response.location_id,
        status=response.status or ("PREVIEW" if response.is_preview else "N/A"),
        message=response.message,
        next_actions_text=next_actions_text,
    )


# ============================================================================
# Tool 2: get_manufacturing_order
# ============================================================================


class GetManufacturingOrderRequest(BaseModel):
    """Request to look up manufacturing orders."""

    order_no: str | None = Field(
        default=None, description="Order number to look up (e.g., '#WEB20082 / 1')"
    )
    order_id: int | None = Field(default=None, description="Manufacturing order ID")


class ManufacturingOrderInfo(BaseModel):
    """Manufacturing order details."""

    id: int
    order_no: str | None
    status: str | None
    variant_id: int | None
    planned_quantity: float | None
    actual_quantity: float | None
    location_id: int | None
    order_created_date: str | None
    production_deadline_date: str | None
    done_date: str | None
    is_linked_to_sales_order: bool | None
    sales_order_id: int | None
    ingredient_availability: str | None
    total_cost: float | None
    material_cost: float | None
    operations_cost: float | None
    additional_info: str | None


class GetManufacturingOrderResponse(BaseModel):
    """Response containing manufacturing orders."""

    orders: list[ManufacturingOrderInfo]
    total_count: int


async def _get_manufacturing_order_impl(
    request: GetManufacturingOrderRequest, context: Context
) -> GetManufacturingOrderResponse:
    """Look up manufacturing orders by order number or ID."""
    from katana_public_api_client.api.manufacturing_order import (
        get_all_manufacturing_orders,
    )
    from katana_public_api_client.utils import unwrap_data

    if not request.order_no and not request.order_id:
        raise ValueError("Either order_no or order_id must be provided")

    services = get_services(context)

    kwargs: dict = {"client": services.client, "limit": 50}
    if request.order_id:
        kwargs["ids"] = [request.order_id]
    if request.order_no:
        kwargs["order_no"] = request.order_no

    response = await get_all_manufacturing_orders.asyncio_detailed(**kwargs)
    attrs_list = unwrap_data(response)

    orders = [
        ManufacturingOrderInfo(
            id=mo.id,
            order_no=unwrap_unset(mo.order_no, None),
            status=unwrap_unset(mo.status, None),
            variant_id=unwrap_unset(mo.variant_id, None),
            planned_quantity=unwrap_unset(mo.planned_quantity, None),
            actual_quantity=unwrap_unset(mo.actual_quantity, None),
            location_id=unwrap_unset(mo.location_id, None),
            order_created_date=mo.order_created_date.isoformat()
            if not isinstance(mo.order_created_date, type(UNSET))
            and mo.order_created_date
            else None,
            production_deadline_date=mo.production_deadline_date.isoformat()
            if not isinstance(mo.production_deadline_date, type(UNSET))
            and mo.production_deadline_date
            else None,
            done_date=mo.done_date.isoformat()
            if not isinstance(mo.done_date, type(UNSET)) and mo.done_date
            else None,
            is_linked_to_sales_order=unwrap_unset(mo.is_linked_to_sales_order, None),
            sales_order_id=unwrap_unset(mo.sales_order_id, None),
            ingredient_availability=unwrap_unset(mo.ingredient_availability, None),
            total_cost=unwrap_unset(mo.total_cost, None),
            material_cost=unwrap_unset(mo.material_cost, None),
            operations_cost=unwrap_unset(mo.operations_cost, None),
            additional_info=unwrap_unset(mo.additional_info, None),
        )
        for mo in attrs_list
    ]

    return GetManufacturingOrderResponse(orders=orders, total_count=len(orders))


@observe_tool
@unpack_pydantic_params
async def get_manufacturing_order(
    request: Annotated[GetManufacturingOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Look up manufacturing orders by order number or ID.

    Returns order details including status, quantities, costs, linked sales order,
    and production timeline. Use to investigate production issues or track order progress.

    Provide either order_no (e.g., '#WEB20082 / 1') or order_id.
    """
    from katana_mcp.tools.tool_result_utils import make_simple_result

    response = await _get_manufacturing_order_impl(request, context)

    if not response.orders:
        return make_simple_result(
            f"No manufacturing orders found for "
            f"{'order_no=' + request.order_no if request.order_no else 'order_id=' + str(request.order_id)}",
            structured_data=response.model_dump(),
        )

    # Build markdown summary
    lines = []
    for o in response.orders:
        lines.append(f"## MO {o.order_no or o.id}")
        lines.append(f"- **Status**: {o.status}")
        lines.append(f"- **Variant ID**: {o.variant_id}")
        lines.append(
            f"- **Quantity**: {o.actual_quantity or 0} / {o.planned_quantity} planned"
        )
        if o.is_linked_to_sales_order:
            lines.append(f"- **Sales Order ID**: {o.sales_order_id}")
        if o.total_cost is not None:
            lines.append(f"- **Total Cost**: ${o.total_cost:,.2f}")
        if o.production_deadline_date:
            lines.append(f"- **Deadline**: {o.production_deadline_date}")
        if o.done_date:
            lines.append(f"- **Completed**: {o.done_date}")
        if o.additional_info:
            lines.append(f"- **Notes**: {o.additional_info}")
        lines.append("")

    return make_simple_result(
        "\n".join(lines),
        structured_data=response.model_dump(),
    )


# ============================================================================
# Tool 3: get_manufacturing_order_recipe
# ============================================================================


class GetManufacturingOrderRecipeRequest(BaseModel):
    """Request to list ingredient rows for a manufacturing order."""

    manufacturing_order_id: int = Field(..., description="Manufacturing order ID")


class RecipeRowInfo(BaseModel):
    """Summary of a manufacturing order recipe row (ingredient)."""

    id: int
    variant_id: int | None
    sku: str | None
    planned_quantity_per_unit: float | None
    total_actual_quantity: float | None
    ingredient_availability: str | None
    notes: str | None
    cost: float | None


class GetManufacturingOrderRecipeResponse(BaseModel):
    """Response containing recipe rows for an MO."""

    manufacturing_order_id: int
    rows: list[RecipeRowInfo]
    total_count: int


async def _get_manufacturing_order_recipe_impl(
    request: GetManufacturingOrderRecipeRequest, context: Context
) -> GetManufacturingOrderRecipeResponse:
    """Read the ingredient rows for a manufacturing order."""
    from katana_public_api_client.api.manufacturing_order_recipe import (
        get_all_manufacturing_order_recipe_rows,
    )
    from katana_public_api_client.utils import unwrap_data

    services = get_services(context)

    response = await get_all_manufacturing_order_recipe_rows.asyncio_detailed(
        client=services.client,
        manufacturing_order_id=request.manufacturing_order_id,
    )
    raw_rows = unwrap_data(response, default=[])

    # Enrich each row with the variant SKU from the cache
    rows: list[RecipeRowInfo] = []
    for row in raw_rows:
        variant_id = unwrap_unset(row.variant_id, None)
        sku: str | None = None
        if variant_id is not None:
            variant = await services.cache.get_by_id("variant", variant_id)
            if variant:
                sku = variant.get("sku")

        rows.append(
            RecipeRowInfo(
                id=row.id,
                variant_id=variant_id,
                sku=sku,
                planned_quantity_per_unit=unwrap_unset(
                    row.planned_quantity_per_unit, None
                ),
                total_actual_quantity=unwrap_unset(row.total_actual_quantity, None),
                ingredient_availability=unwrap_unset(row.ingredient_availability, None),
                notes=unwrap_unset(row.notes, None),
                cost=unwrap_unset(row.cost, None),
            )
        )

    return GetManufacturingOrderRecipeResponse(
        manufacturing_order_id=request.manufacturing_order_id,
        rows=rows,
        total_count=len(rows),
    )


@observe_tool
@unpack_pydantic_params
async def get_manufacturing_order_recipe(
    request: Annotated[GetManufacturingOrderRecipeRequest, Unpack()],
    context: Context,
) -> ToolResult:
    """List the ingredient (recipe) rows for a manufacturing order.

    Returns each row with its ID, variant ID, SKU, planned quantity per unit,
    ingredient availability, and cost. Use this before adding or deleting
    recipe rows so you can identify the rows to modify.
    """
    from katana_mcp.tools.tool_result_utils import make_simple_result

    response = await _get_manufacturing_order_recipe_impl(request, context)

    if not response.rows:
        md = f"No recipe rows found for MO ID {response.manufacturing_order_id}."
    else:
        lines = [
            f"## Recipe for MO {response.manufacturing_order_id}",
            f"{response.total_count} ingredient rows",
            "",
            "| Row ID | Variant ID | SKU | Qty/Unit | Availability |",
            "|--------|-----------|-----|----------|--------------|",
        ]
        for r in response.rows:
            lines.append(
                f"| {r.id} | {r.variant_id} | {r.sku or 'N/A'} | "
                f"{r.planned_quantity_per_unit} | {r.ingredient_availability or 'N/A'} |"
            )
        md = "\n".join(lines)

    return make_simple_result(md, structured_data=response.model_dump())


# ============================================================================
# Tool 4: add_manufacturing_order_recipe_row
# ============================================================================


class AddRecipeRowRequest(BaseModel):
    """Request to add an ingredient row to a manufacturing order."""

    manufacturing_order_id: int = Field(..., description="Manufacturing order ID")
    sku: str | None = Field(
        default=None,
        description="SKU of the variant to add (resolved via cache). Use this OR variant_id.",
    )
    variant_id: int | None = Field(
        default=None,
        description="Variant ID to add directly. Use when the SKU isn't in the cache.",
    )
    planned_quantity_per_unit: float = Field(
        ..., description="Planned quantity needed per manufactured unit", gt=0
    )
    notes: str | None = Field(default=None, description="Optional notes")
    confirm: bool = Field(
        default=False,
        description="Set false to preview, true to add (prompts for confirmation)",
    )


class AddRecipeRowResponse(BaseModel):
    """Response from adding a recipe row."""

    id: int | None
    manufacturing_order_id: int
    variant_id: int
    sku: str | None
    planned_quantity_per_unit: float
    is_preview: bool
    message: str


async def _add_recipe_row_impl(
    request: AddRecipeRowRequest, context: Context
) -> AddRecipeRowResponse:
    """Add a new ingredient row to a manufacturing order."""
    from katana_public_api_client.api.manufacturing_order_recipe import (
        create_manufacturing_order_recipe_rows,
    )
    from katana_public_api_client.models.create_manufacturing_order_recipe_row_request import (
        CreateManufacturingOrderRecipeRowRequest,
    )
    from katana_public_api_client.utils import APIError, unwrap

    if not request.sku and not request.variant_id:
        raise ValueError("Either sku or variant_id must be provided")

    services = get_services(context)

    # Resolve variant_id — either from SKU via cache, or use directly
    if request.variant_id:
        variant_id = request.variant_id
        sku = request.sku  # may be None
        display_name = sku or f"variant {variant_id}"
    else:
        variant = await services.cache.get_by_sku(sku=request.sku)
        if not variant:
            raise ValueError(f"SKU '{request.sku}' not found")
        variant_id = variant["id"]
        sku = request.sku
        display_name = variant.get("display_name") or sku

    if not request.confirm:
        return AddRecipeRowResponse(
            id=None,
            manufacturing_order_id=request.manufacturing_order_id,
            variant_id=variant_id,
            sku=sku,
            planned_quantity_per_unit=request.planned_quantity_per_unit,
            is_preview=True,
            message=(
                f"Preview: Would add {request.planned_quantity_per_unit}x "
                f"{display_name} to MO {request.manufacturing_order_id}"
            ),
        )

    confirmation = await require_confirmation(
        context,
        f"Add {request.planned_quantity_per_unit}x {display_name} "
        f"to MO {request.manufacturing_order_id}?",
    )
    if confirmation != ConfirmationResult.CONFIRMED:
        return AddRecipeRowResponse(
            id=None,
            manufacturing_order_id=request.manufacturing_order_id,
            variant_id=variant_id,
            sku=sku,
            planned_quantity_per_unit=request.planned_quantity_per_unit,
            is_preview=True,
            message=f"Add recipe row {confirmation} by user",
        )

    api_request = CreateManufacturingOrderRecipeRowRequest(
        manufacturing_order_id=request.manufacturing_order_id,
        variant_id=variant_id,
        planned_quantity_per_unit=request.planned_quantity_per_unit,
        notes=to_unset(request.notes),
    )

    response = await create_manufacturing_order_recipe_rows.asyncio_detailed(
        client=services.client, body=api_request
    )
    try:
        result = unwrap(response)
    except APIError as e:
        raise ValueError(str(e)) from e

    new_id = getattr(result, "id", None) if result else None
    return AddRecipeRowResponse(
        id=new_id,
        manufacturing_order_id=request.manufacturing_order_id,
        variant_id=variant_id,
        sku=sku,
        planned_quantity_per_unit=request.planned_quantity_per_unit,
        is_preview=False,
        message=f"Added recipe row (ID {new_id}) to MO {request.manufacturing_order_id}",
    )


@observe_tool
@unpack_pydantic_params
async def add_manufacturing_order_recipe_row(
    request: Annotated[AddRecipeRowRequest, Unpack()], context: Context
) -> ToolResult:
    """Add a new ingredient row to a manufacturing order's recipe.

    Two-step flow: confirm=false to preview, confirm=true to add (prompts
    for confirmation). Provide either `sku` (resolved to variant_id via the
    cache) or `variant_id` directly.

    Use this to add missing ingredients to an MO or build up a custom recipe.
    To remove an ingredient, use delete_manufacturing_order_recipe_row.
    """
    from katana_mcp.tools.tool_result_utils import make_simple_result

    response = await _add_recipe_row_impl(request, context)
    status = "PREVIEW" if response.is_preview else "ADDED"
    md = f"## Recipe Row ({status})\n\n{response.message}"
    return make_simple_result(md, structured_data=response.model_dump())


# ============================================================================
# Tool 5: delete_manufacturing_order_recipe_row
# ============================================================================


class DeleteRecipeRowRequest(BaseModel):
    """Request to delete an ingredient row from a manufacturing order."""

    recipe_row_id: int = Field(..., description="Recipe row ID to delete")
    confirm: bool = Field(
        default=False,
        description="Set false to preview, true to delete (prompts for confirmation)",
    )


class DeleteRecipeRowResponse(BaseModel):
    """Response from deleting a recipe row."""

    recipe_row_id: int
    is_preview: bool
    message: str


async def _delete_recipe_row_impl(
    request: DeleteRecipeRowRequest, context: Context
) -> DeleteRecipeRowResponse:
    """Delete an ingredient row from a manufacturing order."""
    from katana_public_api_client.api.manufacturing_order_recipe import (
        delete_manufacturing_order_recipe_row,
    )
    from katana_public_api_client.utils import APIError, is_success, unwrap

    services = get_services(context)

    if not request.confirm:
        return DeleteRecipeRowResponse(
            recipe_row_id=request.recipe_row_id,
            is_preview=True,
            message=f"Preview: Would delete recipe row {request.recipe_row_id}",
        )

    confirmation = await require_confirmation(
        context,
        f"Delete recipe row {request.recipe_row_id}? This cannot be undone.",
    )
    if confirmation != ConfirmationResult.CONFIRMED:
        return DeleteRecipeRowResponse(
            recipe_row_id=request.recipe_row_id,
            is_preview=True,
            message=f"Delete recipe row {confirmation} by user",
        )

    response = await delete_manufacturing_order_recipe_row.asyncio_detailed(
        client=services.client, id=request.recipe_row_id
    )

    if not is_success(response):
        try:
            unwrap(response)
        except APIError as e:
            raise ValueError(str(e)) from e
        raise ValueError(f"Failed to delete recipe row {request.recipe_row_id}")

    return DeleteRecipeRowResponse(
        recipe_row_id=request.recipe_row_id,
        is_preview=False,
        message=f"Deleted recipe row {request.recipe_row_id}",
    )


@observe_tool
@unpack_pydantic_params
async def delete_manufacturing_order_recipe_row(
    request: Annotated[DeleteRecipeRowRequest, Unpack()], context: Context
) -> ToolResult:
    """Delete an ingredient row from a manufacturing order's recipe.

    Two-step flow: confirm=false to preview, confirm=true to delete (prompts
    for confirmation). Find the recipe_row_id with get_manufacturing_order_recipe.

    Use with add_manufacturing_order_recipe_row to replace an ingredient.
    """
    from katana_mcp.tools.tool_result_utils import make_simple_result

    response = await _delete_recipe_row_impl(request, context)
    status = "PREVIEW" if response.is_preview else "DELETED"
    md = f"## Recipe Row ({status})\n\n{response.message}"
    return make_simple_result(md, structured_data=response.model_dump())


def register_tools(mcp: FastMCP) -> None:
    """Register all manufacturing order tools with the FastMCP instance.

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
    _destructive_write = ToolAnnotations(
        readOnlyHint=False, destructiveHint=True, openWorldHint=True
    )

    mcp.tool(
        tags={"orders", "manufacturing", "write"},
        annotations=_write,
    )(create_manufacturing_order)
    mcp.tool(
        tags={"orders", "manufacturing", "read"},
        annotations=_read,
    )(get_manufacturing_order)
    mcp.tool(
        tags={"orders", "manufacturing", "read"},
        annotations=_read,
    )(get_manufacturing_order_recipe)
    mcp.tool(
        tags={"orders", "manufacturing", "write"},
        annotations=_write,
    )(add_manufacturing_order_recipe_row)
    mcp.tool(
        tags={"orders", "manufacturing", "write"},
        annotations=_destructive_write,
    )(delete_manufacturing_order_recipe_row)
