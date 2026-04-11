"""Manufacturing order management tools for Katana MCP Server.

Foundation tools for creating manufacturing orders to initiate production.

These tools provide:
- create_manufacturing_order: Create manufacturing orders with preview/confirm pattern
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, Field

from katana_mcp.cache import EntityType
from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.schemas import ConfirmationResult, require_confirmation
from katana_mcp.tools.tool_result_utils import format_md_table, make_tool_result
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.client_types import UNSET
from katana_public_api_client.domain.converters import to_unset, unwrap_unset
from katana_public_api_client.models import (
    CreateManufacturingOrderRequest as APICreateManufacturingOrderRequest,
    ManufacturingOrder,
)
from katana_public_api_client.utils import unwrap_as

logger = get_logger(__name__)


async def _none_coro() -> None:
    """Helper coroutine returning None for asyncio.gather placeholder slots."""
    return None


# ============================================================================
# Tool 1: create_manufacturing_order
# ============================================================================


class CreateManufacturingOrderRequest(BaseModel):
    """Request to create a manufacturing order.

    Two modes:
    - **Standalone**: Provide variant_id, planned_quantity, location_id. Creates
      an MO not linked to any sales order.
    - **Make-to-order (linked)**: Provide sales_order_row_id. Creates an MO
      directly linked to the sales order row. variant_id, planned_quantity, and
      location_id are inferred from the sales order row; passing them explicitly
      is optional and will be ignored by the API.
    """

    variant_id: int | None = Field(
        None,
        description="Variant ID to manufacture (required for standalone MOs)",
    )
    planned_quantity: float | None = Field(
        None,
        description="Planned quantity (required for standalone MOs)",
        gt=0,
    )
    location_id: int | None = Field(
        None, description="Production location ID (required for standalone MOs)"
    )
    sales_order_row_id: int | None = Field(
        None,
        description="Sales order row ID — when provided, creates a make-to-order "
        "MO linked to that sales order row (uses /manufacturing_order_make_to_order).",
    )
    create_subassemblies: bool = Field(
        default=False,
        description="Make-to-order only: also create MOs for subassemblies. Ignored for standalone MOs.",
    )
    order_created_date: datetime | None = Field(
        None, description="Order creation date (standalone mode only)"
    )
    production_deadline_date: datetime | None = Field(
        None, description="Production deadline date (standalone mode only)"
    )
    additional_info: str | None = Field(
        None, description="Additional notes (standalone mode only)"
    )
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

    Branches based on whether `sales_order_row_id` is provided:
    - Provided → make-to-order endpoint (linked to the sales order)
    - Not provided → standard create endpoint (standalone MO)
    """
    # Validate input based on mode
    is_make_to_order = request.sales_order_row_id is not None
    if not is_make_to_order:
        missing = [
            name
            for name, val in [
                ("variant_id", request.variant_id),
                ("planned_quantity", request.planned_quantity),
                ("location_id", request.location_id),
            ]
            if val is None
        ]
        if missing:
            raise ValueError(
                f"Standalone MO creation requires: {', '.join(missing)}. "
                "Alternatively, provide sales_order_row_id for a make-to-order linked MO."
            )

    logger.info(
        f"{'Previewing' if not request.confirm else 'Creating'} manufacturing order "
        f"({'make-to-order' if is_make_to_order else 'standalone'})"
    )

    # Preview mode — return the plan without calling the API
    if not request.confirm:
        if is_make_to_order:
            preview_msg = (
                f"Preview: Make-to-order MO from sales_order_row_id="
                f"{request.sales_order_row_id}"
                + (" (with subassemblies)" if request.create_subassemblies else "")
            )
        else:
            preview_msg = (
                f"Preview: Manufacturing order for variant {request.variant_id}, "
                f"quantity {request.planned_quantity}"
            )

        warnings = []
        if not is_make_to_order:
            if request.production_deadline_date is None:
                warnings.append(
                    "No production_deadline_date specified - order will have no deadline"
                )
            if request.additional_info is None:
                warnings.append(
                    "No additional_info specified - consider adding notes for context"
                )

        return ManufacturingOrderResponse(
            variant_id=request.variant_id or 0,
            planned_quantity=request.planned_quantity or 0,
            location_id=request.location_id or 0,
            order_created_date=request.order_created_date,
            production_deadline_date=request.production_deadline_date,
            additional_info=request.additional_info,
            is_preview=True,
            warnings=warnings,
            next_actions=[
                "Review the order details",
                "Set confirm=true to create the manufacturing order",
            ],
            message=preview_msg,
        )

    # Confirm mode — elicit confirmation
    confirm_msg = (
        f"Create make-to-order MO from sales_order_row_id={request.sales_order_row_id}?"
        if is_make_to_order
        else (
            f"Create manufacturing order for variant {request.variant_id} "
            f"with quantity {request.planned_quantity}?"
        )
    )
    confirmation = await require_confirmation(context, confirm_msg)

    if confirmation != ConfirmationResult.CONFIRMED:
        return ManufacturingOrderResponse(
            variant_id=request.variant_id or 0,
            planned_quantity=request.planned_quantity or 0,
            location_id=request.location_id or 0,
            order_created_date=request.order_created_date,
            production_deadline_date=request.production_deadline_date,
            additional_info=request.additional_info,
            is_preview=True,
            message=f"Manufacturing order creation {confirmation} by user",
            next_actions=["Review the order details and try again with confirm=true"],
        )

    # Execute
    try:
        services = get_services(context)

        if is_make_to_order:
            from katana_public_api_client.api.manufacturing_order import (
                make_to_order_manufacturing_order as api_mto,
            )
            from katana_public_api_client.models.make_to_order_manufacturing_order_request import (
                MakeToOrderManufacturingOrderRequest,
            )

            mto_request = MakeToOrderManufacturingOrderRequest(
                sales_order_row_id=request.sales_order_row_id,
                create_subassemblies=request.create_subassemblies,
            )
            response = await api_mto.asyncio_detailed(
                client=services.client, body=mto_request
            )
        else:
            api_request = APICreateManufacturingOrderRequest(
                variant_id=request.variant_id,
                planned_quantity=request.planned_quantity,
                location_id=request.location_id,
                order_created_date=to_unset(request.order_created_date),
                production_deadline_date=to_unset(request.production_deadline_date),
                additional_info=to_unset(request.additional_info),
            )

            from katana_public_api_client.api.manufacturing_order import (
                create_manufacturing_order as api_create_manufacturing_order,
            )

            response = await api_create_manufacturing_order.asyncio_detailed(
                client=services.client, body=api_request
            )

        mo = unwrap_as(response, ManufacturingOrder)
        logger.info(f"Successfully created manufacturing order ID {mo.id}")

        order_no = unwrap_unset(mo.order_no, None)
        variant_id = unwrap_unset(mo.variant_id, request.variant_id or 0)
        planned_quantity = unwrap_unset(
            mo.planned_quantity, request.planned_quantity or 0
        )
        location_id = unwrap_unset(mo.location_id, request.location_id or 0)
        order_created_date = unwrap_unset(mo.order_created_date, None)
        production_deadline_date = unwrap_unset(mo.production_deadline_date, None)
        additional_info = unwrap_unset(mo.additional_info, None)
        mo_status = unwrap_unset(mo.status, None)
        status = mo_status.value if mo_status else None

        next_actions = [
            f"Manufacturing order created with ID {mo.id}",
        ]
        if is_make_to_order:
            next_actions.append(
                f"Linked to sales order (sales_order_id={unwrap_unset(mo.sales_order_id, 'N/A')})"
            )
        next_actions.append("Use production tools to track and complete the order")

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
            next_actions=next_actions,
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

    Two modes:

    **Standalone MO** (not linked to a sales order):
    Provide `variant_id`, `planned_quantity`, and `location_id`. Recipe and
    operation rows are copied from the product's recipe.

    **Make-to-order MO** (linked to a sales order row):
    Provide `sales_order_row_id`. Everything else (variant, quantity, location)
    is inferred from the sales order row. Optionally set `create_subassemblies=true`
    to also create MOs for subassemblies. This is what you want when processing
    a new sales order that needs production.

    Two-step flow: confirm=false to preview, confirm=true to create (prompts
    for confirmation).
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

    # Parallelize variant lookups across all rows (N+1 fix)
    variant_ids_raw = [unwrap_unset(row.variant_id, None) for row in raw_rows]
    variants = await asyncio.gather(
        *(
            services.cache.get_by_id(EntityType.VARIANT, v_id)
            if v_id is not None
            else _none_coro()
            for v_id in variant_ids_raw
        )
    )

    rows: list[RecipeRowInfo] = []
    for row, variant in zip(raw_rows, variants, strict=True):
        variant_id = unwrap_unset(row.variant_id, None)
        sku = variant.get("sku") if variant else None

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
        table = format_md_table(
            headers=["Row ID", "Variant ID", "SKU", "Qty/Unit", "Availability"],
            rows=[
                [
                    r.id,
                    r.variant_id,
                    r.sku or "N/A",
                    r.planned_quantity_per_unit,
                    r.ingredient_availability or "N/A",
                ]
                for r in response.rows
            ],
        )
        md = (
            f"## Recipe for MO {response.manufacturing_order_id}\n"
            f"{response.total_count} ingredient rows\n\n{table}"
        )

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


