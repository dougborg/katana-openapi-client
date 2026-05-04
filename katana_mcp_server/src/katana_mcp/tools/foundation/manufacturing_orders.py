"""Manufacturing order management tools for Katana MCP Server.

Tools:
- create_manufacturing_order / get_manufacturing_order /
  list_manufacturing_orders / list_blocking_ingredients /
  get_manufacturing_order_recipe — read-mostly + create.
- modify_manufacturing_order: header + recipe rows + operation rows +
  production records via typed sub-payload slots.
- delete_manufacturing_order: destructive sibling of
  modify_manufacturing_order.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Any, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, Field

from katana_mcp.cache import EntityType
from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools._modification import (
    ConfirmableRequest,
    ModificationResponse,
    compute_field_diff,
    make_response_verifier,
    to_tool_result,
)
from katana_mcp.tools._modification_dispatch import (
    ActionSpec,
    has_any_subpayload,
    make_delete_apply,
    make_patch_apply,
    make_post_apply,
    plan_creates,
    plan_deletes,
    plan_updates,
    run_delete_plan,
    run_modify_plan,
    safe_fetch_for_diff,
    unset_dict,
)
from katana_mcp.tools.list_coercion import (
    CoercedIntListOpt,
    CoercedStrListOpt,
)
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
from katana_mcp.web_urls import katana_web_url

# Modify/delete API endpoints used by ``modify_manufacturing_order`` /
# ``delete_manufacturing_order``. Hoisted to module scope.
from katana_public_api_client.api.manufacturing_order import (
    delete_manufacturing_order as api_delete_manufacturing_order,
    get_manufacturing_order as api_get_manufacturing_order,
    update_manufacturing_order as api_update_manufacturing_order,
)
from katana_public_api_client.api.manufacturing_order_operation import (
    create_manufacturing_order_operation_row as api_create_mo_operation_row,
    delete_manufacturing_order_operation_row as api_delete_mo_operation_row,
    get_manufacturing_order_operation_row as api_get_mo_operation_row,
    update_manufacturing_order_operation_row as api_update_mo_operation_row,
)
from katana_public_api_client.api.manufacturing_order_production import (
    create_manufacturing_order_production as api_create_mo_production,
    delete_manufacturing_order_production as api_delete_mo_production,
    get_manufacturing_order_production as api_get_mo_production,
    update_manufacturing_order_production as api_update_mo_production,
)
from katana_public_api_client.api.manufacturing_order_recipe import (
    create_manufacturing_order_recipe_rows as api_create_mo_recipe_row,
    delete_manufacturing_order_recipe_row as api_delete_mo_recipe_row,
    get_manufacturing_order_recipe_row as api_get_mo_recipe_row,
    update_manufacturing_order_recipe_rows as api_update_mo_recipe_row,
)
from katana_public_api_client.domain.converters import to_unset, unwrap_unset
from katana_public_api_client.models import (
    CreateManufacturingOrderOperationRowRequest as APICreateMOOperationRowRequest,
    CreateManufacturingOrderProductionRequest as APICreateMOProductionRequest,
    CreateManufacturingOrderRecipeRowRequest as APICreateMORecipeRowRequest,
    CreateManufacturingOrderRequest as APICreateManufacturingOrderRequest,
    ManufacturingOperationStatus,
    ManufacturingOperationType,
    ManufacturingOrder,
    ManufacturingOrderOperationRow,
    ManufacturingOrderProduction,
    ManufacturingOrderRecipeRow,
    ManufacturingOrderStatus,
    UpdateManufacturingOrderOperationRowRequest as APIUpdateMOOperationRowRequest,
    UpdateManufacturingOrderProductionRequest as APIUpdateMOProductionRequest,
    UpdateManufacturingOrderRecipeRowRequest as APIUpdateMORecipeRowRequest,
    UpdateManufacturingOrderRequest as APIUpdateManufacturingOrderRequest,
)
from katana_public_api_client.models_pydantic._generated import (
    OutsourcedPurchaseOrderIngredientAvailability,
)
from katana_public_api_client.utils import unwrap_as

logger = get_logger(__name__)


# ============================================================================
# Tool: create_manufacturing_order
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
    katana_url: str | None = None


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
            katana_url=katana_web_url("manufacturing_order", mo.id),
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
    )

    response = await _create_manufacturing_order_impl(request, context)

    order_dict = response.model_dump()
    if response.is_preview:
        ui = build_order_preview_ui(
            order_dict,
            "Manufacturing Order",
            confirm_request=request,
            confirm_tool="create_manufacturing_order",
        )
    else:
        ui = build_order_created_ui(order_dict, "Manufacturing Order")

    return make_tool_result(response, ui=ui)


# ============================================================================
# Tool: get_manufacturing_order
# ============================================================================

# Recipe-row metadata fields stripped from the compact response. These have
# no value for triage workflows (they're fetched per-MO so reading them adds
# no provenance information that wasn't already on the parent MO).
_ROW_METADATA_FIELDS = frozenset({"created_at", "updated_at", "deleted_at"})

# Recipe rows in these availability states are considered "blocking" for the
# procurement triage view. IN_STOCK / PROCESSED / NOT_APPLICABLE / NO_RECIPE
# are deliberately excluded:
#   - IN_STOCK: material on hand, not blocking.
#   - PROCESSED: already consumed by a production run.
#   - NOT_APPLICABLE: not an inventory-tracked item (e.g., a service line).
#   - NO_RECIPE: BOM metadata problem, not a procurement problem.
# Stored as the enum's string values so it works for both Python comparison
# (against ``RecipeRowInfo.ingredient_availability: str``) and the SQL ``IN``
# clause against the cached ``ingredient_availability`` column.
_BLOCKING_AVAILABILITY: frozenset[str] = frozenset(
    {
        OutsourcedPurchaseOrderIngredientAvailability.not_available.value,
        OutsourcedPurchaseOrderIngredientAvailability.expected.value,
    }
)


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
    include_rows: Literal["all", "blocking", "none"] = Field(
        default="blocking",
        description=(
            "Recipe-row projection. 'blocking' (default) returns only rows whose "
            "ingredient_availability is NOT_AVAILABLE or EXPECTED — the procurement "
            "triage view. 'all' returns every recipe row. 'none' omits the array "
            "and skips the recipe-row API call entirely."
        ),
    )
    include_operation_rows: bool = Field(
        default=False,
        description=(
            "When true, fetch and include operation_rows. Off by default to keep "
            "the response under inline tool-result limits — operation rows are bulky "
            "and irrelevant to procurement triage."
        ),
    )
    include_productions: bool = Field(
        default=False,
        description=(
            "When true, fetch and include production records. Off by default — "
            "production history is the largest contributor to MO payload size."
        ),
    )
    verbose: bool = Field(
        default=False,
        description=(
            "When true, restore metadata fields stripped from the compact view: "
            "created_at, updated_at, deleted_at, and empty batch_transactions on "
            "every nested row. Use with include_rows='all', include_operation_rows=True, "
            "and include_productions=True to reproduce the legacy exhaustive payload."
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
    katana_url: str | None = None
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

    # One batched IN-clause SQLite read instead of one read per recipe row —
    # a full-bike Mayhem MO has ~30 rows, all looked up by variant_id.
    variant_ids = {
        v_id
        for v_id in (unwrap_unset(row.variant_id, None) for row in raw_rows)
        if v_id is not None
    }
    variants = await services.cache.get_many_by_ids(EntityType.VARIANT, variant_ids)
    return [
        _recipe_row_info_from_attrs(
            row,
            (variants.get(v_id) or {}).get("sku")
            if (v_id := unwrap_unset(row.variant_id, None)) is not None
            else None,
        )
        for row in raw_rows
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
        katana_url=katana_web_url("manufacturing_order", mo.id),
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
    """Look up a manufacturing order by order number or ID.

    Compact-by-default: ``include_rows='blocking'`` filters recipe rows to
    procurement-actionable rows; operation rows and production records are
    omitted unless explicitly requested. Each related-resource fetch is a
    separate HTTP call (cache-first migration tracked in #342) — gating on
    the ``include_*`` flags also skips the upstream call when the data
    isn't needed.
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

    # Gate each related-resource fetch on its include flag. asyncio.gather
    # over the requested subset keeps the parallel-fetch advantage while
    # avoiding wasted HTTP calls when the caller doesn't want the data.
    fetch_recipe = request.include_rows != "none"
    fetchers: list[Any] = [
        _fetch_mo_recipe_rows(services, mo.id) if fetch_recipe else none_coro(),
        _fetch_mo_operation_rows(services, mo.id)
        if request.include_operation_rows
        else none_coro(),
        _fetch_mo_productions(services, mo.id)
        if request.include_productions
        else none_coro(),
    ]
    recipe_rows, operation_rows, productions = await asyncio.gather(*fetchers)
    recipe_rows = recipe_rows or []
    operation_rows = operation_rows or []
    productions = productions or []

    if request.include_rows == "blocking":
        recipe_rows = [
            r
            for r in recipe_rows
            if r.ingredient_availability in _BLOCKING_AVAILABILITY
        ]

    return _build_mo_response(mo, recipe_rows, operation_rows, productions)


def _render_mo_scalar_lines(
    response: GetManufacturingOrderResponse, *, verbose: bool = True
) -> list[str]:
    """Render every scalar MO field as ``**field_name**: value`` lines.

    Uses canonical Pydantic field names so LLM consumers can't confuse a
    prettified label with a different field name (see #346 follow-on).
    """
    scalar_fields: tuple[str, ...] = (
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
    )
    if verbose:
        scalar_fields += ("created_at", "updated_at", "deleted_at")
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


def _render_recipe_row_md(row: RecipeRowInfo, *, verbose: bool = True) -> str:
    """Render a single recipe row as a compact multi-line block."""
    lines = [f"  - **id**: {row.id}"]
    scalar_fields: tuple[str, ...] = (
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
    )
    if verbose:
        scalar_fields += ("created_at", "updated_at", "deleted_at")
    for fname in scalar_fields:
        val = getattr(row, fname)
        if val is None or val == "":
            continue
        lines.append(f"    **{fname}**: {val}")
    if row.batch_transactions:
        lines.append(f"    **batch_transactions** ({len(row.batch_transactions)}):")
        for bt in row.batch_transactions:
            lines.append(f"      - batch_id={bt.batch_id}, quantity={bt.quantity}")
    elif verbose:
        lines.append("    **batch_transactions**: []")
    return "\n".join(lines)


def _render_operation_row_md(row: OperationRowInfo, *, verbose: bool = True) -> str:
    """Render a single operation row as a compact multi-line block."""
    lines = [f"  - **id**: {row.id}"]
    scalar_fields: tuple[str, ...] = (
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
    )
    if verbose:
        scalar_fields += ("created_at", "updated_at", "deleted_at")
    for fname in scalar_fields:
        val = getattr(row, fname)
        if val is None or val == "":
            continue
        lines.append(f"    **{fname}**: {val}")
    for list_name in ("assigned_operators", "completed_by_operators"):
        items = getattr(row, list_name)
        if not items:
            if verbose:
                lines.append(f"    **{list_name}**: []")
            continue
        lines.append(f"    **{list_name}** ({len(items)}):")
        for op in items:
            lines.append(f"      - operator_id={op.operator_id}, name={op.name}")
    return "\n".join(lines)


def _render_production_md(prod: ProductionInfo, *, verbose: bool = True) -> str:
    """Render a single production record as a compact multi-line block."""
    lines = [f"  - **id**: {prod.id}"]
    scalar_fields: tuple[str, ...] = (
        "manufacturing_order_id",
        "factory_id",
        "quantity",
        "production_date",
    )
    if verbose:
        scalar_fields += ("created_at", "updated_at", "deleted_at")
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
    *,
    verbose: bool = True,
    include_rows: Literal["all", "blocking", "none"] = "all",
    include_operation_rows: bool = True,
    include_productions: bool = True,
) -> list[str]:
    """Render every list-shaped field with canonical names + explicit list syntax.

    Empty lists render as ``**field**: []`` (motivation: #346 follow-on —
    no bare section headers that could be misread as scalar values) when
    ``verbose=True``. In compact mode, empty/omitted collections are
    suppressed entirely so the response stays under inline tool-result
    limits.
    """
    lines: list[str] = []
    # MO-level batch_transactions
    if response.batch_transactions:
        lines.append("")
        lines.append(f"**batch_transactions** ({len(response.batch_transactions)}):")
        for bt in response.batch_transactions:
            lines.append(f"  - batch_id={bt.batch_id}, quantity={bt.quantity}")
    elif verbose:
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
    elif verbose:
        lines.append("**serial_numbers**: []")

    # Render each collection with the canonical field-name label. In
    # compact mode, an empty/omitted collection is suppressed entirely
    # (no ``**field**: []`` placeholder) so the response stays small. The
    # blocking-filter is surfaced as a sibling annotation rather than
    # decorating the field name, so consumers parsing the markdown still
    # see the canonical ``recipe_rows`` header.
    if include_rows != "none" and (verbose or response.recipe_rows):
        if include_rows == "blocking":
            lines.append("")
            lines.append("_recipe_rows filtered to blocking rows only_")
        lines.extend(
            _render_list_field(
                "recipe_rows",
                response.recipe_rows,
                lambda r: _render_recipe_row_md(r, verbose=verbose),
            )
        )
    if include_operation_rows and (verbose or response.operation_rows):
        lines.extend(
            _render_list_field(
                "operation_rows",
                response.operation_rows,
                lambda r: _render_operation_row_md(r, verbose=verbose),
            )
        )
    if include_productions and (verbose or response.productions):
        lines.extend(
            _render_list_field(
                "productions",
                response.productions,
                lambda p: _render_production_md(p, verbose=verbose),
            )
        )
    return lines


