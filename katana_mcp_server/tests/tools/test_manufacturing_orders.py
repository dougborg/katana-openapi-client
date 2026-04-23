"""Tests for manufacturing order MCP tools."""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from katana_mcp.tools.foundation.manufacturing_orders import (
    AddRecipeRowRequest,
    BatchUpdateRecipesRequest,
    CreateManufacturingOrderRequest,
    DeleteRecipeRowRequest,
    ExplicitChange,
    GetManufacturingOrderRecipeRequest,
    SubOpStatus,
    VariantReplacement,
    VariantSpec,
    _add_recipe_row_impl,
    _batch_update_impl,
    _create_manufacturing_order_impl,
    _delete_recipe_row_impl,
    _get_manufacturing_order_recipe_impl,
    _plan_batch_update,
    get_manufacturing_order,
    get_manufacturing_order_recipe,
    list_manufacturing_orders,
)

from katana_public_api_client.client_types import UNSET
from katana_public_api_client.models import (
    ManufacturingOrder,
    ManufacturingOrderStatus,
)
from katana_public_api_client.utils import APIError
from tests.conftest import create_mock_context

# ============================================================================
# Unit Tests (with mocks)
# ============================================================================


@pytest.mark.asyncio
async def test_create_manufacturing_order_preview():
    """Test create_manufacturing_order in preview mode."""
    context, _ = create_mock_context()

    request = CreateManufacturingOrderRequest(
        variant_id=2101,
        planned_quantity=50.0,
        location_id=1,
        production_deadline_date=datetime(2024, 1, 25, 17, 0, 0, tzinfo=UTC),
        additional_info="Priority order",
        confirm=False,
    )
    result = await _create_manufacturing_order_impl(request, context)

    assert result.is_preview is True
    assert result.variant_id == 2101
    assert result.planned_quantity == 50.0
    assert result.location_id == 1
    assert result.production_deadline_date == datetime(
        2024, 1, 25, 17, 0, 0, tzinfo=UTC
    )
    assert result.additional_info == "Priority order"
    assert result.id is None
    assert "preview" in result.message.lower()
    assert len(result.next_actions) > 0
    assert len(result.warnings) == 0  # All optional fields provided


