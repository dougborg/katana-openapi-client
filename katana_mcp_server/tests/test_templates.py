"""Tests for template loader functionality."""

import pytest
from katana_mcp.templates import TEMPLATE_DIR, format_template, load_template


def test_template_dir_exists():
    """Test that TEMPLATE_DIR is a valid path."""
    assert TEMPLATE_DIR.exists()
    assert TEMPLATE_DIR.is_dir()


def test_load_template_success():
    """Test loading an existing template."""
    content = load_template("order_created")
    assert "Purchase Order Created" in content
    assert "{order_number}" in content
    assert "{id}" in content


def test_load_template_not_found():
    """Test loading a non-existent template raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="Template not found"):
        load_template("nonexistent_template")


def test_format_template_success():
    """Test formatting a template with variables."""
    result = format_template(
        "order_created",
        order_number="PO-2024-001",
        id=1234,
        supplier_id=4001,
        location_id=1,
        total_cost=2550.00,
        currency="USD",
        status="NOT_RECEIVED",
        entity_type="regular",
    )
    assert "PO-2024-001" in result
    assert "1234" in result
    assert "2,550.00" in result


def test_format_template_missing_variable():
    """Test formatting with missing required variables raises KeyError."""
    with pytest.raises(KeyError):
        format_template("order_created", order_number="PO-001")


# ============================================================================
# Purchase Order Templates
# ============================================================================


def test_order_preview_template_exists():
    """Test that order preview template exists."""
    content = load_template("order_preview")
    assert "Preview" in content
    assert "{next_actions_text}" in content


def test_order_created_template_exists():
    """Test that order created template exists."""
    content = load_template("order_created")
    assert "Purchase Order Created" in content
    assert "{order_number}" in content
    assert "{id}" in content


def test_order_received_template_exists():
    """Test that order received template exists."""
    content = load_template("order_received")
    assert "Received" in content
    assert "{items_received}" in content


# ============================================================================
# Order Verification Templates
# ============================================================================


def test_verification_match_template_exists():
    """Test that verification match template exists."""
    content = load_template("order_verification_match")
    assert "Perfect Match" in content
    assert "{order_id}" in content
    assert "{matches_text}" in content


def test_verification_partial_template_exists():
    """Test that verification partial match template exists."""
    content = load_template("order_verification_partial")
    assert "Partial Match" in content
    assert "{discrepancies_text}" in content


def test_verification_no_match_template_exists():
    """Test that verification no match template exists."""
    content = load_template("order_verification_no_match")
    assert "No Match" in content
    assert "{discrepancies_text}" in content


# ============================================================================
# Item Templates
# ============================================================================


def test_item_search_results_template_exists():
    """Test that item search results template exists."""
    content = load_template("item_search_results")
    assert "Search Results" in content
    assert "{query}" in content
    assert "{items_table}" in content
    assert "{result_count}" in content


def test_item_details_template_exists():
    """Test that item details template exists."""
    content = load_template("item_details")
    assert "Item Details" in content
    assert "{sku}" in content
    assert "{name}" in content
    assert "{sales_price" in content


def test_stock_summary_template_exists():
    """Test that stock summary template exists."""
    content = load_template("stock_summary")
    assert "{sku}" in content


# ============================================================================
# Order Fulfillment Templates
# ============================================================================


def test_order_fulfilled_template_exists():
    """Test that order fulfilled template exists."""
    content = load_template("order_fulfilled")
    assert "{order_type}" in content
    assert "{order_number}" in content
    assert "{status}" in content


# ============================================================================
# Utility Templates
# ============================================================================


def test_error_template_exists():
    """Test that error template exists."""
    content = load_template("error")
    assert "Error" in content
    assert "{error_message}" in content


# ============================================================================
# Template Formatting Tests
# ============================================================================


def test_format_order_preview():
    """Test formatting order preview template."""
    result = format_template(
        "order_preview",
        order_number="PO-2024-001",
        supplier_id=4001,
        location_id=1,
        total_cost=1500.00,
        currency="USD",
        status="NOT_RECEIVED",
        entity_type="regular",
        next_actions_text="- Set confirm=true to create",
    )
    assert "Preview" in result
    assert "PO-2024-001" in result
    assert "1,500.00" in result


def test_format_order_verification_match():
    """Test formatting order verification match template."""
    result = format_template(
        "order_verification_match",
        order_id=1234,
        overall_status="match",
        message="All items verified",
        matches_text="- WIDGET-001: 100 @ $25.50 - Perfect match",
        suggested_actions_text="- Proceed to receive order",
    )
    assert "1234" in result
    assert "All items verified" in result


def test_format_item_search_results():
    """Test formatting item search results template."""
    result = format_template(
        "item_search_results",
        query="widget",
        result_count=5,
        items_table="| SKU | Name | Type |\n|-----|------|------|\n| W-001 | Widget | product |",
        product_count=3,
        material_count=2,
        service_count=0,
    )
    assert "widget" in result
    assert "5 items found" in result


def test_format_order_fulfilled():
    """Test formatting order fulfilled template."""
    result = format_template(
        "order_fulfilled",
        order_type="Manufacturing",
        order_number="MO-001",
        order_id=5678,
        fulfilled_at="2024-11-12T14:30:00Z",
        items_count="N/A",  # Not available in fulfill response
        total_value="N/A",  # Not available in fulfill response
        status="DONE",
        inventory_updates="- Finished goods added to stock",
        next_steps="- Check inventory levels",
    )
    assert "Manufacturing" in result
    assert "MO-001" in result
    assert "DONE" in result
    assert "N/A" in result  # Verify N/A values are rendered
