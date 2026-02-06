#!/usr/bin/env python3
"""Test script to verify MCP resources are working correctly.

This script directly calls resource handlers to verify they:
1. Can access the Katana API
2. Return properly structured data
3. Include summaries and next actions
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from dotenv import load_dotenv
from fastmcp import Context

from katana_public_api_client import KatanaClient
from katana_public_api_client.client import AuthenticatedClient

# Add project root to path for local MCP server imports
_project_root = Path(__file__).parent.parent
sys.path.insert(0, str(_project_root / "katana_mcp_server" / "src"))

if TYPE_CHECKING:
    pass


def create_test_context(client: AuthenticatedClient) -> Context:
    """Create a test context with real KatanaClient.

    Args:
        client: Real KatanaClient instance

    Returns:
        Mock Context object with proper FastMCP structure
    """
    context = MagicMock(spec=Context)
    mock_request_context = MagicMock()
    mock_lifespan_context = MagicMock()

    # Attach real client to mock context
    mock_lifespan_context.client = client
    mock_request_context.lifespan_context = mock_lifespan_context
    context.request_context = mock_request_context

    return context


async def run_resource_test(resource_name: str, resource_func, context: Context):
    """Run a single resource test and print results.

    Args:
        resource_name: Name of the resource being tested
        resource_func: Async function that implements the resource
        context: Test context with KatanaClient
    """
    print(f"\n{'=' * 60}")
    print(f"Testing: {resource_name}")
    print(f"{'=' * 60}")

    try:
        result = await resource_func(context)

        # Print summary
        if isinstance(result, dict):
            if "summary" in result:
                print(f"✓ Summary: {json.dumps(result['summary'], indent=2)}")
            if "generated_at" in result:
                print(f"✓ Generated at: {result['generated_at']}")
            if "next_actions" in result:
                print(
                    f"✓ Next actions: {len(result.get('next_actions', []))} suggestions"
                )

            # Print data counts
            data_keys = [
                k
                for k in result
                if k not in ["summary", "generated_at", "next_actions"]
            ]
            for key in data_keys:
                if isinstance(result[key], list):
                    print(f"✓ {key}: {len(result[key])} items")
                elif isinstance(result[key], dict):
                    print(f"✓ {key}: {len(result[key])} entries")

            print(f"\n✓ SUCCESS: {resource_name} returned data")
            return True
        else:
            print(
                f"✓ SUCCESS: {resource_name} returned data (type: {type(result).__name__})"
            )
            return True

    except Exception as e:
        print(f"✗ ERROR: {resource_name} failed")
        print(f"  Error type: {type(e).__name__}")
        print(f"  Error message: {e!s}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    # Load environment variables
    load_dotenv()

    # Get API key
    api_key = os.getenv("KATANA_API_KEY")
    if not api_key:
        print("ERROR: KATANA_API_KEY environment variable is required")
        print("Set it in your .env file or export it:")
        print("  export KATANA_API_KEY=your-api-key-here")
        sys.exit(1)

    assert api_key is not None  # Type narrowing for type checker
    base_url = os.getenv("KATANA_BASE_URL", "https://api.katanamrp.com/v1")

    print("=" * 60)
    print("MCP Resources Test")
    print("=" * 60)
    print(f"API Base URL: {base_url}")
    print("API Key: [configured]")

    # Initialize KatanaClient
    async with KatanaClient(
        api_key=api_key,
        base_url=base_url,
        timeout=30.0,
        max_retries=3,
        max_pages=10,
    ) as client:
        # Create test context
        context = create_test_context(client)

        # Import resource handlers
        from katana_mcp.resources.help import (
            get_help_index,
            get_help_resources,
            get_help_tools,
            get_help_workflows,
        )
        from katana_mcp.resources.inventory import (
            get_inventory_items,
            get_stock_movements,
        )
        from katana_mcp.resources.orders import (
            get_manufacturing_orders,
            get_purchase_orders,
            get_sales_orders,
        )

        # Test resources
        results = []

        # Help resources (should always work - no API calls)
        results.append(
            await run_resource_test("katana://help", get_help_index, context)
        )
        results.append(
            await run_resource_test(
                "katana://help/resources", get_help_resources, context
            )
        )
        results.append(
            await run_resource_test("katana://help/tools", get_help_tools, context)
        )
        results.append(
            await run_resource_test(
                "katana://help/workflows", get_help_workflows, context
            )
        )

        # Data resources (require API access)
        results.append(
            await run_resource_test(
                "katana://inventory/items", get_inventory_items, context
            )
        )
        results.append(
            await run_resource_test(
                "katana://inventory/stock-movements", get_stock_movements, context
            )
        )
        results.append(
            await run_resource_test("katana://sales-orders", get_sales_orders, context)
        )
        results.append(
            await run_resource_test(
                "katana://purchase-orders", get_purchase_orders, context
            )
        )
        results.append(
            await run_resource_test(
                "katana://manufacturing-orders", get_manufacturing_orders, context
            )
        )

        # Print summary
        print(f"\n{'=' * 60}")
        print("Test Summary")
        print(f"{'=' * 60}")
        passed = sum(results)
        total = len(results)
        print(f"Passed: {passed}/{total}")
        print(f"Failed: {total - passed}/{total}")

        if all(results):
            print("\n✓ All resources are working correctly!")
            sys.exit(0)
        else:
            print("\n✗ Some resources failed. Check errors above.")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