@pytest.mark.asyncio
async def test_create_manufacturing_order_confirm_success():
    """Test create_manufacturing_order with confirm=True succeeds."""
    context, _lifespan_ctx = create_mock_context()

    # Mock successful API response
    mock_mo = ManufacturingOrder(
        id=3001,
        status=ManufacturingOrderStatus.NOT_STARTED,
        order_no="MO-2024-001",
        variant_id=2101,
        planned_quantity=50.0,
        location_id=1,
        order_created_date=datetime(2024, 1, 15, 8, 0, 0, tzinfo=UTC),
        production_deadline_date=datetime(2024, 1, 25, 17, 0, 0, tzinfo=UTC),
        additional_info="Priority order",
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = mock_mo

    # Mock the API call
    mock_api_call = AsyncMock(return_value=mock_response)

    # Patch the API call
    import katana_public_api_client.api.manufacturing_order.create_manufacturing_order as create_mo_module

    original_asyncio_detailed = create_mo_module.asyncio_detailed
    create_mo_module.asyncio_detailed = mock_api_call

    try:
        request = CreateManufacturingOrderRequest(
            variant_id=2101,
            planned_quantity=50.0,
            location_id=1,
            production_deadline_date=datetime(2024, 1, 25, 17, 0, 0, tzinfo=UTC),
            additional_info="Priority order",
            confirm=True,
        )
        result = await _create_manufacturing_order_impl(request, context)

        assert result.is_preview is False
        assert result.id == 3001
        assert result.order_no == "MO-2024-001"
        assert result.variant_id == 2101
        assert result.planned_quantity == 50.0
        assert result.location_id == 1
        assert result.status == "NOT_STARTED"
        assert result.additional_info == "Priority order"
        assert "3001" in result.message
        assert len(result.next_actions) > 0

        # Verify API was called
        mock_api_call.assert_called_once()
    finally:
        # Restore original function
        create_mo_module.asyncio_detailed = original_asyncio_detailed


@pytest.mark.asyncio
async def test_create_manufacturing_order_missing_optional_fields():
    """Test create_manufacturing_order handles missing optional fields."""
    context, _ = create_mock_context()

    request = CreateManufacturingOrderRequest(
        variant_id=2101,
        planned_quantity=50.0,
        location_id=1,
        confirm=False,
    )
    result = await _create_manufacturing_order_impl(request, context)

    assert result.is_preview is True
    assert result.variant_id == 2101
    assert result.planned_quantity == 50.0
    assert result.location_id == 1
    assert result.order_created_date is None
    assert result.production_deadline_date is None
    assert result.additional_info is None
    # Verify warnings for missing optional fields
    assert len(result.warnings) == 2
    assert any("production_deadline_date" in w for w in result.warnings)
    assert any("additional_info" in w for w in result.warnings)


@pytest.mark.asyncio
async def test_create_manufacturing_order_confirm_with_minimal_fields():
    """Test create_manufacturing_order with only required fields."""
    context, _lifespan_ctx = create_mock_context()

    # Mock successful API response with minimal fields
    mock_mo = ManufacturingOrder(
        id=3002,
        status=ManufacturingOrderStatus.NOT_STARTED,
        order_no="MO-2024-002",
        variant_id=2102,
        planned_quantity=25.0,
        location_id=2,
        order_created_date=UNSET,
        production_deadline_date=UNSET,
        additional_info=UNSET,
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = mock_mo

    # Mock the API call
    mock_api_call = AsyncMock(return_value=mock_response)

    # Patch the API call
    import katana_public_api_client.api.manufacturing_order.create_manufacturing_order as create_mo_module

    original_asyncio_detailed = create_mo_module.asyncio_detailed
    create_mo_module.asyncio_detailed = mock_api_call

    try:
        request = CreateManufacturingOrderRequest(
            variant_id=2102,
            planned_quantity=25.0,
            location_id=2,
            confirm=True,
        )
        result = await _create_manufacturing_order_impl(request, context)

        assert result.is_preview is False
        assert result.id == 3002
        assert result.order_no == "MO-2024-002"
        assert result.variant_id == 2102
        assert result.planned_quantity == 25.0
        assert result.location_id == 2
        assert result.order_created_date is None
        assert result.production_deadline_date is None
        assert result.additional_info is None
    finally:
        # Restore original function
        create_mo_module.asyncio_detailed = original_asyncio_detailed


@pytest.mark.asyncio
async def test_create_manufacturing_order_api_error():
    """Test create_manufacturing_order handles API errors."""
    context, _lifespan_ctx = create_mock_context()

    # Mock error response
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.parsed = None

    mock_api_call = AsyncMock(return_value=mock_response)

    # Patch the API call
    import katana_public_api_client.api.manufacturing_order.create_manufacturing_order as create_mo_module

    original_asyncio_detailed = create_mo_module.asyncio_detailed
    create_mo_module.asyncio_detailed = mock_api_call

    try:
        request = CreateManufacturingOrderRequest(
            variant_id=2101,
            planned_quantity=50.0,
            location_id=1,
            confirm=True,
        )

        with pytest.raises(APIError):
            await _create_manufacturing_order_impl(request, context)
    finally:
        # Restore original function
        create_mo_module.asyncio_detailed = original_asyncio_detailed


@pytest.mark.asyncio
async def test_create_manufacturing_order_api_exception():
    """Test create_manufacturing_order handles API exceptions."""
    context, _lifespan_ctx = create_mock_context()

    # Mock API call that raises exception
    mock_api_call = AsyncMock(side_effect=Exception("Network error"))

    # Patch the API call
    import katana_public_api_client.api.manufacturing_order.create_manufacturing_order as create_mo_module

    original_asyncio_detailed = create_mo_module.asyncio_detailed
    create_mo_module.asyncio_detailed = mock_api_call

    try:
        request = CreateManufacturingOrderRequest(
            variant_id=2101,
            planned_quantity=50.0,
            location_id=1,
            confirm=True,
        )

        with pytest.raises(Exception, match="Network error"):
            await _create_manufacturing_order_impl(request, context)
    finally:
        # Restore original function
        create_mo_module.asyncio_detailed = original_asyncio_detailed


@pytest.mark.asyncio
async def test_create_manufacturing_order_with_order_created_date():
    """Test create_manufacturing_order with explicit order_created_date."""
    context, _ = create_mock_context()

    order_date = datetime(2024, 1, 15, 8, 0, 0, tzinfo=UTC)
    request = CreateManufacturingOrderRequest(
        variant_id=2101,
        planned_quantity=50.0,
        location_id=1,
        order_created_date=order_date,
        confirm=False,
    )
    result = await _create_manufacturing_order_impl(request, context)

    assert result.is_preview is True
    assert result.order_created_date == order_date


# ============================================================================
# Validation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_manufacturing_order_invalid_quantity():
    """Test create_manufacturing_order rejects invalid quantity."""
    # Pydantic will raise validation error for quantity <= 0
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CreateManufacturingOrderRequest(
            variant_id=2101,
            planned_quantity=0.0,  # Invalid: must be > 0
            location_id=1,
            confirm=False,
        )


@pytest.mark.asyncio
async def test_create_manufacturing_order_negative_quantity():
    """Test create_manufacturing_order rejects negative quantity."""
    # Pydantic will raise validation error for negative quantity
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CreateManufacturingOrderRequest(
            variant_id=2101,
            planned_quantity=-10.0,  # Invalid: must be > 0
            location_id=1,
            confirm=False,
        )


# ============================================================================
# Integration Tests (with real API)
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_manufacturing_order_preview_integration(katana_context):
    """Integration test: create_manufacturing_order preview with real Katana API.

    This test requires a valid KATANA_API_KEY in the environment.
    Tests preview mode which doesn't make API calls.
    """
    request = CreateManufacturingOrderRequest(
        variant_id=2101,
        planned_quantity=50.0,
        location_id=1,
        production_deadline_date=datetime(2024, 12, 31, 17, 0, 0, tzinfo=UTC),
        additional_info="Integration test preview",
        confirm=False,
    )

    try:
        result = await _create_manufacturing_order_impl(request, katana_context)

        # Verify response structure
        assert result.is_preview is True
        assert result.variant_id == 2101
        assert result.planned_quantity == 50.0
        assert result.location_id == 1
        assert isinstance(result.message, str)
        assert isinstance(result.next_actions, list)
        assert result.id is None  # Preview mode doesn't create
    except Exception as e:
        # Should not fail in preview mode
        pytest.fail(f"Preview mode should not fail: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_manufacturing_order_confirm_integration(katana_context):
    """Integration test: create_manufacturing_order confirm with real Katana API.

    This test requires a valid KATANA_API_KEY in the environment.
    Tests actual creation of manufacturing order.

    Note: This test may fail if:
    - API key is invalid
    - Network is unavailable
    - Variant doesn't exist
    - Location doesn't exist
    """
    request = CreateManufacturingOrderRequest(
        variant_id=2101,
        planned_quantity=1.0,  # Small quantity for test
        location_id=1,
        production_deadline_date=datetime(2024, 12, 31, 17, 0, 0, tzinfo=UTC),
        additional_info="Integration test - can be deleted",
        confirm=True,
    )

    try:
        result = await _create_manufacturing_order_impl(request, katana_context)

        # Verify response structure
        assert result.is_preview is False
        assert isinstance(result.id, int)
        assert result.id > 0
        assert isinstance(result.order_no, str) or result.order_no is None
        assert result.variant_id == 2101
        assert result.planned_quantity == 1.0
        assert result.location_id == 1
        assert isinstance(result.status, str) or result.status is None
        assert isinstance(result.message, str)
        assert len(result.next_actions) > 0

    except Exception as e:
        # Network/auth/validation errors are acceptable in integration tests
        error_msg = str(e).lower()
        assert any(
            word in error_msg
            for word in [
                "connection",
                "network",
                "auth",
                "timeout",
                "not found",
                "variant",
                "location",
                "invalid",
            ]
        ), f"Unexpected error: {e}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_manufacturing_order_minimal_fields_integration(katana_context):
    """Integration test: create_manufacturing_order with minimal fields.

    Tests creation with only required fields.
    """
    request = CreateManufacturingOrderRequest(
        variant_id=2101,
        planned_quantity=1.0,
        location_id=1,
        confirm=True,
    )

    try:
        result = await _create_manufacturing_order_impl(request, katana_context)

        # Verify response structure
        assert result.is_preview is False
        assert isinstance(result.id, int)
        assert result.variant_id == 2101
        assert result.planned_quantity == 1.0
        assert result.location_id == 1

    except Exception as e:
        # Network/auth/validation errors are acceptable in integration tests
        error_msg = str(e).lower()
        assert any(
            word in error_msg
            for word in [
                "connection",
                "network",
                "auth",
                "timeout",
                "not found",
                "variant",
                "location",
            ]
        ), f"Unexpected error: {e}"


# ============================================================================
# Recipe row tools — get, add, delete
# ============================================================================

_RECIPE_API = "katana_public_api_client.api.manufacturing_order_recipe"
_UNWRAP_DATA = "katana_public_api_client.utils.unwrap_data"


@pytest.mark.asyncio
async def test_get_manufacturing_order_recipe():
    """Test listing recipe rows for an MO."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.get_by_id = AsyncMock(
        side_effect=[
            {"id": 101, "sku": "FORK-001"},
            {"id": 102, "sku": "BOLT-004"},
        ]
    )

    def _mk_row(row_id: int, variant_id: int, qpu: float, cost: float) -> MagicMock:
        # _recipe_row_info_from_attrs now reads every ManufacturingOrderRecipeRow
        # field — explicitly set the ones it touches to UNSET or safe values so
        # MagicMock's auto-attributes don't leak into Pydantic validation.
        m = MagicMock()
        m.id = row_id
        m.variant_id = variant_id
        m.planned_quantity_per_unit = qpu
        m.total_actual_quantity = 0.0
        m.ingredient_availability = "IN_STOCK"
        m.notes = None
        m.cost = cost
        m.manufacturing_order_id = UNSET
        m.total_consumed_quantity = UNSET
        m.total_remaining_quantity = UNSET
        m.ingredient_expected_date = UNSET
        m.batch_transactions = UNSET
        m.created_at = UNSET
        m.updated_at = UNSET
        m.deleted_at = UNSET
        return m

    mock_row1 = _mk_row(5001, 101, 1.0, 250.0)
    mock_row2 = _mk_row(5002, 102, 4.0, 2.0)

    with (
        patch(
            f"{_RECIPE_API}.get_all_manufacturing_order_recipe_rows.asyncio_detailed",
            new_callable=AsyncMock,
        ),
        patch(_UNWRAP_DATA, return_value=[mock_row1, mock_row2]),
    ):
        request = GetManufacturingOrderRecipeRequest(manufacturing_order_id=9999)
        result = await _get_manufacturing_order_recipe_impl(request, context)

    assert result.total_count == 2
    assert result.rows[0].id == 5001
    assert result.rows[0].sku == "FORK-001"
    assert result.rows[1].sku == "BOLT-004"


@pytest.mark.asyncio
async def test_get_manufacturing_order_recipe_empty():
    """Test listing recipe rows when MO has no ingredients."""
    context, _ = create_mock_context()

    with (
        patch(
            f"{_RECIPE_API}.get_all_manufacturing_order_recipe_rows.asyncio_detailed",
            new_callable=AsyncMock,
        ),
        patch(_UNWRAP_DATA, return_value=[]),
    ):
        request = GetManufacturingOrderRecipeRequest(manufacturing_order_id=9999)
        result = await _get_manufacturing_order_recipe_impl(request, context)

    assert result.total_count == 0
    assert result.rows == []


@pytest.mark.asyncio
async def test_add_recipe_row_preview():
    """Preview adding a recipe row returns without calling the API."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.get_by_sku = AsyncMock(
        return_value={"id": 555, "sku": "FORK-NEW", "display_name": "New Fork"}
    )

    request = AddRecipeRowRequest(
        manufacturing_order_id=9999,
        sku="FORK-NEW",
        planned_quantity_per_unit=1.0,
        confirm=False,
    )
    result = await _add_recipe_row_impl(request, context)

    assert result.is_preview is True
    assert result.variant_id == 555
    assert result.sku == "FORK-NEW"
    assert "Preview" in result.message


@pytest.mark.asyncio
async def test_add_recipe_row_sku_not_found():
    """Adding a recipe row with an unknown SKU raises."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.get_by_sku = AsyncMock(return_value=None)

    request = AddRecipeRowRequest(
        manufacturing_order_id=9999,
        sku="UNKNOWN",
        planned_quantity_per_unit=1.0,
        confirm=False,
    )
    with pytest.raises(ValueError, match="SKU 'UNKNOWN' not found"):
        await _add_recipe_row_impl(request, context)


@pytest.mark.asyncio
async def test_add_recipe_row_by_variant_id():
    """Adding a recipe row by variant_id skips the cache lookup."""
    context, lifespan_ctx = create_mock_context()
    # Cache.get_by_sku should NOT be called
    lifespan_ctx.cache.get_by_sku = AsyncMock(
        side_effect=AssertionError("should not be called")
    )

    request = AddRecipeRowRequest(
        manufacturing_order_id=9999,
        variant_id=40010545,
        planned_quantity_per_unit=1.0,
        confirm=False,
    )
    result = await _add_recipe_row_impl(request, context)

    assert result.is_preview is True
    assert result.variant_id == 40010545
    assert result.sku is None


@pytest.mark.asyncio
async def test_add_recipe_row_requires_identifier():
    """Must provide sku or variant_id."""
    context, _ = create_mock_context()

    request = AddRecipeRowRequest(
        manufacturing_order_id=9999,
        planned_quantity_per_unit=1.0,
        confirm=False,
    )
    with pytest.raises(ValueError, match="sku or variant_id"):
        await _add_recipe_row_impl(request, context)


@pytest.mark.asyncio
async def test_delete_recipe_row_preview():
    """Preview deleting a recipe row returns without calling the API."""
    context, _ = create_mock_context()

    request = DeleteRecipeRowRequest(recipe_row_id=5001, confirm=False)
    result = await _delete_recipe_row_impl(request, context)

    assert result.is_preview is True
    assert result.recipe_row_id == 5001
    assert "Preview" in result.message


# ============================================================================
# batch_update_manufacturing_order_recipes
# ============================================================================


def _mock_recipe_rows(rows_data: list[dict]) -> list:
    """Helper to build a list of mock RecipeRowInfo-like objects."""
    mocks = []
    for r in rows_data:
        m = MagicMock()
        for k, v in r.items():
            setattr(m, k, v)
        mocks.append(m)
    return mocks


@pytest.mark.asyncio
async def test_batch_plan_replacement_basic():
    """Plan a simple replacement across one MO."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.get_by_sku = AsyncMock(
        side_effect=[
            {"id": 100, "sku": "OLD-FORK", "display_name": "Old Fork"},
            {"id": 200, "sku": "NEW-FORK", "display_name": "New Fork"},
            {"id": 201, "sku": "AIR-SHAFT", "display_name": "Air Shaft"},
        ]
    )

    # Mock the recipe fetch
    from katana_mcp.tools.foundation.manufacturing_orders import RecipeRowInfo

    async def fake_get_recipe(req, ctx):
        from katana_mcp.tools.foundation.manufacturing_orders import (
            GetManufacturingOrderRecipeResponse,
        )

        return GetManufacturingOrderRecipeResponse(
            manufacturing_order_id=req.manufacturing_order_id,
            rows=[
                RecipeRowInfo(
                    id=5001,
                    variant_id=100,
                    sku="OLD-FORK",
                    planned_quantity_per_unit=1.0,
                    total_actual_quantity=None,
                    ingredient_availability="IN_STOCK",
                    notes=None,
                    cost=None,
                ),
            ],
            total_count=1,
        )

    with patch(
        "katana_mcp.tools.foundation.manufacturing_orders._get_manufacturing_order_recipe_impl",
        side_effect=fake_get_recipe,
    ):
        request = BatchUpdateRecipesRequest(
            replacements=[
                VariantReplacement(
                    manufacturing_order_ids=[9999],
                    old_sku="OLD-FORK",
                    new_components=[
                        VariantSpec(sku="NEW-FORK", planned_quantity_per_unit=1.0),
                        VariantSpec(sku="AIR-SHAFT", planned_quantity_per_unit=1.0),
                    ],
                )
            ],
        )
        planned, warnings = await _plan_batch_update(request, context)

    # Expect: 1 delete + 2 adds
    assert len(planned) == 3
    deletes = [p for p in planned if p.op_type == "delete"]
    adds = [p for p in planned if p.op_type == "add"]
    assert len(deletes) == 1
    assert len(adds) == 2
    assert deletes[0].recipe_row_id == 5001
    assert adds[0].sku == "NEW-FORK"
    assert adds[1].sku == "AIR-SHAFT"
    # All grouped under the same label
    assert all(p.group_label == "OLD-FORK → [NEW-FORK, AIR-SHAFT]" for p in planned)
    assert warnings == []


@pytest.mark.asyncio
async def test_batch_plan_skips_mo_missing_old_variant():
    """Non-strict mode: MOs without the old variant are skipped with a warning."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.get_by_sku = AsyncMock(
        side_effect=[
            {"id": 100, "sku": "OLD-FORK"},
            {"id": 200, "sku": "NEW-FORK"},
        ]
    )

    from katana_mcp.tools.foundation.manufacturing_orders import (
        GetManufacturingOrderRecipeResponse,
    )

    async def fake_get_recipe(req, ctx):
        return GetManufacturingOrderRecipeResponse(
            manufacturing_order_id=req.manufacturing_order_id,
            rows=[],  # empty — old variant not present
            total_count=0,
        )

    with patch(
        "katana_mcp.tools.foundation.manufacturing_orders._get_manufacturing_order_recipe_impl",
        side_effect=fake_get_recipe,
    ):
        request = BatchUpdateRecipesRequest(
            replacements=[
                VariantReplacement(
                    manufacturing_order_ids=[9999],
                    old_sku="OLD-FORK",
                    new_components=[
                        VariantSpec(sku="NEW-FORK", planned_quantity_per_unit=1.0),
                    ],
                    strict=False,
                )
            ],
        )
        planned, warnings = await _plan_batch_update(request, context)

    assert len(warnings) == 1
    assert "not in recipe" in warnings[0]
    # Skipped add placeholder emitted for visibility
    assert len(planned) == 1
    assert planned[0].status == SubOpStatus.SKIPPED


@pytest.mark.asyncio
async def test_batch_plan_strict_raises_on_missing():
    """Strict mode: MOs without the old variant raise an error."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.get_by_sku = AsyncMock(
        side_effect=[
            {"id": 100, "sku": "OLD-FORK"},
            {"id": 200, "sku": "NEW-FORK"},
        ]
    )

    from katana_mcp.tools.foundation.manufacturing_orders import (
        GetManufacturingOrderRecipeResponse,
    )

    async def fake_get_recipe(req, ctx):
        return GetManufacturingOrderRecipeResponse(
            manufacturing_order_id=req.manufacturing_order_id,
            rows=[],
            total_count=0,
        )

    with patch(
        "katana_mcp.tools.foundation.manufacturing_orders._get_manufacturing_order_recipe_impl",
        side_effect=fake_get_recipe,
    ):
        request = BatchUpdateRecipesRequest(
            replacements=[
                VariantReplacement(
                    manufacturing_order_ids=[9999],
                    old_sku="OLD-FORK",
                    new_components=[
                        VariantSpec(sku="NEW-FORK", planned_quantity_per_unit=1.0),
                    ],
                    strict=True,
                )
            ],
        )
        with pytest.raises(ValueError, match="not in recipe"):
            await _plan_batch_update(request, context)