@observe_tool
@unpack_pydantic_params
async def get_manufacturing_order(
    request: Annotated[GetManufacturingOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Look up a manufacturing order by number or ID, compact-by-default.

    The default response shape is built for procurement triage: every scalar
    MO field, plus only the *blocking* recipe rows (those with
    ``ingredient_availability`` of NOT_AVAILABLE / EXPECTED), with per-row
    metadata stripped. Operation rows and production records are omitted
    unless ``include_operation_rows`` / ``include_productions`` are set.

    Toggle the projection with the request flags:
      * ``include_rows`` — ``"blocking"`` (default), ``"all"``, or ``"none"``.
      * ``include_operation_rows`` / ``include_productions`` — bring the
        respective collections back; each triggers its own upstream fetch.
      * ``verbose`` — restore stripped metadata (created_at/updated_at/deleted_at)
        and explicit empty-list placeholders. Combined with all three
        ``include_*`` flags this reproduces the legacy exhaustive payload
        byte-for-byte.

    For multiple manufacturing orders at once, use
    ``list_manufacturing_orders(ids=[...])`` — it returns a summary table
    that already exposes ``ingredient_availability`` so you can pick which
    MOs to drill into. To roll up blocking SKUs across many MOs, use
    ``list_blocking_ingredients``.

    Provide either ``order_no`` (e.g., '#WEB20082 / 1') or ``order_id``.
    """
    response = await _get_manufacturing_order_impl(request, context)

    # In compact mode, prune null fields and per-row metadata from the JSON
    # output so the response fits under inline tool-result limits. The
    # production-record shape mixes scalar metadata to drop with nested
    # collections to descend into; pydantic accepts that as a dict that
    # mixes ``True`` (exclude leaf) with nested ``{"__all__": ...}`` dicts.
    # Collections the caller explicitly opted out of are dropped entirely
    # (rather than serialized as ``[]``) so the documented "omit" contract
    # actually holds in the JSON payload.
    dump_kwargs: dict[str, Any] = {}
    exclude: dict[str, Any] = {}
    if request.include_rows == "none":
        exclude["recipe_rows"] = True
    elif not request.verbose:
        exclude["recipe_rows"] = {"__all__": set(_ROW_METADATA_FIELDS)}
    if not request.include_operation_rows:
        exclude["operation_rows"] = True
    elif not request.verbose:
        exclude["operation_rows"] = {"__all__": set(_ROW_METADATA_FIELDS)}
    if not request.include_productions:
        exclude["productions"] = True
    elif not request.verbose:
        production_exclude: dict[str, Any] = dict.fromkeys(_ROW_METADATA_FIELDS, True)
        production_exclude["ingredients"] = {"__all__": set(_ROW_METADATA_FIELDS)}
        production_exclude["operations"] = {"__all__": set(_ROW_METADATA_FIELDS)}
        exclude["productions"] = {"__all__": production_exclude}
    if not request.verbose:
        dump_kwargs["exclude_none"] = True
    if exclude:
        dump_kwargs["exclude"] = exclude

    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2, **dump_kwargs),
            structured_content=response.model_dump(**dump_kwargs),
        )

    # Labels use the canonical Pydantic field names so LLM consumers can't
    # confuse a section header with the field name (see #346 follow-on).
    md_lines = [f"## MO {response.order_no or response.id}"]
    md_lines.extend(_render_mo_scalar_lines(response, verbose=request.verbose))
    md_lines.extend(
        _render_mo_list_fields_md(
            response,
            verbose=request.verbose,
            include_rows=request.include_rows,
            include_operation_rows=request.include_operation_rows,
            include_productions=request.include_productions,
        )
    )

    return make_simple_result(
        "\n".join(md_lines),
        structured_data=response.model_dump(**dump_kwargs),
    )


# ============================================================================
# Tool: get_manufacturing_order_recipe
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
    status: ManufacturingOrderStatus | None = Field(
        default=None,
        description=(
            "Filter by MO status: NOT_STARTED, BLOCKED, IN_PROGRESS, "
            "PARTIALLY_COMPLETED, DONE."
        ),
    )
    location_id: int | None = Field(
        default=None, description="Filter by production location ID"
    )
    variant_ids: CoercedIntListOpt = Field(
        default=None,
        description=(
            "Filter to MOs producing any of the given variant IDs. "
            "JSON array of integers, e.g. [2101, 2102]. Resolve a SKU to "
            "its variant_id via `search_items` or `get_variant_details` "
            "first, then pass the IDs here."
        ),
    )
    sales_order_ids: CoercedIntListOpt = Field(
        default=None,
        description=(
            "Filter to MOs linked to any of the given sales order IDs. "
            "JSON array of integers, e.g. [10000, 10001]. More precise "
            "than `is_linked_to_sales_order=true` when you already know "
            "the SO IDs."
        ),
    )
    ingredient_availability: OutsourcedPurchaseOrderIngredientAvailability | None = (
        Field(
            default=None,
            description=(
                "Filter by rolled-up MO ingredient availability: "
                "PROCESSED, IN_STOCK, NOT_AVAILABLE, EXPECTED, NO_RECIPE, "
                "NOT_APPLICABLE. Use NOT_AVAILABLE / EXPECTED to find MOs "
                "blocked on materials."
            ),
        )
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
    ingredient_availability: str | None
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
    katana_url: str | None = None


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
    )

    if request.ids is not None:
        stmt = stmt.where(CachedManufacturingOrder.id.in_(request.ids))
    if request.order_no is not None:
        stmt = stmt.where(CachedManufacturingOrder.order_no == request.order_no)
    if request.status is not None:
        stmt = stmt.where(CachedManufacturingOrder.status == request.status)
    if request.location_id is not None:
        stmt = stmt.where(CachedManufacturingOrder.location_id == request.location_id)
    if request.variant_ids is not None:
        stmt = stmt.where(CachedManufacturingOrder.variant_id.in_(request.variant_ids))
    if request.sales_order_ids is not None:
        stmt = stmt.where(
            CachedManufacturingOrder.sales_order_id.in_(request.sales_order_ids)
        )
    if request.ingredient_availability is not None:
        stmt = stmt.where(
            CachedManufacturingOrder.ingredient_availability
            == coerce_enum(
                request.ingredient_availability,
                OutsourcedPurchaseOrderIngredientAvailability,
                "ingredient_availability",
            )
        )
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
                ingredient_availability=enum_to_str(mo.ingredient_availability),
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
                katana_url=katana_web_url("manufacturing_order", mo.id),
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
    - `variant_ids=[2101, 2102]` — MOs producing specific variants. To
      filter by SKU, resolve the SKU to its `variant_id` first via
      `search_items` or `get_variant_details`, then pass the IDs here.
    - `sales_order_ids=[10000, 10001]` — MOs linked to specific SOs
    - `ingredient_availability="NOT_AVAILABLE"` — MOs blocked on materials
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
                "Ingredients",
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
                    o.ingredient_availability or "—",
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


# ============================================================================
# Tool: list_blocking_ingredients
# ============================================================================


class ListBlockingIngredientsRequest(BaseModel):
    """Request to roll up blocking-ingredient rows across manufacturing orders."""

    mo_status: CoercedStrListOpt = Field(
        default=None,
        description=(
            "MO statuses to scope the rollup. JSON array (or CSV string) of "
            "ManufacturingOrderStatus values: NOT_STARTED, BLOCKED, IN_PROGRESS, "
            'PARTIALLY_COMPLETED, DONE. Example: ["NOT_STARTED", "IN_PROGRESS"]. '
            "Defaults to NOT_STARTED + IN_PROGRESS — the active queue procurement "
            "actually cares about."
        ),
    )
    mo_ids: CoercedIntListOpt = Field(
        default=None,
        description=(
            "Restrict the rollup to a specific list of MO IDs. JSON array of "
            "integers, e.g. [101, 202, 303]."
        ),
    )
    mo_order_nos: CoercedStrListOpt = Field(
        default=None,
        description=(
            "Restrict the rollup to MOs with these order_no values. JSON array "
            'of strings, e.g. ["#WEB20402 / 1", "#WEB20462 / 2"].'
        ),
    )
    location_id: int | None = Field(
        default=None,
        description="Restrict the rollup to MOs at this production location.",
    )
    production_deadline_after: str | None = Field(
        default=None,
        description="ISO-8601 datetime lower bound on production_deadline_date.",
    )
    production_deadline_before: str | None = Field(
        default=None,
        description="ISO-8601 datetime upper bound on production_deadline_date.",
    )
    group_by: Literal["variant", "mo"] = Field(
        default="variant",
        description=(
            "Aggregation axis. 'variant' (default) returns one row per blocking "
            "SKU with the count of affected MOs and total quantity needed — the "
            "procurement-priority view. 'mo' returns one block per MO with its "
            "blocking rows, preserving per-row detail."
        ),
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Max aggregate rows to return (default 100, max 500).",
    )
    format: Literal["markdown", "json"] = Field(
        default="markdown",
        description=(
            "Output format: 'markdown' (default) for human-readable tables; "
            "'json' for structured data."
        ),
    )


class BlockingRow(BaseModel):
    """One blocking recipe-row entry within a per-MO grouping."""

    recipe_row_id: int
    variant_id: int | None
    sku: str | None
    planned_quantity_per_unit: float | None
    total_remaining_quantity: float | None
    ingredient_availability: str | None
    ingredient_expected_date: str | None


class BlockingIngredientByMO(BaseModel):
    """A manufacturing order with at least one blocking recipe row."""

    manufacturing_order_id: int
    order_no: str | None
    status: str | None
    production_deadline_date: str | None
    blocking_rows: list[BlockingRow]


class BlockingIngredientByVariant(BaseModel):
    """A SKU rolled up across the MOs it's blocking."""

    variant_id: int
    sku: str | None
    affected_mo_count: int
    affected_mo_order_nos: list[str]
    total_planned_quantity: float
    total_remaining_quantity: float
    earliest_expected_date: str | None


class ListBlockingIngredientsResponse(BaseModel):
    """Aggregate response for ``list_blocking_ingredients``.

    Exactly one of ``by_variant`` / ``by_mo`` is populated based on the
    request's ``group_by`` setting.
    """

    by_variant: list[BlockingIngredientByVariant] | None = None
    by_mo: list[BlockingIngredientByMO] | None = None
    total_blocking_rows: int
    total_affected_mos: int


@dataclass
class _VariantAggregate:
    """In-loop accumulator for the variant-rollup branch of ``list_blocking_ingredients``.

    ``mo_ids`` and ``order_nos`` are tracked separately because the
    affected-MO count must reflect every blocked MO regardless of whether
    Katana populated its ``order_no`` (rare but possible — e.g., MOs created
    via API before an order_no was assigned). Display lists only show the
    populated order numbers.
    """

    mo_ids: set[int] = field(default_factory=set)
    order_nos: set[str] = field(default_factory=set)
    planned: float = 0.0
    remaining: float = 0.0
    earliest: datetime | None = None


def _coerce_status_filter(
    statuses: list[str] | None,
) -> list[Any]:
    """Translate request-side status strings to the cached enum used in queries.

    Default to the active-procurement scope (NOT_STARTED + IN_PROGRESS) when
    the caller doesn't pin one. ``coerce_enum`` raises ``ValueError`` if a
    string isn't a valid ``ManufacturingOrderStatus`` member, so an LLM that
    sends, say, ``["IN-PROGRESS"]`` (hyphen) gets a clear schema-boundary error.
    """
    from katana_public_api_client.models_pydantic._generated import (
        ManufacturingOrderStatus,
    )

    if statuses is None:
        return [
            ManufacturingOrderStatus.not_started,
            ManufacturingOrderStatus.in_progress,
        ]
    return [coerce_enum(s, ManufacturingOrderStatus, "mo_status") for s in statuses]


async def _list_blocking_ingredients_impl(
    request: ListBlockingIngredientsRequest, context: Context
) -> ListBlockingIngredientsResponse:
    """Aggregate blocking recipe rows across MOs from the typed cache.

    The cache holds both ``CachedManufacturingOrder`` and
    ``CachedManufacturingOrderRecipeRow`` already (synced by the velocity
    report and by sibling tools); the rollup is a single SQL join + filter.
    Variant SKUs come from the legacy in-memory ``CatalogCache`` since
    variants don't have a typed-cache table yet.
    """
    from sqlmodel import select

    from katana_mcp.typed_cache import ensure_manufacturing_orders_synced
    from katana_public_api_client.models_pydantic._generated import (
        CachedManufacturingOrder,
        CachedManufacturingOrderRecipeRow,
    )

    services = get_services(context)

    # MO sync fans out to recipe rows via ``EntitySpec.related_specs``.
    await ensure_manufacturing_orders_synced(services.client, services.typed_cache)

    parsed_dates = parse_request_dates(
        request, ("production_deadline_after", "production_deadline_before")
    )

    statuses = _coerce_status_filter(request.mo_status)

    # Fetch (recipe_row, mo) pairs for any MO/row in scope. Filtering happens
    # at the SQL layer to keep the wire-payload off the Python heap.
    stmt = (
        select(CachedManufacturingOrderRecipeRow, CachedManufacturingOrder)
        .join(
            CachedManufacturingOrder,
            CachedManufacturingOrder.id
            == CachedManufacturingOrderRecipeRow.manufacturing_order_id,
        )
        .where(CachedManufacturingOrder.deleted_at.is_(None))
        .where(CachedManufacturingOrderRecipeRow.deleted_at.is_(None))
        .where(CachedManufacturingOrder.status.in_(statuses))
        .where(
            CachedManufacturingOrderRecipeRow.ingredient_availability.in_(
                list(_BLOCKING_AVAILABILITY)
            )
        )
    )
    if request.mo_ids is not None:
        stmt = stmt.where(CachedManufacturingOrder.id.in_(request.mo_ids))
    if request.mo_order_nos is not None:
        stmt = stmt.where(CachedManufacturingOrder.order_no.in_(request.mo_order_nos))
    if request.location_id is not None:
        stmt = stmt.where(CachedManufacturingOrder.location_id == request.location_id)
    stmt = apply_date_window_filters(
        stmt,
        parsed_dates,
        ge_pairs={
            "production_deadline_after": CachedManufacturingOrder.production_deadline_date,
        },
        le_pairs={
            "production_deadline_before": CachedManufacturingOrder.production_deadline_date,
        },
    )

    async with services.typed_cache.session() as session:
        result = await session.exec(stmt)
        pairs: list[tuple[Any, Any]] = list(result.all())

    total_blocking_rows = len(pairs)
    total_affected_mos = len({mo.id for _row, mo in pairs})

    # Aggregate first, slice to ``limit`` second, resolve SKUs third — only
    # the variants that survived the limit hit the legacy catalog cache.
    # Avoids an N-row SQLite read when the caller wants the top-N rollup
    # but the join produced thousands of recipe rows.
    if request.group_by == "mo":
        by_mo_map: dict[int, BlockingIngredientByMO] = {}
        for row, mo in pairs:
            entry = by_mo_map.get(mo.id)
            if entry is None:
                entry = BlockingIngredientByMO(
                    manufacturing_order_id=mo.id,
                    order_no=mo.order_no,
                    status=enum_to_str(mo.status),
                    production_deadline_date=iso_or_none(mo.production_deadline_date),
                    blocking_rows=[],
                )
                by_mo_map[mo.id] = entry
            entry.blocking_rows.append(
                BlockingRow(
                    recipe_row_id=row.id,
                    variant_id=row.variant_id,
                    sku=None,  # filled in below after slicing
                    planned_quantity_per_unit=row.planned_quantity_per_unit,
                    total_remaining_quantity=row.total_remaining_quantity,
                    # WHERE clause guarantees ingredient_availability is set
                    # to one of the blocking enum values; enum_to_str returns
                    # the canonical string for those.
                    ingredient_availability=enum_to_str(row.ingredient_availability),
                    ingredient_expected_date=iso_or_none(row.ingredient_expected_date),
                )
            )
        # Earliest deadline first — that's the procurement priority order.
        by_mo = sorted(
            by_mo_map.values(),
            key=lambda e: e.production_deadline_date or "9999-12-31",
        )[: request.limit]
        kept_variant_ids = {
            br.variant_id
            for entry in by_mo
            for br in entry.blocking_rows
            if br.variant_id is not None
        }
        sku_by_variant = await _resolve_variant_skus(services, kept_variant_ids)
        for entry in by_mo:
            for br in entry.blocking_rows:
                if br.variant_id is not None:
                    br.sku = sku_by_variant.get(br.variant_id)
        return ListBlockingIngredientsResponse(
            by_mo=by_mo,
            total_blocking_rows=total_blocking_rows,
            total_affected_mos=total_affected_mos,
        )

    # group_by == "variant"
    agg: dict[int, _VariantAggregate] = {}
    for row, mo in pairs:
        if row.variant_id is None:
            continue
        bucket = agg.setdefault(row.variant_id, _VariantAggregate())
        bucket.mo_ids.add(mo.id)
        if mo.order_no:
            bucket.order_nos.add(mo.order_no)
        per_unit = row.planned_quantity_per_unit or 0.0
        mo_qty = mo.planned_quantity or 0.0
        bucket.planned += float(per_unit) * float(mo_qty)
        bucket.remaining += float(row.total_remaining_quantity or 0.0)
        if row.ingredient_expected_date is not None and (
            bucket.earliest is None or row.ingredient_expected_date < bucket.earliest
        ):
            bucket.earliest = row.ingredient_expected_date

    by_variant: list[BlockingIngredientByVariant] = [
        BlockingIngredientByVariant(
            variant_id=vid,
            sku=None,  # filled in below after slicing
            affected_mo_count=len(bucket.mo_ids),
            affected_mo_order_nos=sorted(bucket.order_nos),
            total_planned_quantity=bucket.planned,
            total_remaining_quantity=bucket.remaining,
            earliest_expected_date=iso_or_none(bucket.earliest),
        )
        for vid, bucket in agg.items()
    ]
    # Most-affected SKUs first; ties broken by total remaining quantity.
    by_variant.sort(key=lambda v: (-v.affected_mo_count, -v.total_remaining_quantity))
    by_variant = by_variant[: request.limit]
    sku_by_variant = await _resolve_variant_skus(
        services, {v.variant_id for v in by_variant}
    )
    for v in by_variant:
        v.sku = sku_by_variant.get(v.variant_id)

    return ListBlockingIngredientsResponse(
        by_variant=by_variant,
        total_blocking_rows=total_blocking_rows,
        total_affected_mos=total_affected_mos,
    )


async def _resolve_variant_skus(
    services: Any, variant_ids: set[int] | frozenset[int]
) -> dict[int, str | None]:
    """Resolve SKUs for the given variant IDs via the legacy catalog cache.

    Returns ``{variant_id: sku_or_None}``. Empty input → empty dict (no
    catalog reads). Issues one batched SQL ``IN``-clause read; missing
    variants map to ``None``. Callers should aggregate/sort/slice first
    so this only fires for the variants surfaced in the response.
    """
    if not variant_ids:
        return {}
    variants = await services.cache.get_many_by_ids(EntityType.VARIANT, variant_ids)
    return {vid: (variants.get(vid) or {}).get("sku") for vid in variant_ids}


@observe_tool
@unpack_pydantic_params
async def list_blocking_ingredients(
    request: Annotated[ListBlockingIngredientsRequest, Unpack()], context: Context
) -> ToolResult:
    """Roll up blocking-ingredient recipe rows across manufacturing orders.

    Answers "what should procurement order first?" by aggregating recipe
    rows whose ``ingredient_availability`` is NOT_AVAILABLE or EXPECTED
    across active MOs. Cache-backed: a single typed-cache join, no per-MO
    fan-out.

    **Default scope:** NOT_STARTED + IN_PROGRESS MOs. Override via ``mo_status``.

    **group_by="variant"** (default) — one row per SKU, sorted by impact:

    | SKU | Variant ID | Affected MOs | Total Planned | Total Remaining | Earliest Expected |

    **group_by="mo"** — one block per MO, sorted by deadline. Useful when
    you need per-row detail (notes, exact remaining qty per row).
    """
    response = await _list_blocking_ingredients_impl(request, context)

    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2, exclude_none=True),
            structured_content=response.model_dump(exclude_none=True),
        )

    if request.group_by == "variant":
        rows = response.by_variant or []
        if not rows:
            md = (
                f"## Blocking Ingredients\n\nNo blocking recipe rows in scope "
                f"(scanned {response.total_blocking_rows} blocking row(s) across "
                f"{response.total_affected_mos} MO(s))."
            )
        else:
            table = format_md_table(
                headers=[
                    "SKU",
                    "Variant ID",
                    "Affected MOs",
                    "Total Planned",
                    "Total Remaining",
                    "Earliest Expected",
                    "Order #s",
                ],
                rows=[
                    [
                        v.sku or "—",
                        v.variant_id,
                        v.affected_mo_count,
                        f"{v.total_planned_quantity:g}",
                        f"{v.total_remaining_quantity:g}",
                        v.earliest_expected_date or "—",
                        ", ".join(v.affected_mo_order_nos[:5])
                        + (
                            f" (+{len(v.affected_mo_order_nos) - 5} more)"
                            if len(v.affected_mo_order_nos) > 5
                            else ""
                        ),
                    ]
                    for v in rows
                ],
            )
            md = (
                f"## Blocking Ingredients by Variant ({len(rows)} variant(s) "
                f"across {response.total_affected_mos} affected MO(s), "
                f"{response.total_blocking_rows} blocking row(s))\n\n{table}"
            )
    else:
        mos = response.by_mo or []
        if not mos:
            md = "## Blocking Ingredients\n\nNo blocking recipe rows in scope."
        else:
            sections: list[str] = [
                f"## Blocking Ingredients by MO ({len(mos)} MO(s), "
                f"{response.total_blocking_rows} blocking row(s))"
            ]
            for entry in mos:
                deadline = entry.production_deadline_date or "—"
                sections.append(
                    f"\n### {entry.order_no or entry.manufacturing_order_id} "
                    f"(status: {entry.status or '—'}, deadline: {deadline})"
                )
                sections.append(
                    format_md_table(
                        headers=[
                            "SKU",
                            "Variant ID",
                            "Per-Unit",
                            "Remaining",
                            "Availability",
                            "Expected",
                        ],
                        rows=[
                            [
                                r.sku or "—",
                                r.variant_id if r.variant_id is not None else "—",
                                r.planned_quantity_per_unit
                                if r.planned_quantity_per_unit is not None
                                else "—",
                                r.total_remaining_quantity
                                if r.total_remaining_quantity is not None
                                else "—",
                                r.ingredient_availability or "—",
                                r.ingredient_expected_date or "—",
                            ]
                            for r in entry.blocking_rows
                        ],
                    )
                )
            md = "\n".join(sections)

    return make_simple_result(
        md, structured_data=response.model_dump(exclude_none=True)
    )


