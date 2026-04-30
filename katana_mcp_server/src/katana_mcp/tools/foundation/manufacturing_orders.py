"""Manufacturing order management tools for Katana MCP Server.

Foundation tools for creating manufacturing orders to initiate production.

These tools provide:
- create_manufacturing_order: Create manufacturing orders with preview/confirm pattern
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Any, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, Field

from katana_mcp.cache import EntityType
from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.list_coercion import CoercedIntList, CoercedIntListOpt
from katana_mcp.tools.tool_result_utils import (
    BLOCK_WARNING_PREFIX,
    UI_META,
    PaginationMeta,
    apply_date_window_filters,
    coerce_enum,
    enum_to_str,
    format_md_table,
    iso_or_none,
    make_simple_result,
    make_tool_result,
    none_coro,
    parse_request_dates,
)
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.domain.converters import to_unset, unwrap_unset
from katana_public_api_client.models import (
    CreateManufacturingOrderRequest as APICreateManufacturingOrderRequest,
    GetAllManufacturingOrdersStatus,
    ManufacturingOrder,
)
from katana_public_api_client.utils import unwrap_as

logger = get_logger(__name__)


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
        default=None,
        description="Variant ID to manufacture (required for standalone MOs)",
    )
    planned_quantity: float | None = Field(
        default=None,
        description="Planned quantity (required for standalone MOs)",
        gt=0,
    )
    location_id: int | None = Field(
        default=None,
        description="Production location ID (required for standalone MOs)",
    )
    sales_order_row_id: int | None = Field(
        default=None,
        description="Sales order row ID — when provided, creates a make-to-order "
        "MO linked to that sales order row (uses /manufacturing_order_make_to_order).",
    )
    create_subassemblies: bool = Field(
        default=False,
        description="Make-to-order only: also create MOs for subassemblies. Ignored for standalone MOs.",
    )
    order_created_date: datetime | None = Field(
        default=None, description="Order creation date (standalone mode only)"
    )
    production_deadline_date: datetime | None = Field(
        default=None, description="Production deadline date (standalone mode only)"
    )
    additional_info: str | None = Field(
        default=None, description="Additional notes (standalone mode only)"
    )
    order_no: str | None = Field(
        default=None,
        description=(
            "Manufacturing order reference number (standalone mode only). "
            "Required by the live API; if omitted, a timestamp-based default "
            "(``MO-<unix-ts>``) is generated client-side."
        ),
    )
    confirm: bool = Field(
        default=False,
        description="If false, returns preview. If true, creates order.",
    )


class ManufacturingOrderResponse(BaseModel):
    """Response from creating a manufacturing order."""

    id: int | None = None
    order_no: str | None = None
    variant_id: int | None = None
    sku: str | None = None
    planned_quantity: float | None = None
    location_id: int | None = None
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
            missing_fields = ", ".join(missing)
            raise ValueError(
                f"Standalone MO requires: {missing_fields}. "
                "Alternatively, provide sales_order_row_id for a make-to-order linked MO."
            )

    mode = "make-to-order" if is_make_to_order else "standalone"
    action = "Previewing" if not request.confirm else "Starting"
    logger.info(f"{action} manufacturing order ({mode})")

    # Make-to-order: fetch the sales_order_row upfront so both preview and
    # confirm see the same backing data. The duplicate-create guard runs
    # in the confirm path too — programmatic callers skipping the preview
    # UI get the same protection as the iframe (defense in depth).
    sor_variant_id: int | None = None
    sor_quantity: float | None = None
    sor_location_id: int | None = None
    linked_mo: int | None = None
    if is_make_to_order:
        assert request.sales_order_row_id is not None
        services = get_services(context)
        from katana_public_api_client.api.sales_order_row import (
            get_sales_order_row as api_get_sor,
        )
        from katana_public_api_client.models import SalesOrderRow

        sor_response = await api_get_sor.asyncio_detailed(
            id=request.sales_order_row_id, client=services.client
        )
        sor = unwrap_as(sor_response, SalesOrderRow)
        sor_variant_id = sor.variant_id
        sor_quantity = sor.quantity
        sor_location_id = unwrap_unset(sor.location_id, None)
        # SalesOrderRow.sku isn't a typed field on the attrs model (spec
        # drift — the live API returns it but the model doesn't list it),
        # so the preview omits SKU. variant_id + quantity is enough for
        # the user to recognize what's being made.
        linked_mo = unwrap_unset(sor.linked_manufacturing_order_id, None)

    if not request.confirm:
        warnings: list[str] = []
        next_actions = [
            "Review the order details",
            "Set confirm=true to create the manufacturing order",
        ]

        if is_make_to_order:
            if linked_mo is not None:
                warnings.append(
                    f"{BLOCK_WARNING_PREFIX} sales_order_row "
                    f"{request.sales_order_row_id} is already linked to "
                    f"manufacturing order {linked_mo}. Creating another "
                    "would duplicate production."
                )
                next_actions = [
                    f"Use get_manufacturing_order with order_id={linked_mo} "
                    "to inspect the existing order, or cancel."
                ]

            preview_msg = (
                f"Preview: Make-to-order MO from sales_order_row_id="
                f"{request.sales_order_row_id}"
                + (" (with subassemblies)" if request.create_subassemblies else "")
            )

            return ManufacturingOrderResponse(
                variant_id=sor_variant_id,
                planned_quantity=sor_quantity,
                location_id=sor_location_id,
                is_preview=True,
                warnings=warnings,
                next_actions=next_actions,
                message=preview_msg,
            )

        # Standalone preview — caller has already provided variant/quantity/location.
        if request.production_deadline_date is None:
            warnings.append(
                "No production_deadline_date specified - order will have no deadline"
            )
        if request.additional_info is None:
            warnings.append(
                "No additional_info specified - consider adding notes for context"
            )

        preview_msg = (
            f"Preview: Manufacturing order for variant {request.variant_id}, "
            f"quantity {request.planned_quantity}"
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
            next_actions=next_actions,
            message=preview_msg,
        )

    # Confirm-path defense-in-depth: refuse if the SO row is already linked.
    if is_make_to_order and linked_mo is not None:
        return ManufacturingOrderResponse(
            variant_id=sor_variant_id,
            planned_quantity=sor_quantity,
            location_id=sor_location_id,
            is_preview=False,
            warnings=[
                f"{BLOCK_WARNING_PREFIX} sales_order_row "
                f"{request.sales_order_row_id} is already linked to "
                f"manufacturing order {linked_mo}. No new order was created."
            ],
            next_actions=[
                f"Use get_manufacturing_order with order_id={linked_mo} "
                "to inspect the existing order."
            ],
            message=(
                f"Refused: sales_order_row {request.sales_order_row_id} is "
                f"already linked to MO {linked_mo}; no duplicate created."
            ),
        )

    try:
        services = get_services(context)

        if is_make_to_order:
            from katana_public_api_client.api.manufacturing_order import (
                make_to_order_manufacturing_order as api_mto,
            )
            from katana_public_api_client.models.make_to_order_manufacturing_order_request import (
                MakeToOrderManufacturingOrderRequest,
            )

            assert request.sales_order_row_id is not None
            mto_request = MakeToOrderManufacturingOrderRequest(
                sales_order_row_id=request.sales_order_row_id,
                create_subassemblies=request.create_subassemblies,
            )
            response = await api_mto.asyncio_detailed(
                client=services.client, body=mto_request
            )
        else:
            assert request.variant_id is not None
            assert request.planned_quantity is not None
            assert request.location_id is not None
            # ``order_no`` is required by the live API. Auto-generate a
            # timestamp-based default if the caller didn't provide one so
            # the request constructs and Katana accepts it.
            order_no = request.order_no or (f"MO-{int(datetime.now(UTC).timestamp())}")
            api_request = APICreateManufacturingOrderRequest(
                variant_id=request.variant_id,
                planned_quantity=request.planned_quantity,
                location_id=request.location_id,
                order_no=order_no,
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
        variant_id = unwrap_unset(mo.variant_id, request.variant_id)
        planned_quantity = unwrap_unset(mo.planned_quantity, request.planned_quantity)
        location_id = unwrap_unset(mo.location_id, request.location_id)
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

    Two-step flow: confirm=false to preview, confirm=true to create.
    """
    from katana_mcp.tools.prefab_ui import (
        build_order_created_ui,
        build_order_preview_ui,
        call_tool_from_request,
    )

    response = await _create_manufacturing_order_impl(request, context)

    order_dict = response.model_dump()
    if response.is_preview:
        ui = build_order_preview_ui(
            order_dict,
            "Manufacturing Order",
            request=request.model_dump(),
            confirm_action=call_tool_from_request(
                "create_manufacturing_order",
                CreateManufacturingOrderRequest,
                overrides={"confirm": True},
            ),
        )
    else:
        ui = build_order_created_ui(order_dict, "Manufacturing Order")

    return make_tool_result(response, ui=ui)