@pytest.mark.asyncio
async def test_batch_plan_empty_request_raises():
    """Empty request should raise."""
    context, _ = create_mock_context()
    request = BatchUpdateRecipesRequest()
    with pytest.raises(ValueError, match="at least one replacement or change"):
        await _batch_update_impl(request, context)


@pytest.mark.asyncio
async def test_batch_impl_preview_mode():
    """Preview mode returns the plan without calling the API."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.get_by_sku = AsyncMock(
        return_value={"id": 200, "sku": "NEW-FORK"}
    )

    request = BatchUpdateRecipesRequest(
        changes=[
            ExplicitChange(
                manufacturing_order_id=9999,
                remove_row_ids=[5001],
                add_variants=[
                    VariantSpec(sku="NEW-FORK", planned_quantity_per_unit=1.0)
                ],
            )
        ],
        confirm=False,
    )
    response = await _batch_update_impl(request, context)

    assert response.is_preview is True
    assert response.total_ops == 2
    assert response.success_count == 0
    assert "Preview" in response.message


@pytest.mark.asyncio
async def test_batch_plan_explicit_change_with_variant_id():
    """Explicit changes accept variant_id directly without SKU lookup."""
    context, lifespan_ctx = create_mock_context()
    # Should not be called — variant_id is direct
    lifespan_ctx.cache.get_by_sku = AsyncMock(
        side_effect=AssertionError("should not be called")
    )

    request = BatchUpdateRecipesRequest(
        changes=[
            ExplicitChange(
                manufacturing_order_id=9999,
                remove_row_ids=[5001, 5002],
                add_variants=[
                    VariantSpec(variant_id=40010545, planned_quantity_per_unit=1.0),
                ],
            )
        ],
    )
    planned, warnings = await _plan_batch_update(request, context)

    assert len(planned) == 3  # 2 deletes + 1 add
    assert warnings == []


@pytest.mark.asyncio
async def test_create_manufacturing_order_make_to_order_preview():
    """Make-to-order preview mode: sales_order_row_id only, no other fields required."""
    context, _ = create_mock_context()

    request = CreateManufacturingOrderRequest(
        sales_order_row_id=105664660,
        confirm=False,
    )
    result = await _create_manufacturing_order_impl(request, context)

    assert result.is_preview is True
    assert "Make-to-order" in result.message or "make-to-order" in result.message
    assert "105664660" in result.message


@pytest.mark.asyncio
async def test_create_manufacturing_order_standalone_requires_fields():
    """Standalone mode without required fields raises ValueError."""
    context, _ = create_mock_context()

    request = CreateManufacturingOrderRequest(confirm=False)
    with pytest.raises(ValueError, match="variant_id"):
        await _create_manufacturing_order_impl(request, context)


@pytest.mark.asyncio
async def test_create_manufacturing_order_make_to_order_with_subassemblies():
    """Make-to-order with create_subassemblies=true."""
    context, _ = create_mock_context()

    request = CreateManufacturingOrderRequest(
        sales_order_row_id=105664660,
        create_subassemblies=True,
        confirm=False,
    )
    result = await _create_manufacturing_order_impl(request, context)

    assert result.is_preview is True
    assert "subassemblies" in result.message


# ============================================================================
# list_manufacturing_orders — pattern v2
# ============================================================================

_MO_GET_ALL = (
    "katana_public_api_client.api.manufacturing_order.get_all_manufacturing_orders"
)
_MO_UNWRAP_DATA = "katana_public_api_client.utils.unwrap_data"


def _make_mock_mo(
    *,
    id: int = 1,
    order_no: str | None = "MO-1",
    status: str | None = "NOT_STARTED",
    variant_id: int | None = 100,
    planned_quantity: float | None = 5.0,
    actual_quantity: float | None = None,
    location_id: int | None = 1,
    order_created_date: datetime | None = None,
    production_deadline_date: datetime | None = None,
    done_date: datetime | None = None,
    is_linked_to_sales_order: bool | None = False,
    sales_order_id: int | None = None,
    total_cost: float | None = 999.0,
) -> MagicMock:
    """Build a mock ManufacturingOrder attrs object for tests."""
    mo = MagicMock()
    mo.id = id
    mo.order_no = order_no if order_no is not None else UNSET
    mo.status = status if status is not None else UNSET
    mo.variant_id = variant_id if variant_id is not None else UNSET
    mo.planned_quantity = planned_quantity if planned_quantity is not None else UNSET
    mo.actual_quantity = actual_quantity if actual_quantity is not None else UNSET
    mo.location_id = location_id if location_id is not None else UNSET
    mo.order_created_date = (
        order_created_date if order_created_date is not None else UNSET
    )
    mo.production_deadline_date = (
        production_deadline_date if production_deadline_date is not None else UNSET
    )
    mo.done_date = done_date if done_date is not None else UNSET
    mo.is_linked_to_sales_order = (
        is_linked_to_sales_order if is_linked_to_sales_order is not None else UNSET
    )
    mo.sales_order_id = sales_order_id if sales_order_id is not None else UNSET
    mo.total_cost = total_cost if total_cost is not None else UNSET
    return mo


@pytest.mark.asyncio
async def test_list_manufacturing_orders_server_side_filters_pass_through():
    """Server-side filters forward to the API kwargs when set."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListManufacturingOrdersRequest,
        _list_manufacturing_orders_impl,
    )

    from katana_public_api_client.models import GetAllManufacturingOrdersStatus

    context, _ = create_mock_context()
    captured: dict = {}

    async def fake(**kwargs):
        captured.update(kwargs)
        return MagicMock()

    request = ListManufacturingOrdersRequest(
        ids=[1, 2, 3],
        order_no="MO-42",
        status=GetAllManufacturingOrdersStatus.IN_PROGRESS,
        location_id=7,
        is_linked_to_sales_order=True,
        include_deleted=False,
        limit=25,
    )

    with (
        patch(f"{_MO_GET_ALL}.asyncio_detailed", side_effect=fake),
        patch(_MO_UNWRAP_DATA, return_value=[]),
    ):
        await _list_manufacturing_orders_impl(request, context)

    assert captured["ids"] == [1, 2, 3]
    assert captured["order_no"] == "MO-42"
    assert captured["status"] == GetAllManufacturingOrdersStatus.IN_PROGRESS
    assert captured["location_id"] == 7
    assert captured["is_linked_to_sales_order"] is True
    assert captured["include_deleted"] is False
    assert captured["limit"] == 25


