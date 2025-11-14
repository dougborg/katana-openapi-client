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
    assert "{order_id}" in content


def test_load_template_not_found():
    """Test loading a non-existent template raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="Template not found"):
        load_template("nonexistent_template")


def test_format_template_success():
    """Test formatting a template with variables."""
    result = format_template(
        "order_created",
        order_number="PO-2024-001",
        order_id=1234,
        supplier_id=4001,
        location_id=1,
        total_cost=2550.00,
        currency="USD",
        created_at="2024-11-12T10:30:00Z",
        status="NOT_RECEIVED",
    )
    assert "PO-2024-001" in result
    assert "1234" in result
    assert "2,550.00 USD" in result


def test_format_template_missing_variable():
    """Test formatting with missing required variables raises KeyError."""
    with pytest.raises(KeyError):
        format_template("order_created", order_number="PO-001")


def test_verification_match_template_exists():
    """Test that verification match template exists."""
    content = load_template("order_verification_match")
    assert "Perfect Match" in content
    assert "{order_number}" in content


def test_verification_partial_template_exists():
    """Test that verification partial match template exists."""
    content = load_template("order_verification_partial")
    assert "Partial Match" in content
    assert "{discrepancies_list}" in content


def test_verification_no_match_template_exists():
    """Test that verification no match template exists."""
    content = load_template("order_verification_no_match")
    assert "No Match" in content
    assert "{error_message}" in content


def test_order_preview_template_exists():
    """Test that order preview template exists."""
    content = load_template("order_preview")
    assert "Preview" in content
    assert "{items_table}" in content


def test_order_received_template_exists():
    """Test that order received template exists."""
    content = load_template("order_received")
    assert "Received" in content
    assert "{items_received}" in content


def test_error_template_exists():
    """Test that error template exists."""
    content = load_template("error")
    assert "Error" in content
    assert "{error_message}" in content
