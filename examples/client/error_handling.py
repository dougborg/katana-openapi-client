"""
Error Handling and Retry Example

This example demonstrates custom error handling and retry logic on top of
the client's built-in resilience.

Based on the Cookbook recipe: docs/COOKBOOK.md#retry-failed-operations
"""

import asyncio
from collections.abc import Callable
from typing import Any, TypeVar

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.sales_order import create_sales_order
from katana_public_api_client.models import CreateSalesOrderRequest

T = TypeVar("T")


async def retry_with_backoff(
    operation: Callable[[], T],
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
) -> T:
    """
    Retry an operation with exponential backoff.

    Note: Network errors and 429/5xx are already handled by KatanaClient.
    This is for application-level retries.

    Args:
        operation: Async function to retry
        max_attempts: Maximum number of attempts
        backoff_factor: Multiplier for delay between retries

    Returns:
        Result from operation

    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    delay = 1.0

    for attempt in range(max_attempts):
        try:
            return await operation()
        except Exception as e:
            last_exception = e

            if attempt < max_attempts - 1:
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
                delay *= backoff_factor
            else:
                print(f"All {max_attempts} attempts failed")

    raise last_exception


async def create_order_with_retry(order_data: dict[str, Any]):
    """Create order with custom retry logic."""
    async with KatanaClient() as client:

        async def create_op():
            request = CreateSalesOrderRequest(**order_data)
            response = await create_sales_order.asyncio_detailed(
                client=client, body=request
            )

            if response.status_code != 201:
                raise ValueError(f"Failed to create order: {response.status_code}")

            return response.parsed

        return await retry_with_backoff(create_op, max_attempts=3)


async def main():
    """Demo of error handling and retry logic."""
    # Example order data
    order = {
        "customer_id": 123,
        "sales_order_rows": [{"variant_id": 456, "quantity": 5, "price": 29.99}],
    }

    print("Creating sales order with custom retry logic...\n")

    try:
        result = await create_order_with_retry(order)
        print(f"✓ Order created successfully: {result.id}")
    except Exception as e:
        print(f"✗ Failed to create order after retries: {e}")


if __name__ == "__main__":
    asyncio.run(main())