@pytest.mark.asyncio
async def test_list_manufacturing_orders_page_short_circuit_single_page():
    """limit <= 250 with no client-side filter adds page=1."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListManufacturingOrdersRequest,
        _list_manufacturing_orders_impl,
    )

    context, _ = create_mock_context()
    captured: dict = {}

    async def fake(**kwargs):
        captured.update(kwargs)
        return MagicMock()

    with (
        patch(f"{_MO_GET_ALL}.asyncio_detailed", side_effect=fake),
        patch(_MO_UNWRAP_DATA, return_value=[]),
    ):
        await _list_manufacturing_orders_impl(
            ListManufacturingOrdersRequest(limit=10), context
        )

    assert captured["page"] == 1
    assert captured["limit"] == 10


@pytest.mark.asyncio
async def test_list_manufacturing_orders_caller_page_preserved():
    """Caller's explicit `page` overrides the short-circuit."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListManufacturingOrdersRequest,
        _list_manufacturing_orders_impl,
    )

    context, _ = create_mock_context()
    captured: dict = {}

    async def fake(**kwargs):
        captured.update(kwargs)
        return MagicMock()

    with (
        patch(f"{_MO_GET_ALL}.asyncio_detailed", side_effect=fake),
        patch(_MO_UNWRAP_DATA, return_value=[]),
    ):
        await _list_manufacturing_orders_impl(
            ListManufacturingOrdersRequest(limit=50, page=3), context
        )

    assert captured["page"] == 3
    assert captured["limit"] == 50


