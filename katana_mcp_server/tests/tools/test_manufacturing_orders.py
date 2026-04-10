"""Tests for manufacturing order MCP tools."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from katana_mcp.tools.foundation.manufacturing_orders import (
    AddRecipeRowRequest,
    CreateManufacturingOrderRequest,
    DeleteRecipeRowRequest,
    GetManufacturingOrderRecipeRequest,
    _add_recipe_row_impl,
    _create_manufacturing_order_impl,
    _delete_recipe_row_impl,
    _get_manufacturing_order_recipe_impl,
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

    mock_row1 = MagicMock()
    mock_row1.id = 5001
    mock_row1.variant_id = 101
    mock_row1.planned_quantity_per_unit = 1.0
    mock_row1.total_actual_quantity = 0.0
    mock_row1.ingredient_availability = "IN_STOCK"
    mock_row1.notes = None
    mock_row1.cost = 250.0

    mock_row2 = MagicMock()
    mock_row2.id = 5002
    mock_row2.variant_id = 102
    mock_row2.planned_quantity_per_unit = 4.0
    mock_row2.total_actual_quantity = 0.0
    mock_row2.ingredient_availability = "IN_STOCK"
    mock_row2.notes = None
    mock_row2.cost = 2.0

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

from katana_mcp.tools.foundation.manufacturing_orders import (  # noqa: E402
    BatchUpdateRecipesRequest,
    ExplicitChange,
    SubOpStatus,
    VariantReplacement,
    VariantSpec,
    _batch_update_impl,
    _plan_batch_update,
)


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