# ============================================================================
# Tool: modify_manufacturing_order — unified modification surface
# ============================================================================


class MOOperation(StrEnum):
    """Operation names emitted on ActionSpecs by ``modify_manufacturing_order``
    / ``delete_manufacturing_order`` plan builders."""

    UPDATE_HEADER = "update_header"
    DELETE = "delete"
    ADD_RECIPE_ROW = "add_recipe_row"
    UPDATE_RECIPE_ROW = "update_recipe_row"
    DELETE_RECIPE_ROW = "delete_recipe_row"
    ADD_OPERATION_ROW = "add_operation_row"
    UPDATE_OPERATION_ROW = "update_operation_row"
    DELETE_OPERATION_ROW = "delete_operation_row"
    ADD_PRODUCTION = "add_production"
    UPDATE_PRODUCTION = "update_production"
    DELETE_PRODUCTION = "delete_production"


# Tool-facing literals — values match the API StrEnum's ``.value`` directly,
# so ``EnumClass(literal)`` resolves the enum without a lookup table.
ManufacturingOrderStatusLiteral = Literal[
    "NOT_STARTED", "IN_PROGRESS", "DONE", "BLOCKED", "PARTIALLY_COMPLETED"
]
ManufacturingOperationStatusLiteral = Literal[
    "NOT_STARTED", "IN_PROGRESS", "PAUSED", "BLOCKED", "COMPLETED"
]
# Operation row type mirrors Katana's API enum exactly: ``fixed``,
# ``perUnit``, ``process``, ``setup`` (lowercase + camelCase mix).
ManufacturingOperationTypeLiteral = Literal["fixed", "perUnit", "process", "setup"]


