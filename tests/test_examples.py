"""
Tests for example scripts to ensure they remain functional.

These tests verify that example code runs without syntax errors and follows
expected patterns, even if they don't make real API calls.
"""

import ast
import importlib.util
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Path to examples directory
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


def load_module_from_file(file_path: Path):
    """Load a Python module from a file path."""
    spec = importlib.util.spec_from_file_location("example_module", file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec from {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["example_module"] = module
    spec.loader.exec_module(module)
    return module


def test_examples_directory_exists():
    """Test that examples directory exists."""
    assert EXAMPLES_DIR.exists()
    assert EXAMPLES_DIR.is_dir()


def test_all_example_files_are_valid_python():
    """Test that all example .py files have valid Python syntax."""
    example_files = list(EXAMPLES_DIR.glob("*.py"))

    # Filter out __init__.py
    example_files = [f for f in example_files if f.name != "__init__.py"]

    assert len(example_files) > 0, "No example files found"

    for example_file in example_files:
        with open(example_file, encoding="utf-8") as f:
            source = f.read()

        try:
            ast.parse(source)
        except SyntaxError as e:
            pytest.fail(f"Syntax error in {example_file.name}: {e}")


def test_all_examples_have_docstrings():
    """Test that all example files have module-level docstrings."""
    example_files = list(EXAMPLES_DIR.glob("*.py"))
    example_files = [f for f in example_files if f.name != "__init__.py"]

    for example_file in example_files:
        with open(example_file, encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)
        docstring = ast.get_docstring(tree)

        assert docstring is not None, (
            f"{example_file.name} is missing a module docstring"
        )
        assert len(docstring) > 20, f"{example_file.name} has an insufficient docstring"


def test_new_cookbook_examples_have_main_function():
    """Test that new cookbook example files have a main() function."""
    # Only check new cookbook examples
    cookbook_examples = [
        "inventory_sync.py",
        "low_stock_monitoring.py",
        "concurrent_requests.py",
        "error_handling.py",
    ]

    for example_name in cookbook_examples:
        example_file = EXAMPLES_DIR / example_name
        if not example_file.exists():
            continue  # Skip if not created yet

        with open(example_file, encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)

        # Find all function definitions (including async)
        functions = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        ]

        assert "main" in functions, f"{example_name} is missing a main() function"


@pytest.mark.asyncio
async def test_inventory_sync_example():
    """Test inventory sync example can be imported and has expected functions."""
    example_file = EXAMPLES_DIR / "inventory_sync.py"
    if not example_file.exists():
        pytest.skip("inventory_sync.py not found")

    module = load_module_from_file(example_file)

    # Check that key functions exist
    assert hasattr(module, "sync_inventory_from_warehouse")
    assert hasattr(module, "main")

    # Test the function signature
    import inspect

    sig = inspect.signature(module.sync_inventory_from_warehouse)
    assert "warehouse_data" in sig.parameters


@pytest.mark.asyncio
async def test_low_stock_monitoring_example():
    """Test low stock monitoring example can be imported."""
    example_file = EXAMPLES_DIR / "low_stock_monitoring.py"
    if not example_file.exists():
        pytest.skip("low_stock_monitoring.py not found")

    module = load_module_from_file(example_file)

    # Check that key functions exist
    assert hasattr(module, "get_low_stock_alerts")
    assert hasattr(module, "main")

    # Test the function signature
    import inspect

    sig = inspect.signature(module.get_low_stock_alerts)
    assert "threshold" in sig.parameters


@pytest.mark.asyncio
async def test_concurrent_requests_example():
    """Test concurrent requests example can be imported."""
    example_file = EXAMPLES_DIR / "concurrent_requests.py"
    if not example_file.exists():
        pytest.skip("concurrent_requests.py not found")

    module = load_module_from_file(example_file)

    # Check that key functions exist
    assert hasattr(module, "fetch_multiple_products_concurrent")
    assert hasattr(module, "main")

    # Test the function signature
    import inspect

    sig = inspect.signature(module.fetch_multiple_products_concurrent)
    assert "product_ids" in sig.parameters


@pytest.mark.asyncio
async def test_error_handling_example():
    """Test error handling example can be imported."""
    example_file = EXAMPLES_DIR / "error_handling.py"
    if not example_file.exists():
        pytest.skip("error_handling.py not found")

    module = load_module_from_file(example_file)

    # Check that key functions exist
    assert hasattr(module, "retry_with_backoff")
    assert hasattr(module, "create_order_with_retry")
    assert hasattr(module, "main")


@pytest.mark.asyncio
async def test_inventory_sync_with_mock():
    """Test inventory sync function with mocked API calls."""
    example_file = EXAMPLES_DIR / "inventory_sync.py"
    if not example_file.exists():
        pytest.skip("inventory_sync.py not found")

    module = load_module_from_file(example_file)

    # Mock variant data
    mock_variant = MagicMock()
    mock_variant.id = 123
    mock_variant.sku = "TEST-001"

    mock_variants_response = MagicMock()
    mock_variants_response.status_code = 200
    mock_variants_response.parsed = MagicMock()
    mock_variants_response.parsed.data = [mock_variant]

    # Mock inventory data
    mock_inventory = MagicMock()
    mock_inventory.variant_id = 123
    mock_inventory.in_stock = 100  # Matches warehouse quantity

    mock_inventory_response = MagicMock()
    mock_inventory_response.status_code = 200
    mock_inventory_response.parsed = MagicMock()
    mock_inventory_response.parsed.data = [mock_inventory]

    with (
        patch(
            "katana_public_api_client.api.variant.get_all_variants.asyncio_detailed",
            new=AsyncMock(return_value=mock_variants_response),
        ),
        patch(
            "katana_public_api_client.api.inventory.get_all_inventory_point.asyncio_detailed",
            new=AsyncMock(return_value=mock_inventory_response),
        ),
        patch("katana_public_api_client.katana_client.load_dotenv"),
    ):
        warehouse_data = [{"sku": "TEST-001", "quantity": 100}]

        # This should work with mocked data
        result = await module.sync_inventory_from_warehouse(warehouse_data)

        # Updated to match new return structure (matched, mismatched, skipped)
        assert result["matched"] == 1
        assert result["mismatched"] == 0
        assert result["skipped"] == 0


@pytest.mark.asyncio
async def test_retry_with_backoff():
    """Test the retry_with_backoff function logic."""
    example_file = EXAMPLES_DIR / "error_handling.py"
    if not example_file.exists():
        pytest.skip("error_handling.py not found")

    module = load_module_from_file(example_file)

    # Test successful operation
    async def successful_op():
        return "success"

    result = await module.retry_with_backoff(successful_op, max_attempts=3)
    assert result == "success"

    # Test operation that fails then succeeds
    call_count = 0

    async def fail_then_succeed():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Temporary failure")
        return "success"

    call_count = 0
    result = await module.retry_with_backoff(
        fail_then_succeed, max_attempts=3, backoff_factor=0.1
    )
    assert result == "success"
    assert call_count == 2

    # Test operation that always fails
    async def always_fails():
        raise ValueError("Permanent failure")

    with pytest.raises(ValueError, match="Permanent failure"):
        await module.retry_with_backoff(always_fails, max_attempts=2)


def test_examples_import_from_correct_modules():
    """Test that examples import from the correct package."""
    example_files = list(EXAMPLES_DIR.glob("*.py"))
    example_files = [f for f in example_files if f.name != "__init__.py"]

    for example_file in example_files:
        with open(example_file, encoding="utf-8") as f:
            source = f.read()

        # Check that examples import from katana_public_api_client
        assert (
            "from katana_public_api_client import" in source
            or "from katana_public_api_client." in source
        ), f"{example_file.name} doesn't import from katana_public_api_client"

        # Check that examples use KatanaClient
        assert "KatanaClient" in source, f"{example_file.name} doesn't use KatanaClient"