@pytest.mark.asyncio
async def test_list_manufacturing_orders_skips_short_circuit_when_client_filter_set():
    """production_deadline filter (client-side) suppresses the page=1 short-circuit."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListManufacturingOrdersRequest,
        _list_manufacturing_orders_impl,
    )

    context, _ = create_mock_context()
    captured: dict = {}

    async def fake(**kwargs):
        captured.update(kwargs)
        return MagicMock()

    with (
        patch(f"{_MO_GET_ALL}.asyncio_detailed", side_effect=fake),
        patch(_MO_UNWRAP_DATA, return_value=[]),
    ):
        await _list_manufacturing_orders_impl(
            ListManufacturingOrdersRequest(
                limit=10, production_deadline_after="2026-04-01T00:00:00Z"
            ),
            context,
        )

    assert "page" not in captured
    assert captured["limit"] == 10


@pytest.mark.asyncio
async def test_list_manufacturing_orders_pagination_meta_from_header():
    """x-pagination header populates PaginationMeta when page is set."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListManufacturingOrdersRequest,
        _list_manufacturing_orders_impl,
    )

    context, _ = create_mock_context()

    mock_response = MagicMock()
    mock_response.headers = {
        "x-pagination": (
            '{"total_records":"200","total_pages":"4","offset":"0","page":"2",'
            '"first_page":"false","last_page":"false"}'
        )
    }

    async def fake(**kwargs):
        return mock_response

    with (
        patch(f"{_MO_GET_ALL}.asyncio_detailed", side_effect=fake),
        patch(_MO_UNWRAP_DATA, return_value=[]),
    ):
        result = await _list_manufacturing_orders_impl(
            ListManufacturingOrdersRequest(page=2, limit=50), context
        )

    assert result.pagination is not None
    assert result.pagination.total_records == 200
    assert result.pagination.total_pages == 4
    assert result.pagination.page == 2
    assert result.pagination.first_page is False