# ----------------------------------------------------------------------------
# Diff-context fetchers
# ----------------------------------------------------------------------------


async def _fetch_manufacturing_order_attrs(
    services: Any, mo_id: int
) -> ManufacturingOrder | None:
    return await safe_fetch_for_diff(
        api_get_manufacturing_order,
        services,
        mo_id,
        return_type=ManufacturingOrder,
        label="manufacturing order",
    )


async def _fetch_mo_recipe_row(
    services: Any, row_id: int
) -> ManufacturingOrderRecipeRow | None:
    return await safe_fetch_for_diff(
        api_get_mo_recipe_row,
        services,
        row_id,
        return_type=ManufacturingOrderRecipeRow,
        label="MO recipe row",
    )


async def _fetch_mo_operation_row(
    services: Any, row_id: int
) -> ManufacturingOrderOperationRow | None:
    return await safe_fetch_for_diff(
        api_get_mo_operation_row,
        services,
        row_id,
        return_type=ManufacturingOrderOperationRow,
        label="MO operation row",
    )


async def _fetch_mo_production(
    services: Any, prod_id: int
) -> ManufacturingOrderProduction | None:
    return await safe_fetch_for_diff(
        api_get_mo_production,
        services,
        prod_id,
        return_type=ManufacturingOrderProduction,
        label="MO production",
    )