# ============================================================================
# Tool 2: get_manufacturing_order
# ============================================================================


class GetManufacturingOrderRequest(BaseModel):
    """Request to look up a manufacturing order."""

    order_no: str | None = Field(
        default=None, description="Order number to look up (e.g., '#WEB20082 / 1')"
    )
    order_id: int | None = Field(default=None, description="Manufacturing order ID")
    format: Literal["markdown", "json"] = Field(
        default="markdown",
        description=(
            "Output format: 'markdown' (default) for human-readable tables; "
            "'json' for structured data consumable by downstream tools/aggregations."
        ),
    )


class BatchTransactionInfo(BaseModel):
    """One entry in ``ManufacturingOrder.batch_transactions``.

    Mirrors the generated ``BatchTransaction`` attrs model.
    """

    batch_id: int | None = None
    quantity: float | None = None


class SerialNumberInfo(BaseModel):
    """One entry in ``serial_numbers`` lists on MO and production records.

    Mirrors the generated ``SerialNumber`` attrs model.
    """

    id: int | None = None
    transaction_id: str | None = None
    serial_number: str | None = None
    resource_type: str | None = None
    resource_id: int | None = None
    transaction_date: str | None = None
    quantity_change: int | None = None


class AssignedOperatorInfo(BaseModel):
    """One entry in an operation row's ``assigned_operators`` /
    ``completed_by_operators`` list. Mirrors the generated ``AssignedOperator``.
    """

    operator_id: int
    name: str
    deleted_at: str | None = None


class RecipeRowBatchTransactionInfo(BaseModel):
    """One entry in a recipe row's ``batch_transactions`` list. Mirrors
    the generated ``ManufacturingOrderRecipeRowBatchTransactionsItem``.
    """

    batch_id: int | None = None
    quantity: float | None = None


class RecipeRowInfo(BaseModel):
    """Full manufacturing-order recipe row. Exhaustive — every field on
    ``ManufacturingOrderRecipeRow`` is surfaced, plus the resolved SKU
    for display convenience.
    """

    id: int
    manufacturing_order_id: int | None = None
    variant_id: int | None = None
    sku: str | None = None
    notes: str | None = None
    planned_quantity_per_unit: float | None = None
    total_actual_quantity: float | None = None
    total_consumed_quantity: float | None = None
    total_remaining_quantity: float | None = None
    ingredient_availability: str | None = None
    ingredient_expected_date: str | None = None
    batch_transactions: list[RecipeRowBatchTransactionInfo] = Field(
        default_factory=list
    )
    cost: float | None = None
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None


class OperationRowInfo(BaseModel):
    """Full manufacturing-order operation row. Exhaustive — every field on
    ``ManufacturingOrderOperationRow`` is surfaced.
    """

    id: int
    manufacturing_order_id: int | None = None
    status: str | None = None
    type_: str | None = Field(default=None, alias="type_")
    rank: float | None = None
    operation_id: int | None = None
    operation_name: str | None = None
    resource_id: int | None = None
    resource_name: str | None = None
    assigned_operators: list[AssignedOperatorInfo] = Field(default_factory=list)
    completed_by_operators: list[AssignedOperatorInfo] = Field(default_factory=list)
    active_operator_id: float | None = None
    planned_time_per_unit: float | None = None
    planned_time_parameter: float | None = None
    total_actual_time: float | None = None
    total_consumed_time: float | None = None
    total_remaining_time: float | None = None
    planned_cost_per_unit: float | None = None
    total_actual_cost: float | None = None
    cost_per_hour: float | None = None
    cost_parameter: float | None = None
    group_boundary: float | None = None
    is_status_actionable: bool | None = None
    completed_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None


class ProductionIngredientInfo(BaseModel):
    """One entry in a production's ``ingredients`` list. Mirrors the
    generated ``ManufacturingOrderProductionIngredient``.
    """

    id: int
    manufacturing_order_id: int | None = None
    manufacturing_order_recipe_row_id: int | None = None
    production_id: int | None = None
    location_id: int | None = None
    variant_id: int | None = None
    quantity: float | None = None
    production_date: str | None = None
    cost: float | None = None
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None


class ProductionOperationInfo(BaseModel):
    """One entry in a production's ``operations`` list. Mirrors the
    generated ``ManufacturingOrderOperationProduction``.
    """

    id: int
    manufacturing_order_id: int | None = None
    manufacturing_order_operation_id: int | None = None
    production_id: int | None = None
    location_id: int | None = None
    time: float | None = None
    production_date: str | None = None
    cost: float | None = None
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None


class ProductionInfo(BaseModel):
    """Full manufacturing-order production record. Exhaustive — every field
    on ``ManufacturingOrderProduction`` is surfaced.
    """

    id: int
    manufacturing_order_id: int | None = None
    factory_id: int | None = None
    quantity: float | None = None
    production_date: str | None = None
    ingredients: list[ProductionIngredientInfo] = Field(default_factory=list)
    operations: list[ProductionOperationInfo] = Field(default_factory=list)
    serial_numbers: list[SerialNumberInfo] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None