# ----- Low-level API helpers (shared by single-row and batch tools) -----


async def _api_create_recipe_row(
    services: Any,
    *,
    manufacturing_order_id: int,
    variant_id: int,
    planned_quantity_per_unit: float,
    notes: str | None,
) -> Any:
    """Raw API call to create a recipe row. Raises ValueError on API failure."""
    from katana_public_api_client.api.manufacturing_order_recipe import (
        create_manufacturing_order_recipe_rows,
    )
    from katana_public_api_client.models.create_manufacturing_order_recipe_row_request import (
        CreateManufacturingOrderRecipeRowRequest,
    )
    from katana_public_api_client.utils import APIError, unwrap

    api_request = CreateManufacturingOrderRecipeRowRequest(
        manufacturing_order_id=manufacturing_order_id,
        variant_id=variant_id,
        planned_quantity_per_unit=planned_quantity_per_unit,
        notes=to_unset(notes),
    )

    response = await create_manufacturing_order_recipe_rows.asyncio_detailed(
        client=services.client, body=api_request
    )
    try:
        return unwrap(response)
    except APIError as e:
        raise ValueError(str(e)) from e


async def _api_delete_recipe_row(services: Any, recipe_row_id: int) -> None:
    """Raw API call to delete a recipe row. Raises ValueError on API failure."""
    from katana_public_api_client.api.manufacturing_order_recipe import (
        delete_manufacturing_order_recipe_row as api_delete,
    )
    from katana_public_api_client.utils import APIError, is_success, unwrap

    response = await api_delete.asyncio_detailed(
        client=services.client, id=recipe_row_id
    )
    if is_success(response):
        return
    try:
        unwrap(response)
    except APIError as e:
        raise ValueError(str(e)) from e
    raise ValueError(f"Failed to delete recipe row {recipe_row_id}")