# ----------------------------------------------------------------------------
# Sub-payload models
# ----------------------------------------------------------------------------


class MOHeaderPatch(BaseModel):
    """Header fields to patch on an MO. Status is included here — Katana's
    PATCH /manufacturing_orders/{id} accepts it as a regular field."""

    order_no: str | None = Field(default=None)
    variant_id: int | None = Field(default=None)
    location_id: int | None = Field(default=None)
    status: ManufacturingOrderStatusLiteral | None = Field(
        default=None,
        description=(
            "New status — NOT_STARTED / IN_PROGRESS / DONE / BLOCKED / "
            "PARTIALLY_COMPLETED. Katana validates transitions server-side."
        ),
    )
    planned_quantity: float | None = Field(default=None, gt=0)
    actual_quantity: float | None = Field(default=None, ge=0)
    order_created_date: datetime | None = Field(default=None)
    production_deadline_date: datetime | None = Field(default=None)
    done_date: datetime | None = Field(default=None)
    additional_info: str | None = Field(default=None)


class MORecipeRowAdd(BaseModel):
    """A new recipe row (ingredient) on the MO."""

    variant_id: int = Field(..., description="Variant ID of the ingredient")
    planned_quantity_per_unit: float = Field(..., description="Quantity per unit", gt=0)
    notes: str | None = Field(default=None)
    total_actual_quantity: float | None = Field(default=None, ge=0)