class GetManufacturingOrderResponse(BaseModel):
    """Full manufacturing order details. Exhaustive — every field Katana
    exposes on ``ManufacturingOrder`` is surfaced (including nested recipe
    rows, operation rows, and production records) so callers don't need
    follow-up lookups for standard fields.
    """

    id: int
    order_no: str | None = None
    status: str | None = None
    variant_id: int | None = None
    planned_quantity: float | None = None
    actual_quantity: float | None = None
    completed_quantity: float | None = None
    remaining_quantity: float | None = None
    includes_partial_completions: bool | None = None
    location_id: int | None = None
    order_created_date: str | None = None
    production_deadline_date: str | None = None
    done_date: str | None = None
    additional_info: str | None = None
    is_linked_to_sales_order: bool | None = None
    ingredient_availability: str | None = None
    total_cost: float | None = None
    total_actual_time: float | None = None
    total_planned_time: float | None = None
    sales_order_id: int | None = None
    sales_order_row_id: int | None = None
    sales_order_delivery_deadline: str | None = None
    material_cost: float | None = None
    subassemblies_cost: float | None = None
    operations_cost: float | None = None
    batch_transactions: list[BatchTransactionInfo] = Field(default_factory=list)
    serial_numbers: list[SerialNumberInfo] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None
    recipe_rows: list[RecipeRowInfo] = Field(default_factory=list)
    operation_rows: list[OperationRowInfo] = Field(default_factory=list)
    productions: list[ProductionInfo] = Field(default_factory=list)


def _recipe_row_info_from_attrs(row: Any, sku: str | None) -> RecipeRowInfo:
    """Build RecipeRowInfo from a ManufacturingOrderRecipeRow attrs model."""
    raw_batch = unwrap_unset(row.batch_transactions, []) or []
    batch_infos = [
        RecipeRowBatchTransactionInfo(
            batch_id=unwrap_unset(bt.batch_id, None),
            quantity=unwrap_unset(bt.quantity, None),
        )
        for bt in raw_batch
    ]
    return RecipeRowInfo(
        id=row.id,
        manufacturing_order_id=unwrap_unset(row.manufacturing_order_id, None),
        variant_id=unwrap_unset(row.variant_id, None),
        sku=sku,
        notes=unwrap_unset(row.notes, None),
        planned_quantity_per_unit=unwrap_unset(row.planned_quantity_per_unit, None),
        total_actual_quantity=unwrap_unset(row.total_actual_quantity, None),
        total_consumed_quantity=unwrap_unset(row.total_consumed_quantity, None),
        total_remaining_quantity=unwrap_unset(row.total_remaining_quantity, None),
        ingredient_availability=unwrap_unset(row.ingredient_availability, None),
        ingredient_expected_date=iso_or_none(
            unwrap_unset(row.ingredient_expected_date, None)
        ),
        batch_transactions=batch_infos,
        cost=unwrap_unset(row.cost, None),
        created_at=iso_or_none(unwrap_unset(row.created_at, None)),
        updated_at=iso_or_none(unwrap_unset(row.updated_at, None)),
        deleted_at=iso_or_none(unwrap_unset(row.deleted_at, None)),
    )


def _operation_row_info_from_attrs(row: Any) -> OperationRowInfo:
    """Build OperationRowInfo from a ManufacturingOrderOperationRow attrs model."""
    assigned = [
        AssignedOperatorInfo(
            operator_id=op.operator_id,
            name=op.name,
            deleted_at=iso_or_none(unwrap_unset(op.deleted_at, None)),
        )
        for op in (unwrap_unset(row.assigned_operators, []) or [])
    ]
    completed = [
        AssignedOperatorInfo(
            operator_id=op.operator_id,
            name=op.name,
            deleted_at=iso_or_none(unwrap_unset(op.deleted_at, None)),
        )
        for op in (unwrap_unset(row.completed_by_operators, []) or [])
    ]
    return OperationRowInfo(
        id=row.id,
        manufacturing_order_id=unwrap_unset(row.manufacturing_order_id, None),
        status=enum_to_str(unwrap_unset(row.status, None)),
        type_=unwrap_unset(row.type_, None),
        rank=unwrap_unset(row.rank, None),
        operation_id=unwrap_unset(row.operation_id, None),
        operation_name=unwrap_unset(row.operation_name, None),
        resource_id=unwrap_unset(row.resource_id, None),
        resource_name=unwrap_unset(row.resource_name, None),
        assigned_operators=assigned,
        completed_by_operators=completed,
        active_operator_id=unwrap_unset(row.active_operator_id, None),
        planned_time_per_unit=unwrap_unset(row.planned_time_per_unit, None),
        planned_time_parameter=unwrap_unset(row.planned_time_parameter, None),
        total_actual_time=unwrap_unset(row.total_actual_time, None),
        total_consumed_time=unwrap_unset(row.total_consumed_time, None),
        total_remaining_time=unwrap_unset(row.total_remaining_time, None),
        planned_cost_per_unit=unwrap_unset(row.planned_cost_per_unit, None),
        total_actual_cost=unwrap_unset(row.total_actual_cost, None),
        cost_per_hour=unwrap_unset(row.cost_per_hour, None),
        cost_parameter=unwrap_unset(row.cost_parameter, None),
        group_boundary=unwrap_unset(row.group_boundary, None),
        is_status_actionable=unwrap_unset(row.is_status_actionable, None),
        completed_at=iso_or_none(unwrap_unset(row.completed_at, None)),
        created_at=iso_or_none(unwrap_unset(row.created_at, None)),
        updated_at=iso_or_none(unwrap_unset(row.updated_at, None)),
        deleted_at=iso_or_none(unwrap_unset(row.deleted_at, None)),
    )


def _production_info_from_attrs(prod: Any) -> ProductionInfo:
    """Build ProductionInfo from a ManufacturingOrderProduction attrs model."""
    ingredients = [
        ProductionIngredientInfo(
            id=ing.id,
            manufacturing_order_id=unwrap_unset(ing.manufacturing_order_id, None),
            manufacturing_order_recipe_row_id=unwrap_unset(
                ing.manufacturing_order_recipe_row_id, None
            ),
            production_id=unwrap_unset(ing.production_id, None),
            location_id=unwrap_unset(ing.location_id, None),
            variant_id=unwrap_unset(ing.variant_id, None),
            quantity=unwrap_unset(ing.quantity, None),
            production_date=iso_or_none(unwrap_unset(ing.production_date, None)),
            cost=unwrap_unset(ing.cost, None),
            created_at=iso_or_none(unwrap_unset(ing.created_at, None)),
            updated_at=iso_or_none(unwrap_unset(ing.updated_at, None)),
            deleted_at=iso_or_none(unwrap_unset(ing.deleted_at, None)),
        )
        for ing in (unwrap_unset(prod.ingredients, []) or [])
    ]
    operations = [
        ProductionOperationInfo(
            id=op.id,
            manufacturing_order_id=unwrap_unset(op.manufacturing_order_id, None),
            manufacturing_order_operation_id=unwrap_unset(
                op.manufacturing_order_operation_id, None
            ),
            production_id=unwrap_unset(op.production_id, None),
            location_id=unwrap_unset(op.location_id, None),
            time=unwrap_unset(op.time, None),
            production_date=iso_or_none(unwrap_unset(op.production_date, None)),
            cost=unwrap_unset(op.cost, None),
            created_at=iso_or_none(unwrap_unset(op.created_at, None)),
            updated_at=iso_or_none(unwrap_unset(op.updated_at, None)),
            deleted_at=iso_or_none(unwrap_unset(op.deleted_at, None)),
        )
        for op in (unwrap_unset(prod.operations, []) or [])
    ]
    serial_numbers = [
        _serial_number_info_from_attrs(sn)
        for sn in (unwrap_unset(prod.serial_numbers, []) or [])
    ]
    return ProductionInfo(
        id=prod.id,
        manufacturing_order_id=unwrap_unset(prod.manufacturing_order_id, None),
        factory_id=unwrap_unset(prod.factory_id, None),
        quantity=unwrap_unset(prod.quantity, None),
        production_date=iso_or_none(unwrap_unset(prod.production_date, None)),
        ingredients=ingredients,
        operations=operations,
        serial_numbers=serial_numbers,
        created_at=iso_or_none(unwrap_unset(prod.created_at, None)),
        updated_at=iso_or_none(unwrap_unset(prod.updated_at, None)),
        deleted_at=iso_or_none(unwrap_unset(prod.deleted_at, None)),
    )


