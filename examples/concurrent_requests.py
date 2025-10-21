"""
Concurrent Requests Example

This example demonstrates how to make multiple API requests concurrently using
asyncio.gather for better performance.

Based on the Cookbook recipe: docs/COOKBOOK.md#concurrent-requests
"""

import asyncio
from typing import Any

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_product


async def fetch_multiple_products_concurrent(product_ids: list[int]) -> list[Any]:
    """
    Fetch multiple products concurrently.

    Args:
        product_ids: List of product IDs to fetch

    Returns:
        List of product objects
    """
    async with KatanaClient() as client:
        # Create tasks for concurrent requests
        tasks = [
            get_product.asyncio_detailed(client=client, id=product_id)
            for product_id in product_ids
        ]

        # Execute all requests concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Extract successful results
        products = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                print(f"✗ Failed to fetch product {product_ids[i]}: {response}")
            elif hasattr(response, "parsed") and response.parsed:
                products.append(response.parsed)

        print(f"Successfully fetched {len(products)}/{len(product_ids)} products")
        return products


async def main():
    """Demo of concurrent product fetching."""
    # Example product IDs - replace with actual IDs from your Katana instance
    product_ids = [1, 2, 3, 4, 5]

    print(f"Fetching {len(product_ids)} products concurrently...\n")

    import time

    start = time.time()
    products = await fetch_multiple_products_concurrent(product_ids)
    elapsed = time.time() - start

    print(f"\n✓ Fetched {len(products)} products in {elapsed:.2f} seconds")

    if products:
        print("\nProducts fetched:")
        for product in products:
            print(f"  - {product.name} (ID: {product.id})")


if __name__ == "__main__":
    asyncio.run(main())
