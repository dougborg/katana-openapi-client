"""Tests for catalog management MCP tools."""

import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from katana_mcp.tools.foundation.catalog import (
    CreateMaterialRequest,
    CreateProductRequest,
    _create_material_impl,
    _create_product_impl,
)

# ============================================================================
# Test Helpers
# ============================================================================


def create_mock_context():
    """Create a mock context with proper FastMCP structure.

    Returns context with request_context.lifespan_context.client accessible.
    """
    context = MagicMock()
    mock_request_context = MagicMock()
    mock_lifespan_context = MagicMock()
    context.request_context = mock_request_context
    mock_request_context.lifespan_context = mock_lifespan_context
    return context, mock_lifespan_context


# ============================================================================
# Unit Tests (with mocks) - create_product
# ============================================================================


@pytest.mark.asyncio
async def test_create_product_minimal():
    """Test create_product with minimal required fields."""
    context, lifespan_ctx = create_mock_context()

    # Mock Product response
    mock_product = MagicMock()
    mock_product.id = 123
    mock_product.name = "Test Product"

    lifespan_ctx.client.products.create = AsyncMock(return_value=mock_product)

    request = CreateProductRequest(
        name="Test Product",
        sku="TEST-001",
    )
    result = await _create_product_impl(request, context)

    assert result.id == 123
    assert result.name == "Test Product"
    assert result.sku == "TEST-001"
    assert result.success is True
    assert "Test Product" in result.message
    assert "TEST-001" in result.message

    # Verify create was called
    lifespan_ctx.client.products.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_product_full_fields():
    """Test create_product with all optional fields."""
    context, lifespan_ctx = create_mock_context()

    # Mock Product response
    mock_product = MagicMock()
    mock_product.id = 456
    mock_product.name = "Widget Pro"

    lifespan_ctx.client.products.create = AsyncMock(return_value=mock_product)

    request = CreateProductRequest(
        name="Widget Pro",
        sku="WGT-PRO-001",
        uom="pcs",
        category_name="Widgets",
        is_sellable=True,
        is_producible=True,
        is_purchasable=False,
        sales_price=29.99,
        purchase_price=15.50,
        default_supplier_id=100,
        additional_info="Premium widget for industrial use",
    )
    result = await _create_product_impl(request, context)

    assert result.id == 456
    assert result.name == "Widget Pro"
    assert result.sku == "WGT-PRO-001"
    assert result.success is True
    assert "Widget Pro" in result.message

    # Verify create was called with all fields
    lifespan_ctx.client.products.create.assert_called_once()
    call_args = lifespan_ctx.client.products.create.call_args[0][0]
    assert call_args.name == "Widget Pro"
    assert call_args.uom == "pcs"
    assert call_args.category_name == "Widgets"
    assert call_args.is_sellable is True
    assert call_args.is_producible is True
    assert call_args.is_purchasable is False
    assert call_args.default_supplier_id == 100
    assert call_args.additional_info == "Premium widget for industrial use"


@pytest.mark.asyncio
async def test_create_product_default_values():
    """Test create_product uses correct default values."""
    context, lifespan_ctx = create_mock_context()

    # Mock Product response
    mock_product = MagicMock()
    mock_product.id = 789
    mock_product.name = "Default Product"

    lifespan_ctx.client.products.create = AsyncMock(return_value=mock_product)

    request = CreateProductRequest(
        name="Default Product",
        sku="DEF-001",
    )
    result = await _create_product_impl(request, context)

    assert result.success is True

    # Verify default values
    call_args = lifespan_ctx.client.products.create.call_args[0][0]
    assert call_args.uom == "pcs"  # Default UOM
    assert call_args.is_sellable is True  # Default sellable
    assert call_args.is_producible is False  # Default not producible
    assert call_args.is_purchasable is True  # Default purchasable