def _serial_number_info_from_attrs(sn: Any) -> SerialNumberInfo:
    """Build SerialNumberInfo from a SerialNumber attrs model."""
    return SerialNumberInfo(
        id=unwrap_unset(sn.id, None),
        transaction_id=unwrap_unset(sn.transaction_id, None),
        serial_number=unwrap_unset(sn.serial_number, None),
        resource_type=enum_to_str(unwrap_unset(sn.resource_type, None)),
        resource_id=unwrap_unset(sn.resource_id, None),
        transaction_date=iso_or_none(unwrap_unset(sn.transaction_date, None)),
        quantity_change=unwrap_unset(sn.quantity_change, None),
    )


async def _fetch_mo_recipe_rows(
    services: Any, manufacturing_order_id: int
) -> list[RecipeRowInfo]:
    """Fetch every recipe row for the MO and enrich with cached SKU."""
    from katana_public_api_client.api.manufacturing_order_recipe import (
        get_all_manufacturing_order_recipe_rows,
    )
    from katana_public_api_client.utils import unwrap_data

    response = await get_all_manufacturing_order_recipe_rows.asyncio_detailed(
        client=services.client,
        manufacturing_order_id=manufacturing_order_id,
        limit=250,
    )
    raw_rows = unwrap_data(response, default=[])

    variant_ids = [unwrap_unset(row.variant_id, None) for row in raw_rows]
    variants = await asyncio.gather(
        *(
            services.cache.get_by_id(EntityType.VARIANT, v_id)
            if v_id is not None
            else none_coro()
            for v_id in variant_ids
        )
    )
    return [
        _recipe_row_info_from_attrs(row, variant.get("sku") if variant else None)
        for row, variant in zip(raw_rows, variants, strict=True)
    ]


async def _fetch_mo_operation_rows(
    services: Any, manufacturing_order_id: int
) -> list[OperationRowInfo]:
    """Fetch every operation row for the MO."""
    from katana_public_api_client.api.manufacturing_order_operation import (
        get_all_manufacturing_order_operation_rows,
    )
    from katana_public_api_client.utils import unwrap_data

    response = await get_all_manufacturing_order_operation_rows.asyncio_detailed(
        client=services.client,
        manufacturing_order_id=manufacturing_order_id,
        limit=250,
    )
    raw_rows = unwrap_data(response, default=[])
    return [_operation_row_info_from_attrs(row) for row in raw_rows]


async def _fetch_mo_productions(
    services: Any, manufacturing_order_id: int
) -> list[ProductionInfo]:
    """Fetch every production record for the MO."""
    from katana_public_api_client.api.manufacturing_order import (
        get_all_manufacturing_order_productions,
    )
    from katana_public_api_client.utils import unwrap_data

    response = await get_all_manufacturing_order_productions.asyncio_detailed(
        client=services.client,
        manufacturing_order_ids=[manufacturing_order_id],
        limit=250,
    )
    raw = unwrap_data(response, default=[])
    return [_production_info_from_attrs(p) for p in raw]


def _build_mo_response(
    mo: ManufacturingOrder,
    recipe_rows: list[RecipeRowInfo],
    operation_rows: list[OperationRowInfo],
    productions: list[ProductionInfo],
) -> GetManufacturingOrderResponse:
    """Flatten a ManufacturingOrder attrs model + related resource lists
    into GetManufacturingOrderResponse, surfacing every attrs field.
    """
    batch_transactions = [
        BatchTransactionInfo(
            batch_id=bt.batch_id,
            quantity=bt.quantity,
        )
        for bt in (unwrap_unset(mo.batch_transactions, []) or [])
    ]
    serial_numbers = [
        _serial_number_info_from_attrs(sn)
        for sn in (unwrap_unset(mo.serial_numbers, []) or [])
    ]
    return GetManufacturingOrderResponse(
        id=mo.id,
        order_no=unwrap_unset(mo.order_no, None),
        status=enum_to_str(unwrap_unset(mo.status, None)),
        variant_id=unwrap_unset(mo.variant_id, None),
        planned_quantity=unwrap_unset(mo.planned_quantity, None),
        actual_quantity=unwrap_unset(mo.actual_quantity, None),
        completed_quantity=unwrap_unset(mo.completed_quantity, None),
        remaining_quantity=unwrap_unset(mo.remaining_quantity, None),
        includes_partial_completions=unwrap_unset(
            mo.includes_partial_completions, None
        ),
        location_id=unwrap_unset(mo.location_id, None),
        order_created_date=iso_or_none(unwrap_unset(mo.order_created_date, None)),
        production_deadline_date=iso_or_none(
            unwrap_unset(mo.production_deadline_date, None)
        ),
        done_date=iso_or_none(unwrap_unset(mo.done_date, None)),
        additional_info=unwrap_unset(mo.additional_info, None),
        is_linked_to_sales_order=unwrap_unset(mo.is_linked_to_sales_order, None),
        ingredient_availability=enum_to_str(
            unwrap_unset(mo.ingredient_availability, None)
        ),
        total_cost=unwrap_unset(mo.total_cost, None),
        total_actual_time=unwrap_unset(mo.total_actual_time, None),
        total_planned_time=unwrap_unset(mo.total_planned_time, None),
        sales_order_id=unwrap_unset(mo.sales_order_id, None),
        sales_order_row_id=unwrap_unset(mo.sales_order_row_id, None),
        sales_order_delivery_deadline=iso_or_none(
            unwrap_unset(mo.sales_order_delivery_deadline, None)
        ),
        material_cost=unwrap_unset(mo.material_cost, None),
        subassemblies_cost=unwrap_unset(mo.subassemblies_cost, None),
        operations_cost=unwrap_unset(mo.operations_cost, None),
        batch_transactions=batch_transactions,
        serial_numbers=serial_numbers,
        created_at=iso_or_none(unwrap_unset(mo.created_at, None)),
        updated_at=iso_or_none(unwrap_unset(mo.updated_at, None)),
        deleted_at=iso_or_none(unwrap_unset(mo.deleted_at, None)),
        recipe_rows=recipe_rows,
        operation_rows=operation_rows,
        productions=productions,
    )