@pytest.mark.asyncio
async def test_list_manufacturing_orders_caps_to_limit():
    """Safety net: slice results to request.limit regardless of transport."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListManufacturingOrdersRequest,
        _list_manufacturing_orders_impl,
    )

    context, _ = create_mock_context()
    over_fetched = [_make_mock_mo(id=i, order_no=f"MO-{i}") for i in range(100)]

    with (
        patch(f"{_MO_GET_ALL}.asyncio_detailed", new_callable=AsyncMock),
        patch(_MO_UNWRAP_DATA, return_value=over_fetched),
    ):
        result = await _list_manufacturing_orders_impl(
            ListManufacturingOrdersRequest(limit=25), context
        )

    assert len(result.orders) == 25
    assert result.total_count == 25


@pytest.mark.asyncio
async def test_list_manufacturing_orders_limit_le_250_validation():
    """limit > 250 is rejected at the schema boundary."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListManufacturingOrdersRequest,
    )
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ListManufacturingOrdersRequest(limit=500)


@pytest.mark.asyncio
async def test_list_manufacturing_orders_invalid_date_raises():
    """Malformed ISO-8601 for a date filter surfaces as ValueError."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListManufacturingOrdersRequest,
        _list_manufacturing_orders_impl,
    )

    context, _ = create_mock_context()

    with (
        patch(f"{_MO_GET_ALL}.asyncio_detailed", new_callable=AsyncMock),
        patch(_MO_UNWRAP_DATA, return_value=[]),
        pytest.raises(ValueError, match=r"Invalid ISO-8601.*created_after"),
    ):
        await _list_manufacturing_orders_impl(
            ListManufacturingOrdersRequest(created_after="not-a-date"), context
        )


@pytest.mark.asyncio
async def test_list_manufacturing_orders_date_z_normalization():
    """Trailing Z and z both normalize to +00:00 and forward as datetimes."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListManufacturingOrdersRequest,
        _list_manufacturing_orders_impl,
    )

    context, _ = create_mock_context()
    captured: dict = {}

    async def fake(**kwargs):
        captured.update(kwargs)
        return MagicMock()

    with (
        patch(f"{_MO_GET_ALL}.asyncio_detailed", side_effect=fake),
        patch(_MO_UNWRAP_DATA, return_value=[]),
    ):
        await _list_manufacturing_orders_impl(
            ListManufacturingOrdersRequest(
                created_after="2026-01-01T00:00:00Z",
                updated_before="2026-04-01T00:00:00z",
            ),
            context,
        )

    assert isinstance(captured["created_at_min"], datetime)
    assert isinstance(captured["updated_at_max"], datetime)
    assert captured["created_at_min"].tzinfo is not None
    assert captured["updated_at_max"].tzinfo is not None