@pytest.mark.asyncio
async def test_create_product_handles_none_name():
    """Test create_product handles None product name in response."""
    context, lifespan_ctx = create_mock_context()

    # Mock Product with None name
    mock_product = MagicMock()
    mock_product.id = 999
    mock_product.name = None

    lifespan_ctx.client.products.create = AsyncMock(return_value=mock_product)

    request = CreateProductRequest(
        name="Test",
        sku="TEST-999",
    )
    result = await _create_product_impl(request, context)

    assert result.name == ""  # Converts None to empty string
    assert result.id == 999


@pytest.mark.asyncio
async def test_create_product_error_handling():
    """Test create_product error handling."""
    context, lifespan_ctx = create_mock_context()

    # Mock exception
    lifespan_ctx.client.products.create = AsyncMock(
        side_effect=Exception("API Error: Invalid product data")
    )

    request = CreateProductRequest(
        name="Bad Product",
        sku="BAD-001",
    )

    with pytest.raises(Exception, match="API Error: Invalid product data"):
        await _create_product_impl(request, context)


# ============================================================================
# Unit Tests (with mocks) - create_material
# ============================================================================


@pytest.mark.asyncio
async def test_create_material_minimal():
    """Test create_material with minimal required fields."""
    context, lifespan_ctx = create_mock_context()

    # Mock Material response
    mock_material = MagicMock()
    mock_material.id = 200
    mock_material.name = "Steel Rod"

    lifespan_ctx.client.materials.create = AsyncMock(return_value=mock_material)

    request = CreateMaterialRequest(
        name="Steel Rod",
        sku="MAT-STEEL-001",
    )
    result = await _create_material_impl(request, context)

    assert result.id == 200
    assert result.name == "Steel Rod"
    assert result.sku == "MAT-STEEL-001"
    assert result.success is True
    assert "Steel Rod" in result.message
    assert "MAT-STEEL-001" in result.message

    # Verify create was called
    lifespan_ctx.client.materials.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_material_full_fields():
    """Test create_material with all optional fields."""
    context, lifespan_ctx = create_mock_context()

    # Mock Material response
    mock_material = MagicMock()
    mock_material.id = 201
    mock_material.name = "Aluminum Sheet"

    lifespan_ctx.client.materials.create = AsyncMock(return_value=mock_material)

    request = CreateMaterialRequest(
        name="Aluminum Sheet",
        sku="MAT-AL-001",
        uom="kg",
        category_name="Metals",
        is_sellable=True,
        sales_price=8.50,
        purchase_price=5.25,
        default_supplier_id=50,
        additional_info="High-grade aluminum for aerospace",
    )
    result = await _create_material_impl(request, context)

    assert result.id == 201
    assert result.name == "Aluminum Sheet"
    assert result.sku == "MAT-AL-001"
    assert result.success is True

    # Verify create was called with all fields
    lifespan_ctx.client.materials.create.assert_called_once()
    call_args = lifespan_ctx.client.materials.create.call_args[0][0]
    assert call_args.name == "Aluminum Sheet"
    assert call_args.uom == "kg"
    assert call_args.category_name == "Metals"
    assert call_args.is_sellable is True
    assert call_args.default_supplier_id == 50
    assert call_args.additional_info == "High-grade aluminum for aerospace"


@pytest.mark.asyncio
async def test_create_material_default_values():
    """Test create_material uses correct default values."""
    context, lifespan_ctx = create_mock_context()

    # Mock Material response
    mock_material = MagicMock()
    mock_material.id = 202
    mock_material.name = "Basic Material"

    lifespan_ctx.client.materials.create = AsyncMock(return_value=mock_material)

    request = CreateMaterialRequest(
        name="Basic Material",
        sku="MAT-BASIC-001",
    )
    result = await _create_material_impl(request, context)

    assert result.success is True

    # Verify default values
    call_args = lifespan_ctx.client.materials.create.call_args[0][0]
    assert call_args.uom == "pcs"  # Default UOM
    assert call_args.is_sellable is False  # Default not sellable for materials