async def _resolve_variant_ref(
    services: Any, *, sku: str | None, variant_id: int | None
) -> tuple[int, str | None, str]:
    """Resolve a (sku, variant_id) pair to (variant_id, sku, display_name).

    Exactly one of sku/variant_id must be provided. Raises ValueError if the
    SKU is not in the cache.
    """
    if variant_id is not None:
        return variant_id, sku, sku or f"variant {variant_id}"
    if not sku:
        raise ValueError("Either sku or variant_id must be provided")
    variant = await services.cache.get_by_sku(sku=sku)
    if not variant:
        raise ValueError(f"SKU '{sku}' not found")
    return variant["id"], sku, variant.get("display_name") or sku


async def _add_recipe_row_impl(
    request: AddRecipeRowRequest, context: Context
) -> AddRecipeRowResponse:
    """Add a new ingredient row to a manufacturing order."""
    if not request.sku and not request.variant_id:
        raise ValueError("Either sku or variant_id must be provided")

    services = get_services(context)
    variant_id, sku, display_name = await _resolve_variant_ref(
        services, sku=request.sku, variant_id=request.variant_id
    )

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

    result = await _api_create_recipe_row(
        services,
        manufacturing_order_id=request.manufacturing_order_id,
        variant_id=variant_id,
        planned_quantity_per_unit=request.planned_quantity_per_unit,
        notes=request.notes,
    )
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

    await _api_delete_recipe_row(services, request.recipe_row_id)

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


