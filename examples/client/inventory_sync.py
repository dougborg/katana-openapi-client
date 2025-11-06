"""
Inventory Synchronization Example

This example demonstrates how to compare inventory levels between an external
warehouse system and Katana to identify discrepancies.

Note: This example shows how to COMPARE inventory levels for monitoring purposes.
For actual inventory adjustments, use the Katana UI or stocktake API workflow.

Based on the Cookbook recipe: docs/COOKBOOK.md#sync-inventory-from-external-system
"""

import asyncio
from typing import Any

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.inventory import get_all_inventory_point
from katana_public_api_client.api.variant import get_all_variants
from katana_public_api_client.utils import unwrap_data


async def sync_inventory_from_warehouse(
    warehouse_data: list[dict[str, Any]],
) -> dict[str, int]:
    """
    Compare inventory levels between external warehouse system and Katana.

    Args:
        warehouse_data: List of dicts with 'sku' and 'quantity' keys

    Returns:
        Dict with 'matched', 'mismatched', 'skipped' counts

    Example warehouse_data:
        [
            {"sku": "WDG-001", "quantity": 150},
            {"sku": "WDG-002", "quantity": 75},
        ]
    """
    stats = {"matched": 0, "mismatched": 0, "skipped": 0}
    discrepancies = []

    async with KatanaClient() as client:
        # Get all variants to build SKU -> variant_id lookup
        variants_response = await get_all_variants.asyncio_detailed(client=client)
        variants = unwrap_data(variants_response)

        # Build SKU lookup map
        sku_to_variant = {v.sku: v for v in variants if v.sku}

        # Get inventory levels
        inventory_response = await get_all_inventory_point.asyncio_detailed(
            client=client
        )
        inventory_points = unwrap_data(inventory_response)

        # Build variant_id -> inventory lookup
        inventory_by_variant = {inv.variant_id: inv for inv in inventory_points}

        # Compare inventory for each warehouse item
        for item in warehouse_data:
            sku = item["sku"]
            warehouse_qty = item["quantity"]

            variant = sku_to_variant.get(sku)
            if not variant:
                print(f"Warning: SKU {sku} not found in Katana")
                stats["skipped"] += 1
                continue

            inventory = inventory_by_variant.get(variant.id)
            if not inventory:
                print(f"Warning: No inventory data for SKU {sku}")
                stats["skipped"] += 1
                continue

            katana_qty = inventory.in_stock

            if katana_qty == warehouse_qty:
                stats["matched"] += 1
                print(f"✓ {sku}: Inventory matches ({katana_qty} units)")
            else:
                stats["mismatched"] += 1
                diff = warehouse_qty - katana_qty
                discrepancies.append(
                    {
                        "sku": sku,
                        "katana_qty": katana_qty,
                        "warehouse_qty": warehouse_qty,
                        "difference": diff,
                    }
                )
                print(
                    f"⚠️  {sku}: Mismatch (Katana: {katana_qty}, Warehouse: {warehouse_qty}, Diff: {diff:+d})"
                )

    if discrepancies:
        print(f"\nFound {len(discrepancies)} discrepancies:")
        for disc in discrepancies:
            print(
                f"  {disc['sku']}: Katana={disc['katana_qty']}, Warehouse={disc['warehouse_qty']}, Diff={disc['difference']:+d}"
            )

    return stats


async def main():
    """Demo of inventory comparison between warehouse and Katana."""
    # Example warehouse inventory data
    # In production, this would come from your warehouse management system
    warehouse_inventory = [
        {"sku": "WIDGET-001", "quantity": 150},
        {"sku": "GADGET-002", "quantity": 75},
        {"sku": "TOOL-003", "quantity": 200},
    ]

    print("Comparing inventory between warehouse system and Katana...")
    print(f"Checking {len(warehouse_inventory)} items\n")

    results = await sync_inventory_from_warehouse(warehouse_inventory)

    print("\nComparison complete!")
    print(f"  Matched:     {results['matched']}")
    print(f"  Mismatched:  {results['mismatched']}")
    print(f"  Skipped:     {results['skipped']}")


if __name__ == "__main__":
    asyncio.run(main())