async def _get_manufacturing_order_impl(
    request: GetManufacturingOrderRequest, context: Context
) -> GetManufacturingOrderResponse:
    """Look up a manufacturing order by order number or ID with exhaustive detail.

    Fetches the MO record plus its recipe rows, operation rows, and production
    records — each via its own API call (cache-first migration tracked in #342).
    """
    from katana_public_api_client.api.manufacturing_order import (
        get_all_manufacturing_orders,
        get_manufacturing_order as api_get_manufacturing_order,
    )
    from katana_public_api_client.utils import unwrap_as, unwrap_data

    if not request.order_no and not request.order_id:
        raise ValueError("Either order_no or order_id must be provided")

    services = get_services(context)

    if request.order_id:
        response = await api_get_manufacturing_order.asyncio_detailed(
            id=request.order_id, client=services.client
        )
        mo = unwrap_as(response, ManufacturingOrder)
    else:
        assert request.order_no is not None  # narrow for type-checker
        list_response = await get_all_manufacturing_orders.asyncio_detailed(
            client=services.client, order_no=request.order_no, limit=1
        )
        orders = unwrap_data(list_response, default=[])
        if not orders:
            raise ValueError(f"Manufacturing order '{request.order_no}' not found")
        mo = orders[0]

    # Related resources — fetched in parallel. Each is a separate HTTP call
    # today; the cache epic (#342) will move these to cache-first.
    recipe_rows, operation_rows, productions = await asyncio.gather(
        _fetch_mo_recipe_rows(services, mo.id),
        _fetch_mo_operation_rows(services, mo.id),
        _fetch_mo_productions(services, mo.id),
    )

    return _build_mo_response(mo, recipe_rows, operation_rows, productions)


def _render_mo_scalar_lines(response: GetManufacturingOrderResponse) -> list[str]:
    """Render every scalar MO field as ``**field_name**: value`` lines.

    Uses canonical Pydantic field names so LLM consumers can't confuse a
    prettified label with a different field name (see #346 follow-on).
    """
    scalar_fields = (
        "id",
        "order_no",
        "status",
        "variant_id",
        "planned_quantity",
        "actual_quantity",
        "completed_quantity",
        "remaining_quantity",
        "includes_partial_completions",
        "location_id",
        "order_created_date",
        "production_deadline_date",
        "done_date",
        "additional_info",
        "is_linked_to_sales_order",
        "ingredient_availability",
        "total_cost",
        "total_actual_time",
        "total_planned_time",
        "sales_order_id",
        "sales_order_row_id",
        "sales_order_delivery_deadline",
        "material_cost",
        "subassemblies_cost",
        "operations_cost",
        "created_at",
        "updated_at",
        "deleted_at",
    )
    lines: list[str] = []
    for fname in scalar_fields:
        val = getattr(response, fname)
        if val is None or val == "":
            continue
        lines.append(f"**{fname}**: {val}")
    return lines


def _render_list_field(label: str, items: list[Any], renderer: Any) -> list[str]:
    """Render a list-shaped response field with canonical-name syntax.

    Empty → ``**label**: []`` so presence-vs-absence is unambiguous.
    Populated → ``**label** (N):`` followed by indented per-item blocks.
    """
    if not items:
        return [f"**{label}**: []"]
    lines = ["", f"**{label}** ({len(items)}):"]
    for item in items:
        lines.append(renderer(item))
    return lines


def _render_recipe_row_md(row: RecipeRowInfo) -> str:
    """Render a single recipe row as a compact multi-line block."""
    lines = [f"  - **id**: {row.id}"]
    scalar_fields = (
        "manufacturing_order_id",
        "variant_id",
        "sku",
        "notes",
        "planned_quantity_per_unit",
        "total_actual_quantity",
        "total_consumed_quantity",
        "total_remaining_quantity",
        "ingredient_availability",
        "ingredient_expected_date",
        "cost",
        "created_at",
        "updated_at",
        "deleted_at",
    )
    for fname in scalar_fields:
        val = getattr(row, fname)
        if val is None or val == "":
            continue
        lines.append(f"    **{fname}**: {val}")
    if row.batch_transactions:
        lines.append(f"    **batch_transactions** ({len(row.batch_transactions)}):")
        for bt in row.batch_transactions:
            lines.append(f"      - batch_id={bt.batch_id}, quantity={bt.quantity}")
    else:
        lines.append("    **batch_transactions**: []")
    return "\n".join(lines)


def _render_operation_row_md(row: OperationRowInfo) -> str:
    """Render a single operation row as a compact multi-line block."""
    lines = [f"  - **id**: {row.id}"]
    scalar_fields = (
        "manufacturing_order_id",
        "status",
        "type_",
        "rank",
        "operation_id",
        "operation_name",
        "resource_id",
        "resource_name",
        "active_operator_id",
        "planned_time_per_unit",
        "planned_time_parameter",
        "total_actual_time",
        "total_consumed_time",
        "total_remaining_time",
        "planned_cost_per_unit",
        "total_actual_cost",
        "cost_per_hour",
        "cost_parameter",
        "group_boundary",
        "is_status_actionable",
        "completed_at",
        "created_at",
        "updated_at",
        "deleted_at",
    )
    for fname in scalar_fields:
        val = getattr(row, fname)
        if val is None or val == "":
            continue
        lines.append(f"    **{fname}**: {val}")
    for list_name in ("assigned_operators", "completed_by_operators"):
        items = getattr(row, list_name)
        if not items:
            lines.append(f"    **{list_name}**: []")
            continue
        lines.append(f"    **{list_name}** ({len(items)}):")
        for op in items:
            lines.append(f"      - operator_id={op.operator_id}, name={op.name}")
    return "\n".join(lines)


def _render_production_md(prod: ProductionInfo) -> str:
    """Render a single production record as a compact multi-line block."""
    lines = [f"  - **id**: {prod.id}"]
    scalar_fields = (
        "manufacturing_order_id",
        "factory_id",
        "quantity",
        "production_date",
        "created_at",
        "updated_at",
        "deleted_at",
    )
    for fname in scalar_fields:
        val = getattr(prod, fname)
        if val is None or val == "":
            continue
        lines.append(f"    **{fname}**: {val}")
    lines.append(
        f"    **ingredients** ({len(prod.ingredients)}):"
        if prod.ingredients
        else "    **ingredients**: []"
    )
    for ing in prod.ingredients:
        lines.append(
            f"      - id={ing.id}, variant_id={ing.variant_id}, "
            f"quantity={ing.quantity}, cost={ing.cost}"
        )
    lines.append(
        f"    **operations** ({len(prod.operations)}):"
        if prod.operations
        else "    **operations**: []"
    )
    for op in prod.operations:
        lines.append(
            f"      - id={op.id}, operation_id={op.manufacturing_order_operation_id}, "
            f"time={op.time}, cost={op.cost}"
        )
    lines.append(
        f"    **serial_numbers** ({len(prod.serial_numbers)}):"
        if prod.serial_numbers
        else "    **serial_numbers**: []"
    )
    for sn in prod.serial_numbers:
        lines.append(f"      - serial_number={sn.serial_number}")
    return "\n".join(lines)


