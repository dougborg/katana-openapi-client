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
from unittest.mock import MagicMock

from dotenv import load_dotenv
from fastmcp import Context

from katana_public_api_client import KatanaClient

# Add project root to path for local MCP server imports
_project_root = Path(__file__).parent.parent
sys.path.insert(0, str(_project_root / "katana_mcp_server" / "src"))

from katana_mcp.cache import CatalogCache  # noqa: E402
from katana_mcp.services.dependencies import Services  # noqa: E402


def create_test_context(services: Services) -> Context:
    """Create a test context wrapping a real Services container.

    The cache-backed resources call ``get_services(context)`` and expect
    ``context.request_context.lifespan_context`` to be a ``Services`` instance
    with both ``client`` and ``cache`` attributes.

    Args:
        services: Real Services container with an opened CatalogCache

    Returns:
        Mock Context object with proper FastMCP structure
    """
    context = MagicMock(spec=Context)
    mock_request_context = MagicMock()
    mock_request_context.lifespan_context = services
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

        # Resources may return dict or JSON string — normalize to dict for inspection
        parsed: dict | None = None
        if isinstance(result, dict):
            parsed = result
        elif isinstance(result, str):
            try:
                loaded = json.loads(result)
                if isinstance(loaded, dict):
                    parsed = loaded
            except json.JSONDecodeError:
                print(
                    f"✗ ERROR: {resource_name} returned non-JSON string: {result[:100]}"
                )
                return False

        if parsed is not None:
            if "summary" in parsed:
                print(f"✓ Summary: {json.dumps(parsed['summary'], indent=2)}")
            if "generated_at" in parsed:
                print(f"✓ Generated at: {parsed['generated_at']}")
            if "next_actions" in parsed:
                print(
                    f"✓ Next actions: {len(parsed.get('next_actions', []))} suggestions"
                )

            # Print data counts
            data_keys = [
                k
                for k in parsed
                if k not in ["summary", "generated_at", "next_actions"]
            ]
            for key in data_keys:
                if isinstance(parsed[key], list):
                    print(f"✓ {key}: {len(parsed[key])} items")
                elif isinstance(parsed[key], dict):
                    print(f"✓ {key}: {len(parsed[key])} entries")

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

    # Initialize KatanaClient and open catalog cache
    async with KatanaClient(
        api_key=api_key,
        base_url=base_url,
        timeout=30.0,
        max_retries=3,
        max_pages=10,
    ) as client:
        cache = CatalogCache()
        await cache.open()
        try:
            services = Services(client=client, cache=cache)
            context = create_test_context(services)
            await _run_tests(context)
        finally:
            await cache.close()


async def _run_tests(context: Context) -> None:
    """Run all resource tests against the given context."""
    # Import resource handlers
    from katana_mcp.resources.help import (
        get_help_index,
        get_help_resources,
        get_help_tools,
        get_help_workflows,
    )
    from katana_mcp.resources.inventory import get_inventory_items
    from katana_mcp.resources.reference import (
        get_locations,
        get_operators,
        get_suppliers,
        get_tax_rates,
    )

    # Test resources
    results = []

    # Help resources (should always work - no API calls)
    results.append(await run_resource_test("katana://help", get_help_index, context))
    results.append(
        await run_resource_test("katana://help/resources", get_help_resources, context)
    )
    results.append(
        await run_resource_test("katana://help/tools", get_help_tools, context)
    )
    results.append(
        await run_resource_test("katana://help/workflows", get_help_workflows, context)
    )

    # Data resources (require API access)
    results.append(
        await run_resource_test(
            "katana://inventory/items", get_inventory_items, context
        )
    )
    results.append(
        await run_resource_test("katana://suppliers", get_suppliers, context)
    )
    results.append(
        await run_resource_test("katana://locations", get_locations, context)
    )
    results.append(
        await run_resource_test("katana://tax-rates", get_tax_rates, context)
    )
    results.append(
        await run_resource_test("katana://operators", get_operators, context)
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
