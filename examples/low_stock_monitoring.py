"""
Low Stock Monitoring Example

This example demonstrates how to monitor inventory levels and identify products
that need reordering.

Based on the Cookbook recipe: docs/COOKBOOK.md#find-low-stock-items
"""

import asyncio
from typing import Any

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.inventory import get_all_inventory_point
from katana_public_api_client.api.variant import get_variant
from katana_public_api_client.utils import unwrap_data


async def get_low_stock_alerts(threshold: int = 10) -> list[dict[str, Any]]:
    """
    Get products below stock threshold with supplier information.

    Args:
        threshold: Minimum stock level before alert

    Returns:
        List of low stock items with details
    """
    low_stock_items = []

    async with KatanaClient() as client:
        # Get all inventory points
        inventory_response = await get_all_inventory_point.asyncio_detailed(
            client=client
        )
        inventory_points = unwrap_data(inventory_response)

        # Get variant details for items below threshold
        for inv_point in inventory_points:
            if inv_point.in_stock < threshold:
                # Get variant details
                variant_response = await get_variant.asyncio_detailed(
                    client=client, id=inv_point.variant_id
                )

                if variant_response.parsed:
                    variant = variant_response.parsed

                    low_stock_items.append(
                        {
                            "sku": variant.sku,
                            "name": variant.name,
                            "current_stock": inv_point.in_stock,
                            "location": inv_point.location_name,
                            "reorder_point": getattr(inv_point, "reorder_point", None),
                            "variant_id": variant.id,
                        }
                    )

    return low_stock_items


async def main():
    """Demo of low stock monitoring."""
    # Set your threshold
    threshold = 20

    print(f"Checking for items with stock below {threshold} units...\n")

    low_stock = await get_low_stock_alerts(threshold=threshold)

    if low_stock:
        print(f"⚠️  Found {len(low_stock)} low stock items:\n")
        for item in low_stock:
            print(f"  SKU: {item['sku']}")
            print(f"  Name: {item['name']}")
            print(f"  Current Stock: {item['current_stock']} units")
            print(f"  Location: {item['location']}")
            if item["reorder_point"]:
                print(f"  Reorder Point: {item['reorder_point']}")
            print()
    else:
        print(f"✓ No items below {threshold} units")


if __name__ == "__main__":
    asyncio.run(main())