def _render_mo_list_fields_md(
    response: GetManufacturingOrderResponse,
) -> list[str]:
    """Render every list-shaped field with canonical names + explicit list syntax.

    Empty lists render as ``**field**: []`` (motivation: #346 follow-on —
    no bare section headers that could be misread as scalar values).
    """
    lines: list[str] = []
    # MO-level batch_transactions
    if response.batch_transactions:
        lines.append("")
        lines.append(f"**batch_transactions** ({len(response.batch_transactions)}):")
        for bt in response.batch_transactions:
            lines.append(f"  - batch_id={bt.batch_id}, quantity={bt.quantity}")
    else:
        lines.append("**batch_transactions**: []")
    # MO-level serial_numbers
    if response.serial_numbers:
        lines.append("")
        lines.append(f"**serial_numbers** ({len(response.serial_numbers)}):")
        for sn in response.serial_numbers:
            lines.append(
                f"  - id={sn.id}, serial_number={sn.serial_number}, "
                f"transaction_date={sn.transaction_date}"
            )
    else:
        lines.append("**serial_numbers**: []")
    lines.extend(
        _render_list_field("recipe_rows", response.recipe_rows, _render_recipe_row_md)
    )
    lines.extend(
        _render_list_field(
            "operation_rows", response.operation_rows, _render_operation_row_md
        )
    )
    lines.extend(
        _render_list_field("productions", response.productions, _render_production_md)
    )
    return lines