# ============================================================================
# Tool 6: batch_update_manufacturing_order_recipes
# ============================================================================


MAX_BATCH_OPS = 100


class VariantSpec(BaseModel):
    """A variant reference plus the planned quantity per manufactured unit."""

    sku: str | None = Field(default=None, description="SKU of the variant")
    variant_id: int | None = Field(
        default=None, description="Variant ID (used directly if set)"
    )
    planned_quantity_per_unit: float = Field(
        ..., gt=0, description="Qty per manufactured unit"
    )
    notes: str | None = Field(default=None, description="Optional recipe row notes")


class VariantReplacement(BaseModel):
    """Replace a variant across multiple MOs with one or more new components."""

    manufacturing_order_ids: list[int] = Field(..., min_length=1)
    old_sku: str | None = Field(
        default=None, description="SKU of the variant to remove"
    )
    old_variant_id: int | None = Field(
        default=None, description="Variant ID to remove (alternative to old_sku)"
    )
    new_components: list[VariantSpec] = Field(
        default_factory=list,
        description="Replacement components to add. Empty list = pure removal.",
    )
    strict: bool = Field(
        default=False,
        description="If true, missing old variant in any MO is an error. "
        "If false (default), missing is a skipped warning.",
    )


class ExplicitChange(BaseModel):
    """Explicit per-MO list of row deletions and additions."""

    manufacturing_order_id: int
    remove_row_ids: list[int] = Field(default_factory=list)
    add_variants: list[VariantSpec] = Field(default_factory=list)


class BatchUpdateRecipesRequest(BaseModel):
    """Batch update recipe rows across one or more manufacturing orders."""

    replacements: list[VariantReplacement] = Field(default_factory=list)
    changes: list[ExplicitChange] = Field(default_factory=list)
    continue_on_error: bool = Field(
        default=True,
        description="If true, log and continue past failed sub-operations. "
        "If false, abort on the first failure.",
    )
    confirm: bool = Field(
        default=False,
        description="Set false to preview, true to execute (single confirmation for batch)",
    )