class MORecipeRowUpdate(BaseModel):
    """Patch to an existing MO recipe row."""

    id: int = Field(..., description="Recipe row ID")
    variant_id: int | None = Field(default=None)
    planned_quantity_per_unit: float | None = Field(default=None, gt=0)
    notes: str | None = Field(default=None)
    total_actual_quantity: float | None = Field(default=None, ge=0)


class MOOperationRowAdd(BaseModel):
    """A new operation row (production step) on the MO."""

    status: ManufacturingOperationStatusLiteral = Field(
        ..., description="Initial operation status"
    )
    operation_id: int | None = Field(default=None)
    type: ManufacturingOperationTypeLiteral | None = Field(
        default=None, description="LINKED (template) or STANDARD"
    )
    operation_name: str | None = Field(default=None)
    resource_id: int | None = Field(default=None)
    resource_name: str | None = Field(default=None)
    planned_time_parameter: float | None = Field(default=None)
    planned_time_per_unit: float | None = Field(default=None)
    cost_parameter: float | None = Field(default=None)
    cost_per_hour: float | None = Field(default=None)


class MOOperationRowUpdate(BaseModel):
    """Patch to an existing MO operation row."""

    id: int = Field(..., description="Operation row ID")
    status: ManufacturingOperationStatusLiteral | None = Field(default=None)
    operation_id: int | None = Field(default=None)
    type: ManufacturingOperationTypeLiteral | None = Field(default=None)
    operation_name: str | None = Field(default=None)
    resource_id: int | None = Field(default=None)
    resource_name: str | None = Field(default=None)
    planned_time_parameter: float | None = Field(default=None)
    planned_time_per_unit: float | None = Field(default=None)
    total_actual_time: float | None = Field(default=None)
    cost_parameter: float | None = Field(default=None)
    cost_per_hour: float | None = Field(default=None)