@observe_tool
@unpack_pydantic_params
async def get_manufacturing_order(
    request: Annotated[GetManufacturingOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Look up a manufacturing order by number or ID with exhaustive detail.

    For multiple manufacturing orders at once, use ``list_manufacturing_orders(ids=[...])`` —
    it returns a summary table and supports all the same filters.

    Returns every field Katana exposes on the manufacturing order (status,
    quantities, costs, timings, timestamps, linked sales order, batch and
    serial transactions) plus the full recipe rows, operation rows, and
    production records. Use with ``list_manufacturing_orders`` for discovery
    workflows; this tool is the single-call path to the rest.

    Provide either order_no (e.g., '#WEB20082 / 1') or order_id.
    """
    response = await _get_manufacturing_order_impl(request, context)

    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2),
            structured_content=response.model_dump(),
        )

    # Labels use the canonical Pydantic field names so LLM consumers can't
    # confuse a section header with the field name (see #346 follow-on).
    md_lines = [f"## MO {response.order_no or response.id}"]
    md_lines.extend(_render_mo_scalar_lines(response))
    md_lines.extend(_render_mo_list_fields_md(response))

    from katana_mcp.tools.tool_result_utils import make_simple_result

    return make_simple_result(
        "\n".join(md_lines),
        structured_data=response.model_dump(),
    )


# ============================================================================
# Tool 3: get_manufacturing_order_recipe
# ============================================================================


class GetManufacturingOrderRecipeRequest(BaseModel):
    """Request to list ingredient rows for a manufacturing order."""

    manufacturing_order_id: int = Field(..., description="Manufacturing order ID")
    format: Literal["markdown", "json"] = Field(
        default="markdown",
        description=(
            "Output format: 'markdown' (default) for human-readable tables; "
            "'json' for structured data consumable by downstream tools/aggregations."
        ),
    )


class GetManufacturingOrderRecipeResponse(BaseModel):
    """Response containing recipe rows for an MO. Each row is exhaustive —
    every field on the generated ``ManufacturingOrderRecipeRow`` attrs model
    is surfaced (see ``RecipeRowInfo``).
    """

    manufacturing_order_id: int
    rows: list[RecipeRowInfo]
    total_count: int


async def _get_manufacturing_order_recipe_impl(
    request: GetManufacturingOrderRecipeRequest, context: Context
) -> GetManufacturingOrderRecipeResponse:
    """Read the ingredient rows for a manufacturing order (exhaustive)."""
    services = get_services(context)
    rows = await _fetch_mo_recipe_rows(services, request.manufacturing_order_id)
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

    Single-MO: pass the ``manufacturing_order_id`` of interest. For recipe rows
    across multiple MOs, call ``get_manufacturing_order`` once per MO — it
    returns recipe rows inline (there is no batch shape for this tool).

    Returns every field Katana exposes on each ``ManufacturingOrderRecipeRow``
    (notes, planned/actual/consumed/remaining quantities, ingredient
    availability + expected date, batch transactions, cost, timestamps) plus
    the resolved SKU. Use this before adding or deleting recipe rows so you
    can identify the rows to modify.
    """
    from katana_mcp.tools.tool_result_utils import make_simple_result

    response = await _get_manufacturing_order_recipe_impl(request, context)

    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2),
            structured_content=response.model_dump(),
        )

    # Labels use the canonical Pydantic field names so LLM consumers can't
    # confuse a section header with the field name (see #346 follow-on).
    if not response.rows:
        md = f"## Recipe for MO {response.manufacturing_order_id}\n**rows**: []"
    else:
        md_lines = [
            f"## Recipe for MO {response.manufacturing_order_id}",
            f"**rows** ({response.total_count}):",
        ]
        for row in response.rows:
            md_lines.append(_render_recipe_row_md(row))
        md = "\n".join(md_lines)

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
        description="Set false to preview, true to add",
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
    """Resolve ``(sku, variant_id)`` inputs to ``(variant_id, sku, display_name)``.

    At least one of ``sku`` or ``variant_id`` must be provided. If both are
    provided, ``variant_id`` takes precedence and ``sku`` is returned as given
    without re-validating that it matches the variant. Raises ``ValueError``
    if neither is provided or if a provided SKU is not found in the cache.
    """
    if variant_id is not None:
        return variant_id, sku, sku or f"variant {variant_id}"
    if not sku:
        raise ValueError("At least one of sku or variant_id must be provided")
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
        description="Set false to preview, true to delete",
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

    await _api_delete_recipe_row(services, request.recipe_row_id)

    return DeleteRecipeRowResponse(
        recipe_row_id=request.recipe_row_id,
        is_preview=False,
        message=f"Removed recipe row {request.recipe_row_id}",
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

    manufacturing_order_ids: CoercedIntList = Field(
        ...,
        min_length=1,
        description=(
            "JSON array of manufacturing order IDs to apply this replacement to, "
            "e.g. [101, 202, 303]."
        ),
    )
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
    remove_row_ids: CoercedIntList = Field(
        default_factory=list,
        description="JSON array of recipe row IDs to delete, e.g. [42, 87].",
    )
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
    notes: str | None = None
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
                for v_id, sku, qty, notes in resolved_new:
                    planned.append(
                        SubOpResult(
                            op_type=OpType.ADD,
                            manufacturing_order_id=mo_id,
                            variant_id=v_id,
                            sku=sku,
                            planned_quantity_per_unit=qty,
                            notes=notes,
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
            for v_id, sku, qty, notes in resolved_new:
                planned.append(
                    SubOpResult(
                        op_type=OpType.ADD,
                        manufacturing_order_id=mo_id,
                        variant_id=v_id,
                        sku=sku,
                        planned_quantity_per_unit=qty,
                        notes=notes,
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
                    notes=spec.notes,
                    group_label=group_label,
                )
            )

    return planned, warnings


async def _execute_batch_update(
    planned: list[SubOpResult],
    request: BatchUpdateRecipesRequest,
    context: Context,
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
    for (mo_id, _group_label), ops in buckets.items():
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
                if op.recipe_row_id is None:
                    raise ValueError("DELETE op requires recipe_row_id")
                await _api_delete_recipe_row(services, op.recipe_row_id)
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
                if op.variant_id is None:
                    raise ValueError("ADD op requires variant_id")
                if op.planned_quantity_per_unit is None:
                    raise ValueError("ADD op requires planned_quantity_per_unit")
                result = await _api_create_recipe_row(
                    services,
                    manufacturing_order_id=mo_id,
                    variant_id=op.variant_id,
                    planned_quantity_per_unit=op.planned_quantity_per_unit,
                    notes=op.notes,
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

    # 0. Upfront estimate — reject oversized batches BEFORE planning fetches
    # recipes for every MO. Each replacement generates (num_components + 1)
    # ops per MO, doubled for delete+add pairing. The threshold is 4x
    # MAX_BATCH_OPS because this estimate deliberately over-counts (the real
    # plan may be smaller once duplicate rows are merged).
    estimate = sum(
        len(rep.manufacturing_order_ids) * (len(rep.new_components) + 1) * 2
        for rep in request.replacements
    ) + sum(len(ch.remove_row_ids) + len(ch.add_variants) for ch in request.changes)
    if estimate > MAX_BATCH_OPS * 4:
        raise ValueError(
            f"Batch estimate is {estimate} operations, which exceeds "
            f"{MAX_BATCH_OPS * 4} before planning. Split into smaller batches "
            "so we don't fetch recipes for hundreds of MOs up front."
        )

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
    confirm=true to execute (single batch operation).

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

    from katana_mcp.tools.prefab_ui import (
        build_batch_recipe_update_ui,
        call_tool_from_request,
    )

    response = await _batch_update_impl(request, context)
    ui = build_batch_recipe_update_ui(
        response.model_dump(),
        request=request.model_dump() if response.is_preview else None,
        confirm_action=(
            call_tool_from_request(
                "batch_update_manufacturing_order_recipes",
                BatchUpdateRecipesRequest,
                overrides={"confirm": True},
            )
            if response.is_preview
            else None
        ),
    )

    return ToolResult(
        content=response.model_dump_json(),
        structured_content=ui,
    )


# ============================================================================
# Tool: list_manufacturing_orders (list-tool pattern v2)
# ============================================================================


class ListManufacturingOrdersRequest(BaseModel):
    """Request to list/filter manufacturing orders (cache-backed)."""

    # Paging
    limit: int = Field(
        default=50,
        ge=1,
        le=250,
        description=(
            "Max rows to return (default 50, min 1, max 250). When `page` is "
            "set, acts as the page size for that request."
        ),
    )
    page: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Page number (1-based). When set, the response includes "
            "`pagination` metadata (total_records, total_pages) computed via "
            "SQL COUNT against the same filter predicate."
        ),
    )

    # Domain filters
    ids: CoercedIntListOpt = Field(
        default=None,
        description=(
            "Filter by explicit list of manufacturing order IDs. "
            "JSON array of integers, e.g. [101, 202, 303]."
        ),
    )
    order_no: str | None = Field(default=None, description="Filter by exact order_no")
    status: GetAllManufacturingOrdersStatus | None = Field(
        default=None,
        description=(
            "Filter by MO status: NOT_STARTED, IN_PROGRESS, BLOCKED, PAUSED, COMPLETED."
        ),
    )
    location_id: int | None = Field(
        default=None, description="Filter by production location ID"
    )
    is_linked_to_sales_order: bool | None = Field(
        default=None,
        description="When set, filters to MOs linked (True) / not linked (False) to a SO.",
    )
    include_deleted: bool | None = Field(
        default=None,
        description="When true, include soft-deleted manufacturing orders.",
    )

    # Time-window filters
    created_after: str | None = Field(
        default=None, description="ISO-8601 datetime lower bound on created_at."
    )
    created_before: str | None = Field(
        default=None, description="ISO-8601 datetime upper bound on created_at."
    )
    updated_after: str | None = Field(
        default=None, description="ISO-8601 datetime lower bound on updated_at."
    )
    updated_before: str | None = Field(
        default=None, description="ISO-8601 datetime upper bound on updated_at."
    )
    production_deadline_after: str | None = Field(
        default=None,
        description=(
            "ISO-8601 datetime lower bound on production_deadline_date — "
            "indexed SQL range filter against the cache."
        ),
    )
    production_deadline_before: str | None = Field(
        default=None,
        description=(
            "ISO-8601 datetime upper bound on production_deadline_date — "
            "indexed SQL range filter against the cache."
        ),
    )

    # Output formatting
    format: Literal["markdown", "json"] = Field(
        default="markdown",
        description=(
            "Output format: 'markdown' (default) for human-readable tables; "
            "'json' for structured data consumable by downstream tools/aggregations."
        ),
    )


class ManufacturingOrderSummary(BaseModel):
    """Summary row for a manufacturing order in a list."""

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
    total_cost: float | None


class ListManufacturingOrdersResponse(BaseModel):
    """Response containing a list of manufacturing orders."""

    orders: list[ManufacturingOrderSummary]
    total_count: int
    pagination: PaginationMeta | None = None


_MANUFACTURING_ORDER_DATE_FIELDS = (
    "created_after",
    "created_before",
    "updated_after",
    "updated_before",
    "production_deadline_after",
    "production_deadline_before",
)


def _apply_manufacturing_order_filters(
    stmt: Any,
    request: ListManufacturingOrdersRequest,
    parsed_dates: dict[str, datetime | None],
) -> Any:
    """Translate request filters into WHERE clauses on a CachedManufacturingOrder query.

    Shared by the data SELECT and the COUNT SELECT so pagination totals
    reflect exactly the same filter set as the data rows. ``parsed_dates``
    must come from :func:`parse_request_dates`.
    """
    from katana_public_api_client.models_pydantic._generated import (
        CachedManufacturingOrder,
        ManufacturingOrderStatus,
    )

    if request.ids is not None:
        stmt = stmt.where(CachedManufacturingOrder.id.in_(request.ids))
    if request.order_no is not None:
        stmt = stmt.where(CachedManufacturingOrder.order_no == request.order_no)
    if request.status is not None:
        # ``GetAllManufacturingOrdersStatus`` (caller) and
        # ``ManufacturingOrderStatus`` (cache column) share string values
        # but are distinct types — coerce_enum round-trips through .value.
        stmt = stmt.where(
            CachedManufacturingOrder.status
            == coerce_enum(request.status, ManufacturingOrderStatus, "status")
        )
    if request.location_id is not None:
        stmt = stmt.where(CachedManufacturingOrder.location_id == request.location_id)
    if request.is_linked_to_sales_order is not None:
        stmt = stmt.where(
            CachedManufacturingOrder.is_linked_to_sales_order
            == request.is_linked_to_sales_order
        )
    if not request.include_deleted:
        stmt = stmt.where(CachedManufacturingOrder.deleted_at.is_(None))

    return apply_date_window_filters(
        stmt,
        parsed_dates,
        ge_pairs={
            "created_after": CachedManufacturingOrder.created_at,
            "updated_after": CachedManufacturingOrder.updated_at,
            "production_deadline_after": CachedManufacturingOrder.production_deadline_date,
        },
        le_pairs={
            "created_before": CachedManufacturingOrder.created_at,
            "updated_before": CachedManufacturingOrder.updated_at,
            "production_deadline_before": CachedManufacturingOrder.production_deadline_date,
        },
    )


async def _list_manufacturing_orders_impl(
    request: ListManufacturingOrdersRequest, context: Context
) -> ListManufacturingOrdersResponse:
    """List manufacturing orders with filters via the typed cache.

    ``ensure_manufacturing_orders_synced`` runs an incremental
    ``updated_at_min`` delta (debounced — see :data:`_SYNC_DEBOUNCE`).
    Filters (including ``production_deadline_*``) translate to indexed
    SQL. See ADR-0018.
    """
    from sqlmodel import func, select

    from katana_mcp.typed_cache import ensure_manufacturing_orders_synced
    from katana_public_api_client.models_pydantic._generated import (
        CachedManufacturingOrder,
    )

    services = get_services(context)

    await ensure_manufacturing_orders_synced(services.client, services.typed_cache)

    parsed_dates = parse_request_dates(request, _MANUFACTURING_ORDER_DATE_FIELDS)

    stmt = select(CachedManufacturingOrder)
    stmt = _apply_manufacturing_order_filters(stmt, request, parsed_dates)
    stmt = stmt.order_by(
        CachedManufacturingOrder.created_at.desc(),
        CachedManufacturingOrder.id.desc(),
    )
    if request.page is not None:
        stmt = stmt.offset((request.page - 1) * request.limit).limit(request.limit)
    else:
        stmt = stmt.limit(request.limit)

    async with services.typed_cache.session() as session:
        data_result = await session.exec(stmt)
        cached_orders: list[CachedManufacturingOrder] = list(data_result.all())

        pagination: PaginationMeta | None = None
        if request.page is not None:
            count_stmt = _apply_manufacturing_order_filters(
                select(func.count()).select_from(CachedManufacturingOrder),
                request,
                parsed_dates,
            )
            total_records = (await session.exec(count_stmt)).one()
            total_pages = (total_records + request.limit - 1) // request.limit
            pagination = PaginationMeta(
                total_records=total_records,
                total_pages=total_pages,
                page=request.page,
                first_page=request.page == 1,
                last_page=request.page >= total_pages,
            )

    summaries: list[ManufacturingOrderSummary] = []
    for mo in cached_orders:
        summaries.append(
            ManufacturingOrderSummary(
                id=mo.id,
                order_no=mo.order_no,
                status=enum_to_str(mo.status),
                variant_id=mo.variant_id,
                planned_quantity=mo.planned_quantity,
                actual_quantity=mo.actual_quantity,
                location_id=mo.location_id,
                order_created_date=iso_or_none(mo.order_created_date),
                production_deadline_date=iso_or_none(mo.production_deadline_date),
                done_date=iso_or_none(mo.done_date),
                is_linked_to_sales_order=mo.is_linked_to_sales_order,
                sales_order_id=mo.sales_order_id,
                total_cost=mo.total_cost,
            )
        )

    return ListManufacturingOrdersResponse(
        orders=summaries, total_count=len(summaries), pagination=pagination
    )


@observe_tool
@unpack_pydantic_params
async def list_manufacturing_orders(
    request: Annotated[ListManufacturingOrdersRequest, Unpack()], context: Context
) -> ToolResult:
    """List manufacturing orders with filters — pass `ids=[1,2,3]` to fetch a specific batch by ID (cache-backed).

    Use this for discovery workflows — find MOs by status, location, linkage
    to a sales order, or within a date window. Returns summary info (order_no,
    status, variant, qty, costs, deadlines).

    **Common filters:**
    - `status="IN_PROGRESS"` — MOs currently being produced
    - `is_linked_to_sales_order=true` — MOs tied to a customer order
    - `location_id=N` — MOs at a specific production location

    **Time windows** (all run as indexed SQL date-range queries):
    - `created_after` / `created_before` — bounds on `created_at`
    - `updated_after` / `updated_before` — bounds on `updated_at`
    - `production_deadline_after` / `production_deadline_before` — bounds
      on `production_deadline_date` (was a client-side post-fetch filter
      pre-cache; now a SQL range filter)

    **Paging:**
    - `limit` caps the number of rows (default 50, min 1).
    - `page=N` returns a single page; the response includes `pagination`
      metadata (total_records, total_pages, first/last flags) computed
      via SQL COUNT against the same filter predicate.

    For full details on a specific MO, use `get_manufacturing_order`.
    For its recipe rows, use `get_manufacturing_order_recipe`.
    """
    response = await _list_manufacturing_orders_impl(request, context)

    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2),
            structured_content=response.model_dump(),
        )

    if not response.orders:
        md = "No manufacturing orders match the given filters."
    else:
        table = format_md_table(
            headers=[
                "Order #",
                "Status",
                "Variant",
                "Planned",
                "Actual",
                "Deadline",
                "Total Cost",
            ],
            rows=[
                [
                    o.order_no or o.id,
                    o.status or "—",
                    o.variant_id if o.variant_id is not None else "—",
                    o.planned_quantity if o.planned_quantity is not None else "—",
                    o.actual_quantity if o.actual_quantity is not None else "—",
                    o.production_deadline_date or "—",
                    f"{o.total_cost:.2f}" if o.total_cost is not None else "—",
                ]
                for o in response.orders
            ],
        )
        md = f"## Manufacturing Orders ({response.total_count})\n\n{table}"

    if response.pagination is not None:
        p = response.pagination
        if p.page is not None and p.total_pages is not None:
            summary = f"\n\nPage {p.page} of {p.total_pages}"
            if p.total_records is not None:
                summary += f" (total: {p.total_records} records)"
            md += summary

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
        meta=UI_META,
    )(create_manufacturing_order)
    mcp.tool(
        tags={"orders", "manufacturing", "read"},
        annotations=_read,
    )(list_manufacturing_orders)
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
        meta=UI_META,
    )(batch_update_manufacturing_order_recipes)