class SubOpStatus(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class OpType(StrEnum):
    """Sub-operation type within a batch recipe update."""

    DELETE = "delete"
    ADD = "add"


class SubOpResult(BaseModel):
    """Result of a single delete or add within the batch."""

    op_type: OpType
    manufacturing_order_id: int
    recipe_row_id: int | None = None  # existing row (delete) or new row (add result)
    variant_id: int | None = None
    sku: str | None = None
    planned_quantity_per_unit: float | None = None
    status: SubOpStatus = SubOpStatus.PENDING
    error: str | None = None
    group_label: str | None = None


class BatchUpdateRecipesResponse(BaseModel):
    is_preview: bool
    total_ops: int
    success_count: int
    failed_count: int
    skipped_count: int
    results: list[SubOpResult]
    warnings: list[str] = Field(default_factory=list)
    message: str


def _format_group_label(
    old_sku: str | None, old_variant_id: int, new_components: list[VariantSpec]
) -> str:
    """Build a human-readable label for a replacement group."""
    old_label = old_sku or f"variant {old_variant_id}"
    new_labels = [c.sku or f"variant {c.variant_id}" for c in new_components]
    if not new_labels:
        return f"Remove {old_label}"
    return f"{old_label} → [{', '.join(new_labels)}]"


async def _plan_batch_update(
    request: BatchUpdateRecipesRequest, context: Context
) -> tuple[list[SubOpResult], list[str]]:
    """Resolve intent into a concrete, ordered sub-operation plan."""
    services = get_services(context)
    planned: list[SubOpResult] = []
    warnings: list[str] = []

    # Cache recipe fetches within this plan phase — if multiple replacements
    # target the same MO, we only fetch its recipe once.
    recipe_cache: dict[int, GetManufacturingOrderRecipeResponse] = {}

    async def _get_cached_recipe(mo_id: int) -> GetManufacturingOrderRecipeResponse:
        if mo_id not in recipe_cache:
            recipe_cache[mo_id] = await _get_manufacturing_order_recipe_impl(
                GetManufacturingOrderRecipeRequest(manufacturing_order_id=mo_id),
                context,
            )
        return recipe_cache[mo_id]

    # Phase A: expand replacements into per-MO delete+add ops
    for rep in request.replacements:
        # Resolve old variant
        if rep.old_variant_id is not None:
            old_variant_id = rep.old_variant_id
        elif rep.old_sku:
            variant = await services.cache.get_by_sku(sku=rep.old_sku)
            if not variant:
                raise ValueError(f"Old SKU '{rep.old_sku}' not found in cache")
            old_variant_id = variant["id"]
        else:
            raise ValueError("Replacement requires old_sku or old_variant_id")

        # Pre-resolve new components (eager validation)
        resolved_new: list[tuple[int, str | None, float, str | None]] = []
        for spec in rep.new_components:
            v_id, sku, _ = await _resolve_variant_ref(
                services, sku=spec.sku, variant_id=spec.variant_id
            )
            resolved_new.append((v_id, sku, spec.planned_quantity_per_unit, spec.notes))

        group_label = _format_group_label(
            rep.old_sku, old_variant_id, rep.new_components
        )

        for mo_id in rep.manufacturing_order_ids:
            # Fetch the MO's recipe (cached per-MO to avoid duplicates)
            try:
                recipe = await _get_cached_recipe(mo_id)
            except Exception as e:
                msg = f"MO {mo_id}: failed to fetch recipe: {e}"
                if rep.strict:
                    raise ValueError(msg) from e
                warnings.append(msg)
                continue

            matching_rows = [r for r in recipe.rows if r.variant_id == old_variant_id]

            if not matching_rows:
                msg = f"MO {mo_id}: old variant {old_variant_id} not in recipe"
                if rep.strict:
                    raise ValueError(msg)
                warnings.append(msg + " — skipping")
                for v_id, sku, qty, _notes in resolved_new:
                    planned.append(
                        SubOpResult(
                            op_type=OpType.ADD,
                            manufacturing_order_id=mo_id,
                            variant_id=v_id,
                            sku=sku,
                            planned_quantity_per_unit=qty,
                            status=SubOpStatus.SKIPPED,
                            group_label=group_label,
                            error="Old variant not present in this MO",
                        )
                    )
                continue

            for row in matching_rows:
                planned.append(
                    SubOpResult(
                        op_type=OpType.DELETE,
                        manufacturing_order_id=mo_id,
                        recipe_row_id=row.id,
                        variant_id=row.variant_id,
                        sku=row.sku,
                        group_label=group_label,
                    )
                )
            for v_id, sku, qty, _notes in resolved_new:
                planned.append(
                    SubOpResult(
                        op_type=OpType.ADD,
                        manufacturing_order_id=mo_id,
                        variant_id=v_id,
                        sku=sku,
                        planned_quantity_per_unit=qty,
                        group_label=group_label,
                    )
                )

    # Phase B: explicit changes (escape hatch)
    for ch in request.changes:
        group_label = f"MO {ch.manufacturing_order_id} explicit"
        for row_id in ch.remove_row_ids:
            planned.append(
                SubOpResult(
                    op_type=OpType.DELETE,
                    manufacturing_order_id=ch.manufacturing_order_id,
                    recipe_row_id=row_id,
                    group_label=group_label,
                )
            )
        for spec in ch.add_variants:
            v_id, sku, _ = await _resolve_variant_ref(
                services, sku=spec.sku, variant_id=spec.variant_id
            )
            planned.append(
                SubOpResult(
                    op_type=OpType.ADD,
                    manufacturing_order_id=ch.manufacturing_order_id,
                    variant_id=v_id,
                    sku=sku,
                    planned_quantity_per_unit=spec.planned_quantity_per_unit,
                    group_label=group_label,
                )
            )

    return planned, warnings


async def _execute_batch_update(
    planned: list[SubOpResult],
    request: BatchUpdateRecipesRequest,
    context: Context,
    notes_by_index: dict[int, str | None] | None = None,
) -> list[SubOpResult]:
    """Execute the planned sub-ops, grouped by (mo_id, group_label).

    Deletes first, then adds in REVERSE order so the final created_at DESC
    ordering matches the user's intended sequence.
    """
    services = get_services(context)

    # Bucket by (mo_id, group_label) preserving insertion order
    buckets: dict[tuple[int, str], list[SubOpResult]] = {}
    for op in planned:
        if op.status == SubOpStatus.SKIPPED:
            continue
        key = (op.manufacturing_order_id, op.group_label or "")
        buckets.setdefault(key, []).append(op)

    aborted = False
    for (mo_id, _label), ops in buckets.items():
        if aborted:
            for op in ops:
                if op.status == SubOpStatus.PENDING:
                    op.status = SubOpStatus.SKIPPED
                    op.error = "Aborted after earlier failure"
            continue

        deletes = [o for o in ops if o.op_type == OpType.DELETE]
        adds = [o for o in ops if o.op_type == OpType.ADD]

        # Deletes first
        for op in deletes:
            try:
                await _api_delete_recipe_row(services, op.recipe_row_id or 0)
                op.status = SubOpStatus.SUCCESS
            except Exception as e:
                op.status = SubOpStatus.FAILED
                op.error = str(e)
                logger.error(
                    "batch_delete_failed",
                    row_id=op.recipe_row_id,
                    mo_id=mo_id,
                    error=str(e),
                )
                if not request.continue_on_error:
                    aborted = True
                    break

        if aborted:
            for op in adds:
                if op.status == SubOpStatus.PENDING:
                    op.status = SubOpStatus.SKIPPED
                    op.error = "Aborted after earlier failure"
            continue

        # Adds in REVERSE order — because GET returns by created_at DESC,
        # the last-created row appears first, matching the user's intended order.
        for op in reversed(adds):
            try:
                result = await _api_create_recipe_row(
                    services,
                    manufacturing_order_id=mo_id,
                    variant_id=op.variant_id or 0,
                    planned_quantity_per_unit=op.planned_quantity_per_unit or 1.0,
                    notes=None,
                )
                op.recipe_row_id = getattr(result, "id", None) if result else None
                op.status = SubOpStatus.SUCCESS
            except Exception as e:
                op.status = SubOpStatus.FAILED
                op.error = str(e)
                logger.error(
                    "batch_add_failed",
                    variant_id=op.variant_id,
                    mo_id=mo_id,
                    error=str(e),
                )
                if not request.continue_on_error:
                    aborted = True

    return planned


async def _batch_update_impl(
    request: BatchUpdateRecipesRequest, context: Context
) -> BatchUpdateRecipesResponse:
    """Implementation of batch_update_manufacturing_order_recipes."""
    if not request.replacements and not request.changes:
        raise ValueError("Must provide at least one replacement or change")

    # 1. Plan
    planned, warnings = await _plan_batch_update(request, context)
    total = len(planned)

    if total > MAX_BATCH_OPS:
        raise ValueError(
            f"Batch has {total} operations, exceeding MAX_BATCH_OPS={MAX_BATCH_OPS}. "
            "Split into smaller batches."
        )

    # 2. Preview mode
    if not request.confirm:
        skipped = sum(1 for o in planned if o.status == SubOpStatus.SKIPPED)
        return BatchUpdateRecipesResponse(
            is_preview=True,
            total_ops=total,
            success_count=0,
            failed_count=0,
            skipped_count=skipped,
            results=planned,
            warnings=warnings,
            message=f"Preview: {total} sub-operations planned. Set confirm=true to execute.",
        )

    # 3. Single confirmation for the batch
    del_count = sum(1 for o in planned if o.op_type == OpType.DELETE)
    add_count = sum(
        1
        for o in planned
        if o.op_type == OpType.ADD and o.status != SubOpStatus.SKIPPED
    )
    mo_count = len({o.manufacturing_order_id for o in planned})
    confirmation = await require_confirmation(
        context,
        f"Apply batch recipe update? {del_count} deletions, {add_count} additions "
        f"across {mo_count} MOs. Cannot be undone.",
    )
    if confirmation != ConfirmationResult.CONFIRMED:
        return BatchUpdateRecipesResponse(
            is_preview=True,
            total_ops=total,
            success_count=0,
            failed_count=0,
            skipped_count=0,
            results=planned,
            warnings=warnings,
            message=f"Batch update {confirmation} by user",
        )

    # 4. Execute
    results = await _execute_batch_update(planned, request, context)

    # 5. Tally
    success = sum(1 for r in results if r.status == SubOpStatus.SUCCESS)
    failed = sum(1 for r in results if r.status == SubOpStatus.FAILED)
    skipped = sum(1 for r in results if r.status == SubOpStatus.SKIPPED)
    return BatchUpdateRecipesResponse(
        is_preview=False,
        total_ops=total,
        success_count=success,
        failed_count=failed,
        skipped_count=skipped,
        results=results,
        warnings=warnings,
        message=(
            f"Batch update completed: {success} succeeded, "
            f"{failed} failed, {skipped} skipped"
        ),
    )


def _render_batch_markdown(response: BatchUpdateRecipesResponse) -> str:
    """Render a BatchUpdateRecipesResponse as markdown for fallback clients."""
    mode = "PREVIEW" if response.is_preview else "RESULTS"
    lines = [
        f"## Batch Recipe Update — {mode}",
        "",
        f"- **Total operations**: {response.total_ops}",
    ]
    if not response.is_preview:
        lines.extend(
            [
                f"- **Succeeded**: {response.success_count}",
                f"- **Failed**: {response.failed_count}",
                f"- **Skipped**: {response.skipped_count}",
            ]
        )
    lines.append("")

    # Group by group_label
    groups: dict[str, list[SubOpResult]] = {}
    for op in response.results:
        groups.setdefault(op.group_label or "(ungrouped)", []).append(op)

    for label, ops in groups.items():
        lines.append(f"### {label}")
        lines.append("")
        lines.append(
            format_md_table(
                headers=["MO", "Action", "Row ID", "SKU", "Qty", "Status", "Error"],
                rows=[
                    [
                        op.manufacturing_order_id,
                        op.op_type.upper(),
                        str(op.recipe_row_id) if op.recipe_row_id else "(new)",
                        op.sku or (f"variant {op.variant_id}" if op.variant_id else ""),
                        str(op.planned_quantity_per_unit)
                        if op.planned_quantity_per_unit is not None
                        else "—",
                        op.status.upper(),
                        op.error or "",
                    ]
                    for op in ops
                ],
            )
        )
        lines.append("")

    if response.warnings:
        lines.append("### Warnings")
        for w in response.warnings:
            lines.append(f"- {w}")
        lines.append("")

    lines.append(f"**{response.message}**")
    return "\n".join(lines)


@observe_tool
@unpack_pydantic_params
async def batch_update_manufacturing_order_recipes(
    request: Annotated[BatchUpdateRecipesRequest, Unpack()], context: Context
) -> ToolResult:
    """Batch update recipe rows across one or more manufacturing orders.

    Two expression modes (mixable in one request):

    - **replacements**: "replace variant X with [Y, Z] across these MOs" — ideal
      for swapping a component across many MOs in one shot. Accepts old_sku or
      old_variant_id, with a list of new_components (each with sku/variant_id
      and planned_quantity_per_unit).
    - **changes**: explicit per-MO row deletes and additions — escape hatch
      for arbitrary edits.

    Two-step flow: confirm=false to preview (resolves row IDs, shows full plan),
    confirm=true to execute (single confirmation elicitation for the whole batch).

    Semantics:
    - Within a replacement group, old rows are deleted first, then new rows are
      added in reverse order so they appear before the replaced row in Katana's
      natural created_at DESC sort.
    - Old variant appearing multiple times in an MO → all matches are deleted.
    - Old variant not in an MO → skipped with warning (unless strict=true).
    - No rollback. Every sub-op's final status is reported.
    - continue_on_error=true (default): run all sub-ops, mixed results ok.
    - continue_on_error=false: stop at first failure; remaining ops become SKIPPED.
    """
    from fastmcp.tools import ToolResult

    from katana_mcp.tools.prefab_ui import build_batch_recipe_update_ui

    response = await _batch_update_impl(request, context)
    markdown = _render_batch_markdown(response)
    ui = build_batch_recipe_update_ui(response.model_dump())

    # Attach the response data alongside the Prefab UI envelope so programmatic
    # clients can access structured fields.
    prefab_json = ui.to_json()
    prefab_json["data"] = response.model_dump()

    return ToolResult(content=markdown, structured_content=prefab_json)


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
    mcp.tool(
        tags={"orders", "manufacturing", "write", "batch"},
        annotations=_destructive_write,
    )(batch_update_manufacturing_order_recipes)