@pytest.mark.asyncio
async def test_create_material_handles_none_name():
    """Test create_material handles None material name in response."""
    context, lifespan_ctx = create_mock_context()

    # Mock Material with None name
    mock_material = MagicMock()
    mock_material.id = 203
    mock_material.name = None

    lifespan_ctx.client.materials.create = AsyncMock(return_value=mock_material)

    request = CreateMaterialRequest(
        name="Test Material",
        sku="MAT-TEST-001",
    )
    result = await _create_material_impl(request, context)

    assert result.name == ""  # Converts None to empty string
    assert result.id == 203


@pytest.mark.asyncio
async def test_create_material_error_handling():
    """Test create_material error handling."""
    context, lifespan_ctx = create_mock_context()

    # Mock exception
    lifespan_ctx.client.materials.create = AsyncMock(
        side_effect=Exception("API Error: Duplicate SKU")
    )

    request = CreateMaterialRequest(
        name="Duplicate Material",
        sku="MAT-DUP-001",
    )

    with pytest.raises(Exception, match="API Error: Duplicate SKU"):
        await _create_material_impl(request, context)


# ============================================================================
# Validation Tests
# ============================================================================


def test_create_product_requires_name():
    """Test create_product requires name field."""
    with pytest.raises(ValueError):
        CreateProductRequest(sku="TEST-001")


def test_create_product_requires_sku():
    """Test create_product requires sku field."""
    with pytest.raises(ValueError):
        CreateProductRequest(name="Test Product")


def test_create_material_requires_name():
    """Test create_material requires name field."""
    with pytest.raises(ValueError):
        CreateMaterialRequest(sku="MAT-001")


def test_create_material_requires_sku():
    """Test create_material requires sku field."""
    with pytest.raises(ValueError):
        CreateMaterialRequest(name="Test Material")


# ============================================================================
# Integration Tests (with real API)
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_product_integration(katana_context):
    """Integration test: create_product with real Katana API.

    This test requires a valid KATANA_API_KEY in the environment.
    It attempts to create a test product.

    Note: This test may fail if:
    - API key is invalid
    - Network is unavailable
    - SKU already exists
    """
    request = CreateProductRequest(
        name="Integration Test Product",
        sku=f"TEST-PROD-INT-{int(time.time())}",
        uom="pcs",
        is_sellable=True,
        is_producible=False,
        is_purchasable=True,
        sales_price=9.99,
    )

    try:
        result = await _create_product_impl(request, katana_context)

        # Verify response structure
        assert isinstance(result.id, int)
        assert result.id > 0
        assert isinstance(result.name, str)
        assert result.name == "Integration Test Product"
        assert isinstance(result.sku, str)
        assert result.sku == request.sku
        assert result.success is True
        assert "created successfully" in result.message.lower()

    except Exception as e:
        # Network/auth errors are acceptable in integration tests
        error_msg = str(e).lower()
        assert any(
            word in error_msg
            for word in [
                "connection",
                "network",
                "auth",
                "timeout",
                "duplicate",
                "already exists",
            ]
        ), f"Unexpected error: {e}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_material_integration(katana_context):
    """Integration test: create_material with real Katana API.

    This test requires a valid KATANA_API_KEY in the environment.
    It attempts to create a test material.

    Note: This test may fail if:
    - API key is invalid
    - Network is unavailable
    - SKU already exists
    """
    request = CreateMaterialRequest(
        name="Integration Test Material",
        sku=f"TEST-MAT-INT-{int(time.time())}",
        uom="kg",
        is_sellable=False,
        purchase_price=4.99,
    )

    try:
        result = await _create_material_impl(request, katana_context)

        # Verify response structure
        assert isinstance(result.id, int)
        assert result.id > 0
        assert isinstance(result.name, str)
        assert result.name == "Integration Test Material"
        assert isinstance(result.sku, str)
        assert result.sku == request.sku
        assert result.success is True
        assert "created successfully" in result.message.lower()

    except Exception as e:
        # Network/auth errors are acceptable in integration tests
        error_msg = str(e).lower()
        assert any(
            word in error_msg
            for word in [
                "connection",
                "network",
                "auth",
                "timeout",
                "duplicate",
                "already exists",
            ]
        ), f"Unexpected error: {e}"