class MOProductionAdd(BaseModel):
    """A new production record on the MO (output completed quantity)."""

    completed_quantity: float = Field(
        ..., description="Quantity produced in this production record", gt=0
    )
    completed_date: datetime | None = Field(default=None)
    is_final: bool | None = Field(
        default=None,
        description="When true, marks this as the final production record",
    )
    serial_numbers: list[str] | None = Field(
        default=None, description="Serial numbers for serial-tracked variants"
    )


class MOProductionUpdate(BaseModel):
    """Patch to an existing MO production record."""

    id: int = Field(..., description="Production record ID")
    production_date: datetime | None = Field(default=None)


class ModifyManufacturingOrderRequest(ConfirmableRequest):
    """Unified modification request for a manufacturing order.

    Sub-payload slots span header + recipe rows (ingredients) + operation
    rows (production steps) + production records (completion logs).
    Multiple slots can be combined; actions execute in canonical order. To
    remove the MO entirely, use ``delete_manufacturing_order``.
    """

    id: int = Field(..., description="Manufacturing order ID")
    update_header: MOHeaderPatch | None = Field(
        default=None,
        description=(
            "Header-level patch. Fields: order_no, variant_id, location_id, "
            "status (NOT_STARTED/IN_PROGRESS/DONE/BLOCKED/PARTIALLY_COMPLETED "
            "— transitions validated server-side), planned_quantity (>0), "
            "actual_quantity (>=0), order_created_date, "
            "production_deadline_date, done_date, additional_info."
        ),
    )
    add_recipe_rows: list[MORecipeRowAdd] | None = Field(
        default=None,
        description=(
            "New recipe rows (ingredients). Each: variant_id (int, required), "
            "planned_quantity_per_unit (float, required, >0), notes, "
            "total_actual_quantity (>=0)."
        ),
    )
    update_recipe_rows: list[MORecipeRowUpdate] | None = Field(
        default=None,
        description=(
            "Patches to existing recipe rows. Each entry: id (int, required) "
            "+ any subset of variant_id, planned_quantity_per_unit, notes, "
            "total_actual_quantity."
        ),
    )
    delete_recipe_row_ids: list[int] | None = Field(
        default=None,
        description="Recipe row IDs to delete from the MO.",
    )
    add_operation_rows: list[MOOperationRowAdd] | None = Field(
        default=None,
        description=(
            "New operation rows (production steps). Each: status (required), "
            "operation_id, type (LINKED template | STANDARD), operation_name, "
            "resource_id, resource_name, planned_time_parameter, "
            "planned_time_per_unit, cost_parameter, cost_per_hour."
        ),
    )
    update_operation_rows: list[MOOperationRowUpdate] | None = Field(
        default=None,
        description=(
            "Patches to existing operation rows. Each entry: id (int, "
            "required) + any subset of status, operation_id, type, "
            "operation_name, resource_id, resource_name, "
            "planned_time_parameter, planned_time_per_unit, "
            "total_actual_time, cost_parameter, cost_per_hour."
        ),
    )
    delete_operation_row_ids: list[int] | None = Field(
        default=None,
        description="Operation row IDs to delete from the MO.",
    )
    add_productions: list[MOProductionAdd] | None = Field(
        default=None,
        description=(
            "New production records (completion logs). Each: "
            "completed_quantity (float, required, >0), completed_date, "
            "is_final (bool — marks as final production record), "
            "serial_numbers (list[str] — for serial-tracked variants)."
        ),
    )
    update_productions: list[MOProductionUpdate] | None = Field(
        default=None,
        description=(
            "Patches to existing production records. Each entry: id (int, "
            "required), production_date."
        ),
    )
    delete_production_ids: list[int] | None = Field(
        default=None,
        description="Production record IDs to delete from the MO.",
    )


class DeleteManufacturingOrderRequest(ConfirmableRequest):
    """Delete a manufacturing order. Destructive — Katana cascades child
    recipe rows / operation rows / production records server-side.
    """

    id: int = Field(..., description="Manufacturing order ID to delete")


# ----------------------------------------------------------------------------
# API request builders
# ----------------------------------------------------------------------------


def _build_update_header_request(
    patch: MOHeaderPatch,
) -> APIUpdateManufacturingOrderRequest:
    return APIUpdateManufacturingOrderRequest(
        **unset_dict(patch, transforms={"status": ManufacturingOrderStatus})
    )


def _build_create_recipe_row_request(
    mo_id: int, row: MORecipeRowAdd
) -> APICreateMORecipeRowRequest:
    return APICreateMORecipeRowRequest(manufacturing_order_id=mo_id, **unset_dict(row))


def _build_update_recipe_row_request(
    patch: MORecipeRowUpdate,
) -> APIUpdateMORecipeRowRequest:
    return APIUpdateMORecipeRowRequest(**unset_dict(patch, exclude=("id",)))


def _build_create_operation_row_request(
    mo_id: int, row: MOOperationRowAdd
) -> APICreateMOOperationRowRequest:
    return APICreateMOOperationRowRequest(
        manufacturing_order_id=mo_id,
        **unset_dict(
            row,
            field_map={"type": "type_"},
            transforms={
                "status": ManufacturingOperationStatus,
                "type": ManufacturingOperationType,
            },
        ),
    )


def _build_update_operation_row_request(
    patch: MOOperationRowUpdate,
) -> APIUpdateMOOperationRowRequest:
    return APIUpdateMOOperationRowRequest(
        **unset_dict(
            patch,
            exclude=("id",),
            field_map={"type": "type_"},
            transforms={
                "status": ManufacturingOperationStatus,
                "type": ManufacturingOperationType,
            },
        )
    )


def _build_create_production_request(
    mo_id: int, prod: MOProductionAdd
) -> APICreateMOProductionRequest:
    return APICreateMOProductionRequest(
        manufacturing_order_id=mo_id, **unset_dict(prod)
    )


def _build_update_production_request(
    patch: MOProductionUpdate,
) -> APIUpdateMOProductionRequest:
    return APIUpdateMOProductionRequest(**unset_dict(patch, exclude=("id",)))


# ----------------------------------------------------------------------------
# Implementation
# ----------------------------------------------------------------------------