@pytest.mark.asyncio
async def test_list_manufacturing_orders_production_deadline_client_side_filter():
    """production_deadline_after/before filters post-fetch via client code."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListManufacturingOrdersRequest,
        _list_manufacturing_orders_impl,
    )

    context, _ = create_mock_context()
    mos = [
        _make_mock_mo(
            id=1,
            order_no="MO-1",
            production_deadline_date=datetime(2026, 4, 15, tzinfo=UTC),
        ),
        _make_mock_mo(
            id=2,
            order_no="MO-2",
            production_deadline_date=datetime(2027, 1, 1, tzinfo=UTC),
        ),
    ]

    with (
        patch(f"{_MO_GET_ALL}.asyncio_detailed", new_callable=AsyncMock),
        patch(_MO_UNWRAP_DATA, return_value=mos),
    ):
        result = await _list_manufacturing_orders_impl(
            ListManufacturingOrdersRequest(
                production_deadline_after="2026-04-01T00:00:00Z",
                production_deadline_before="2026-04-30T00:00:00Z",
            ),
            context,
        )

    assert result.total_count == 1
    assert result.orders[0].id == 1


# ============================================================================
# format=json (manufacturing_orders tools)
# ============================================================================


def _content_text(result) -> str:
    return result.content[0].text


@pytest.mark.asyncio
async def test_list_manufacturing_orders_format_json_returns_json():
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListManufacturingOrdersResponse,
    )

    context, _ = create_mock_context()

    with patch(
        "katana_mcp.tools.foundation.manufacturing_orders._list_manufacturing_orders_impl",
        new_callable=AsyncMock,
    ) as mock_impl:
        mock_impl.return_value = ListManufacturingOrdersResponse(
            orders=[], total_count=0, pagination=None
        )
        result = await list_manufacturing_orders(format="json", context=context)

    data = json.loads(_content_text(result))
    assert data["total_count"] == 0


@pytest.mark.asyncio
async def test_get_manufacturing_order_format_json_returns_json():
    from katana_mcp.tools.foundation.manufacturing_orders import (
        GetManufacturingOrderResponse,
    )

    context, _ = create_mock_context()

    with patch(
        "katana_mcp.tools.foundation.manufacturing_orders._get_manufacturing_order_impl",
        new_callable=AsyncMock,
    ) as mock_impl:
        mock_impl.return_value = GetManufacturingOrderResponse(
            id=3001,
            order_no="MO-2024-001",
            status="IN_PROGRESS",
        )
        result = await get_manufacturing_order(
            order_id=1, format="json", context=context
        )

    data = json.loads(_content_text(result))
    assert data["id"] == 3001
    assert data["order_no"] == "MO-2024-001"
    assert data["status"] == "IN_PROGRESS"
    # Exhaustive response always has list-shaped fields present (may be empty)
    assert data["recipe_rows"] == []
    assert data["operation_rows"] == []
    assert data["productions"] == []


@pytest.mark.asyncio
async def test_get_manufacturing_order_recipe_format_json_returns_json():
    from katana_mcp.tools.foundation.manufacturing_orders import (
        GetManufacturingOrderRecipeResponse,
    )

    context, _ = create_mock_context()

    with patch(
        "katana_mcp.tools.foundation.manufacturing_orders._get_manufacturing_order_recipe_impl",
        new_callable=AsyncMock,
    ) as mock_impl:
        mock_impl.return_value = GetManufacturingOrderRecipeResponse(
            manufacturing_order_id=7, rows=[], total_count=0
        )
        result = await get_manufacturing_order_recipe(
            manufacturing_order_id=7, format="json", context=context
        )

    data = json.loads(_content_text(result))
    assert data["manufacturing_order_id"] == 7
    assert data["total_count"] == 0


# ============================================================================
# Exhaustive get_manufacturing_order (#346)
# ============================================================================

_FETCH_RECIPE = "katana_mcp.tools.foundation.manufacturing_orders._fetch_mo_recipe_rows"
_FETCH_OPS = "katana_mcp.tools.foundation.manufacturing_orders._fetch_mo_operation_rows"
_FETCH_PRODS = "katana_mcp.tools.foundation.manufacturing_orders._fetch_mo_productions"
_MO_API = "katana_public_api_client.api.manufacturing_order"


def _full_mo_attrs():
    """Build a ManufacturingOrder attrs model with every field populated.

    Used by the exhaustive-coverage tests to prove ``GetManufacturingOrderResponse``
    surfaces every field on the generated attrs model.
    """
    from katana_public_api_client.models import (
        ManufacturingOrder,
        ManufacturingOrderStatus,
    )
    from katana_public_api_client.models.ingredient_availability import (
        IngredientAvailability,
    )

    return ManufacturingOrder(
        id=3001,
        created_at=datetime(2024, 1, 15, 8, 0, 0, tzinfo=UTC),
        updated_at=datetime(2024, 1, 20, 14, 30, 0, tzinfo=UTC),
        deleted_at=None,
        status=ManufacturingOrderStatus.IN_PROGRESS,
        order_no="MO-2024-001",
        variant_id=2101,
        planned_quantity=50.0,
        actual_quantity=35.0,
        completed_quantity=30.0,
        remaining_quantity=20.0,
        includes_partial_completions=True,
        batch_transactions=[],
        location_id=1,
        order_created_date=datetime(2024, 1, 15, 8, 0, 0, tzinfo=UTC),
        production_deadline_date=datetime(2024, 1, 25, 17, 0, 0, tzinfo=UTC),
        done_date=None,
        additional_info="Priority order",
        is_linked_to_sales_order=True,
        ingredient_availability=IngredientAvailability.IN_STOCK,
        total_cost=12500.0,
        total_actual_time=140.5,
        total_planned_time=200.0,
        sales_order_id=2001,
        sales_order_row_id=2501,
        sales_order_delivery_deadline=datetime(2024, 1, 30, 12, 0, 0, tzinfo=UTC),
        material_cost=8750.0,
        subassemblies_cost=2250.0,
        operations_cost=1500.0,
        serial_numbers=[],
    )


@pytest.mark.asyncio
async def test_get_manufacturing_order_full_field_coverage():
    """Every attrs-model field on ManufacturingOrder must flow to the response.

    Pins the #346 exhaustive-coverage contract: previous versions of
    GetManufacturingOrderResponse dropped 13 fields (created_at, updated_at,
    deleted_at, completed_quantity, remaining_quantity, includes_partial_completions,
    batch_transactions, total_actual_time, total_planned_time, sales_order_row_id,
    sales_order_delivery_deadline, subassemblies_cost, serial_numbers). All must
    round-trip through _build_mo_response.
    """
    from katana_mcp.tools.foundation.manufacturing_orders import (
        GetManufacturingOrderRequest,
        _get_manufacturing_order_impl,
    )

    context, _ = create_mock_context()
    mo = _full_mo_attrs()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = mo

    with (
        patch(
            f"{_MO_API}.get_manufacturing_order.asyncio_detailed",
            new_callable=AsyncMock,
            return_value=mock_response,
        ),
        patch(_FETCH_RECIPE, new_callable=AsyncMock, return_value=[]),
        patch(_FETCH_OPS, new_callable=AsyncMock, return_value=[]),
        patch(_FETCH_PRODS, new_callable=AsyncMock, return_value=[]),
    ):
        request = GetManufacturingOrderRequest(order_id=3001)
        result = await _get_manufacturing_order_impl(request, context)

    # Every scalar field on ManufacturingOrder must reach the response:
    assert result.id == 3001
    assert result.order_no == "MO-2024-001"
    assert result.status == "IN_PROGRESS"
    assert result.variant_id == 2101
    assert result.planned_quantity == 50.0
    assert result.actual_quantity == 35.0
    # Previously-dropped fields:
    assert result.completed_quantity == 30.0
    assert result.remaining_quantity == 20.0
    assert result.includes_partial_completions is True
    assert result.total_actual_time == 140.5
    assert result.total_planned_time == 200.0
    assert result.sales_order_row_id == 2501
    assert result.sales_order_delivery_deadline == "2024-01-30T12:00:00+00:00"
    assert result.subassemblies_cost == 2250.0
    assert result.created_at == "2024-01-15T08:00:00+00:00"
    assert result.updated_at == "2024-01-20T14:30:00+00:00"
    assert result.deleted_at is None
    assert result.batch_transactions == []
    assert result.serial_numbers == []
    # Fields that were already there stay correct:
    assert result.location_id == 1
    assert result.additional_info == "Priority order"
    assert result.ingredient_availability == "IN_STOCK"
    assert result.total_cost == 12500.0
    assert result.material_cost == 8750.0
    assert result.operations_cost == 1500.0
    assert result.sales_order_id == 2001
    assert result.is_linked_to_sales_order is True


@pytest.mark.asyncio
async def test_get_manufacturing_order_fetches_related_resources():
    """Recipe rows, operation rows, and productions come from their own endpoints.

    Patches the three _fetch_mo_* helpers to assert that:
      (a) each is invoked exactly once with the MO id, and
      (b) their results flow through to the response's list-shaped fields.
    """
    from katana_mcp.tools.foundation.manufacturing_orders import (
        GetManufacturingOrderRequest,
        OperationRowInfo,
        ProductionInfo,
        RecipeRowInfo,
        _get_manufacturing_order_impl,
    )

    context, _ = create_mock_context()
    mo = _full_mo_attrs()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = mo

    recipe_row = RecipeRowInfo(
        id=4001,
        manufacturing_order_id=3001,
        variant_id=3201,
        sku="STEEL-304",
        planned_quantity_per_unit=2.5,
        total_actual_quantity=125.0,
        ingredient_availability="IN_STOCK",
        notes="Use only grade 304 material",
        cost=437.5,
    )
    operation_row = OperationRowInfo(
        id=3801,
        manufacturing_order_id=3001,
        status="IN_PROGRESS",
        operation_name="Cut Steel Sheets",
        planned_time_per_unit=15.0,
        total_actual_time=12.5,
    )
    production = ProductionInfo(
        id=3501,
        manufacturing_order_id=3001,
        quantity=25.0,
        production_date="2024-01-20T14:30:00+00:00",
    )

    with (
        patch(
            f"{_MO_API}.get_manufacturing_order.asyncio_detailed",
            new_callable=AsyncMock,
            return_value=mock_response,
        ),
        patch(
            _FETCH_RECIPE, new_callable=AsyncMock, return_value=[recipe_row]
        ) as mock_fetch_recipe,
        patch(
            _FETCH_OPS, new_callable=AsyncMock, return_value=[operation_row]
        ) as mock_fetch_ops,
        patch(
            _FETCH_PRODS, new_callable=AsyncMock, return_value=[production]
        ) as mock_fetch_prods,
    ):
        request = GetManufacturingOrderRequest(order_id=3001)
        result = await _get_manufacturing_order_impl(request, context)

    # Each helper called exactly once with the MO id:
    mock_fetch_recipe.assert_awaited_once()
    assert mock_fetch_recipe.await_args.args[1] == 3001
    mock_fetch_ops.assert_awaited_once()
    assert mock_fetch_ops.await_args.args[1] == 3001
    mock_fetch_prods.assert_awaited_once()
    assert mock_fetch_prods.await_args.args[1] == 3001

    # Results flow through to the response:
    assert len(result.recipe_rows) == 1
    assert result.recipe_rows[0].id == 4001
    assert result.recipe_rows[0].sku == "STEEL-304"
    assert len(result.operation_rows) == 1
    assert result.operation_rows[0].operation_name == "Cut Steel Sheets"
    assert len(result.productions) == 1
    assert result.productions[0].quantity == 25.0


@pytest.mark.asyncio
async def test_get_manufacturing_order_markdown_uses_canonical_field_names():
    """Markdown labels use Pydantic field names (not prettified headers) so
    LLM consumers can't misread a section label as a different field
    (motivation: #346 follow-on, supplier_item_codes misread)."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        GetManufacturingOrderResponse,
    )

    context, _ = create_mock_context()

    with patch(
        "katana_mcp.tools.foundation.manufacturing_orders._get_manufacturing_order_impl",
        new_callable=AsyncMock,
    ) as mock_impl:
        mock_impl.return_value = GetManufacturingOrderResponse(
            id=3001,
            order_no="MO-2024-001",
            status="IN_PROGRESS",
            variant_id=2101,
            planned_quantity=50.0,
            production_deadline_date="2024-01-25T17:00:00+00:00",
            total_cost=12500.0,
            subassemblies_cost=2250.0,
            sales_order_row_id=2501,
        )
        result = await get_manufacturing_order(order_id=3001, context=context)

    text = result.content[0].text
    # Canonical scalar labels — the prettified versions the old impl used
    # (e.g. "**Deadline**:", "**Total Cost**:") are gone. These pin the
    # new convention:
    assert "**production_deadline_date**: 2024-01-25T17:00:00+00:00" in text
    assert "**total_cost**: 12500.0" in text
    assert "**subassemblies_cost**: 2250.0" in text
    assert "**sales_order_row_id**: 2501" in text
    # Empty list fields render with explicit [] syntax, not bare headers
    # that a reader might mistake for a section:
    assert "**recipe_rows**: []" in text
    assert "**operation_rows**: []" in text
    assert "**productions**: []" in text
    assert "**batch_transactions**: []" in text
    assert "**serial_numbers**: []" in text