async def _modify_manufacturing_order_impl(
    request: ModifyManufacturingOrderRequest, context: Context
) -> ModificationResponse:
    """Build the action plan from sub-payloads and either preview or execute."""
    services = get_services(context)

    if not has_any_subpayload(request):
        raise ValueError(
            "At least one sub-payload must be set: update_header, "
            "add/update/delete_recipe_rows, "
            "add/update/delete_operation_rows, or "
            "add/update/delete_productions. To remove the MO entirely, use "
            "delete_manufacturing_order."
        )

    existing_mo = await _fetch_manufacturing_order_attrs(services, request.id)

    plan: list[ActionSpec] = []

    if request.update_header is not None:
        diff = compute_field_diff(
            existing_mo, request.update_header, unknown_prior=existing_mo is None
        )
        plan.append(
            ActionSpec(
                operation=MOOperation.UPDATE_HEADER,
                target_id=request.id,
                diff=diff,
                apply=make_patch_apply(
                    api_update_manufacturing_order,
                    services,
                    request.id,
                    _build_update_header_request(request.update_header),
                    return_type=ManufacturingOrder,
                ),
                verify=make_response_verifier(diff),
            )
        )

    # Recipe rows.
    plan.extend(
        plan_creates(
            request.add_recipe_rows,
            MOOperation.ADD_RECIPE_ROW,
            lambda row: _build_create_recipe_row_request(request.id, row),
            lambda body: make_post_apply(
                api_create_mo_recipe_row,
                services,
                body,
                return_type=ManufacturingOrderRecipeRow,
            ),
        )
    )
    plan.extend(
        await plan_updates(
            request.update_recipe_rows,
            MOOperation.UPDATE_RECIPE_ROW,
            lambda rid: _fetch_mo_recipe_row(services, rid),
            _build_update_recipe_row_request,
            lambda rid, body: make_patch_apply(
                api_update_mo_recipe_row,
                services,
                rid,
                body,
                return_type=ManufacturingOrderRecipeRow,
            ),
        )
    )
    plan.extend(
        plan_deletes(
            request.delete_recipe_row_ids,
            MOOperation.DELETE_RECIPE_ROW,
            lambda rid: make_delete_apply(api_delete_mo_recipe_row, services, rid),
        )
    )

    # Operation rows.
    plan.extend(
        plan_creates(
            request.add_operation_rows,
            MOOperation.ADD_OPERATION_ROW,
            lambda row: _build_create_operation_row_request(request.id, row),
            lambda body: make_post_apply(
                api_create_mo_operation_row,
                services,
                body,
                return_type=ManufacturingOrderOperationRow,
            ),
        )
    )
    plan.extend(
        await plan_updates(
            request.update_operation_rows,
            MOOperation.UPDATE_OPERATION_ROW,
            lambda rid: _fetch_mo_operation_row(services, rid),
            _build_update_operation_row_request,
            lambda rid, body: make_patch_apply(
                api_update_mo_operation_row,
                services,
                rid,
                body,
                return_type=ManufacturingOrderOperationRow,
            ),
        )
    )
    plan.extend(
        plan_deletes(
            request.delete_operation_row_ids,
            MOOperation.DELETE_OPERATION_ROW,
            lambda rid: make_delete_apply(api_delete_mo_operation_row, services, rid),
        )
    )

    # Production records.
    plan.extend(
        plan_creates(
            request.add_productions,
            MOOperation.ADD_PRODUCTION,
            lambda prod: _build_create_production_request(request.id, prod),
            lambda body: make_post_apply(
                api_create_mo_production,
                services,
                body,
                return_type=ManufacturingOrderProduction,
            ),
        )
    )
    plan.extend(
        await plan_updates(
            request.update_productions,
            MOOperation.UPDATE_PRODUCTION,
            lambda pid: _fetch_mo_production(services, pid),
            _build_update_production_request,
            lambda pid, body: make_patch_apply(
                api_update_mo_production,
                services,
                pid,
                body,
                return_type=ManufacturingOrderProduction,
            ),
        )
    )
    plan.extend(
        plan_deletes(
            request.delete_production_ids,
            MOOperation.DELETE_PRODUCTION,
            lambda pid: make_delete_apply(api_delete_mo_production, services, pid),
        )
    )

    return await run_modify_plan(
        request=request,
        entity_type="manufacturing_order",
        entity_label=f"manufacturing order {request.id}",
        tool_name="modify_manufacturing_order",
        web_url_kind="manufacturing_order",
        existing=existing_mo,
        plan=plan,
    )


@observe_tool
@unpack_pydantic_params
async def modify_manufacturing_order(
    request: Annotated[ModifyManufacturingOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Modify a manufacturing order — unified surface across header, recipe
    rows (ingredients), operation rows (production steps), and production
    records (completion logs).

    Sub-payloads (any subset, all optional):

    - ``update_header`` — patch header fields (incl. status)
    - ``add_recipe_rows`` / ``update_recipe_rows`` /
      ``delete_recipe_row_ids`` — ingredients
    - ``add_operation_rows`` / ``update_operation_rows`` /
      ``delete_operation_row_ids`` — production steps
    - ``add_productions`` / ``update_productions`` /
      ``delete_production_ids`` — completion logs (output records)

    To remove an MO entirely, use the sibling ``delete_manufacturing_order``
    tool.

    Two-step flow: ``confirm=false`` returns a per-action preview;
    ``confirm=true`` executes the plan in canonical order. Fail-fast on
    error; the response carries a ``prior_state`` snapshot for manual
    revert.
    """
    response = await _modify_manufacturing_order_impl(request, context)
    return to_tool_result(response)


# ============================================================================
# Tool: delete_manufacturing_order
# ============================================================================


async def _delete_manufacturing_order_impl(
    request: DeleteManufacturingOrderRequest, context: Context
) -> ModificationResponse:
    """One-action plan that removes the MO. Katana cascades child rows
    server-side."""
    return await run_delete_plan(
        request=request,
        services=get_services(context),
        entity_type="manufacturing_order",
        entity_label=f"manufacturing order {request.id}",
        web_url_kind="manufacturing_order",
        fetcher=_fetch_manufacturing_order_attrs,
        delete_endpoint=api_delete_manufacturing_order,
        operation=MOOperation.DELETE,
    )


@observe_tool
@unpack_pydantic_params
async def delete_manufacturing_order(
    request: Annotated[DeleteManufacturingOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Delete a manufacturing order. Destructive — Katana cascades the
    delete to child recipe rows / operation rows / production records
    server-side.

    The response carries a ``prior_state`` snapshot for manual revert.
    """
    response = await _delete_manufacturing_order_impl(request, context)
    return to_tool_result(response)


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
        tags={"orders", "manufacturing", "read", "procurement"},
        annotations=_read,
    )(list_blocking_ingredients)
    mcp.tool(
        tags={"orders", "manufacturing", "read"},
        annotations=_read,
    )(get_manufacturing_order_recipe)

    _update = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )
    mcp.tool(tags={"orders", "manufacturing", "write"}, annotations=_update)(
        modify_manufacturing_order
    )
    mcp.tool(
        tags={"orders", "manufacturing", "write", "destructive"},
        annotations=_destructive_write,
    )(delete_manufacturing_order)