@pytest.mark.asyncio
async def test_get_manufacturing_order_recipe_full_field_coverage():
    """RecipeRowInfo must surface every field on ManufacturingOrderRecipeRow.

    The pre-#346 RecipeRowInfo dropped 8 fields (created_at, updated_at,
    deleted_at, manufacturing_order_id, ingredient_expected_date,
    batch_transactions, total_consumed_quantity, total_remaining_quantity).
    """
    from katana_mcp.tools.foundation.manufacturing_orders import (
        _recipe_row_info_from_attrs,
    )

    from katana_public_api_client.models.manufacturing_order_recipe_row import (
        ManufacturingOrderRecipeRow,
    )
    from katana_public_api_client.models.manufacturing_order_recipe_row_batch_transactions_item import (
        ManufacturingOrderRecipeRowBatchTransactionsItem,
    )

    attrs_row = ManufacturingOrderRecipeRow(
        id=4001,
        created_at=datetime(2024, 1, 15, 8, 0, 0, tzinfo=UTC),
        updated_at=datetime(2024, 1, 20, 14, 30, 0, tzinfo=UTC),
        deleted_at=None,
        manufacturing_order_id=3001,
        variant_id=3201,
        notes="Use only grade 304 material",
        planned_quantity_per_unit=2.5,
        total_actual_quantity=125.0,
        ingredient_availability="IN_STOCK",
        ingredient_expected_date=datetime(2024, 1, 18, 0, 0, 0, tzinfo=UTC),
        batch_transactions=[
            ManufacturingOrderRecipeRowBatchTransactionsItem(
                batch_id=1201, quantity=125.0
            )
        ],
        cost=437.5,
        total_consumed_quantity=100.0,
        total_remaining_quantity=25.0,
    )

    info = _recipe_row_info_from_attrs(attrs_row, sku="STEEL-304")

    # Previously-dropped fields:
    assert info.manufacturing_order_id == 3001
    assert info.total_consumed_quantity == 100.0
    assert info.total_remaining_quantity == 25.0
    assert info.ingredient_expected_date == "2024-01-18T00:00:00+00:00"
    assert info.created_at == "2024-01-15T08:00:00+00:00"
    assert info.updated_at == "2024-01-20T14:30:00+00:00"
    assert info.deleted_at is None
    assert len(info.batch_transactions) == 1
    assert info.batch_transactions[0].batch_id == 1201
    assert info.batch_transactions[0].quantity == 125.0
    # Fields that were already there stay correct:
    assert info.id == 4001
    assert info.variant_id == 3201
    assert info.sku == "STEEL-304"
    assert info.notes == "Use only grade 304 material"
    assert info.planned_quantity_per_unit == 2.5
    assert info.total_actual_quantity == 125.0
    assert info.ingredient_availability == "IN_STOCK"
    assert info.cost == 437.5
