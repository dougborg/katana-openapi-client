# Katana API Client Cookbook

This cookbook provides practical, copy-paste recipes for common integration scenarios
with the Katana Manufacturing ERP API.

## Table of Contents

1. [Inventory Management](#inventory-management)
1. [Order Processing](#order-processing)
1. [Manufacturing Operations](#manufacturing-operations)
1. [Error Handling Patterns](#error-handling-patterns)
1. [Integration Patterns](#integration-patterns)
1. [Observability](#observability)
1. [Performance Optimization](#performance-optimization)
1. [Testing Patterns](#testing-patterns)

## Prerequisites

All recipes assume you have:

```python
# .env file with your API key
KATANA_API_KEY=your-api-key-here
KATANA_BASE_URL=https://api.katanamrp.com/v1  # Optional
```

## Inventory Management

### Sync Inventory from External System

Keep Katana inventory synchronized with an external warehouse management system.

```python
import asyncio
from typing import Any

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.inventory import get_all_inventory_point
from katana_public_api_client.api.variant import get_all_variants
from katana_public_api_client.utils import unwrap_data


async def sync_inventory_from_warehouse(warehouse_data: list[dict[str, Any]]) -> dict[str, int]:
    """
    Sync inventory levels from external warehouse system.

    Args:
        warehouse_data: List of dicts with 'sku' and 'quantity' keys

    Returns:
        Dict with 'updated', 'skipped', 'errors' counts

    Example warehouse_data:
        [
            {"sku": "WDG-001", "quantity": 150},
            {"sku": "WDG-002", "quantity": 75},
        ]
    """
    stats = {"updated": 0, "skipped": 0, "errors": 0}

    async with KatanaClient() as client:
        # Get all variants to build SKU -> variant_id lookup
        from katana_public_api_client.api.variant import get_all_variants

        variants_response = await get_all_variants.asyncio_detailed(client=client)
        variants = unwrap_data(variants_response)

        # Build SKU lookup map
        sku_to_variant = {v.sku: v for v in variants if v.sku}

        # Update inventory for each warehouse item
        from katana_public_api_client.api.stock_adjustment import create_stock_adjustment
        from katana_public_api_client.models import CreateStockAdjustmentRequest

        for item in warehouse_data:
            sku = item["sku"]
            new_quantity = item["quantity"]

            variant = sku_to_variant.get(sku)
            if not variant:
                print(f"Warning: SKU {sku} not found in Katana")
                stats["skipped"] += 1
                continue

            try:
                # Create stock adjustment to set new quantity
                adjustment = CreateStockAdjustmentRequest(
                    variant_id=variant.id,
                    adjustment_type="set",  # Set to absolute value
                    quantity=new_quantity,
                    note=f"Synced from warehouse system"
                )

                response = await create_stock_adjustment.asyncio_detailed(
                    client=client,
                    body=adjustment
                )

                if response.status_code == 201:
                    stats["updated"] += 1
                    print(f"✓ Updated {sku}: {new_quantity} units")
                else:
                    stats["errors"] += 1
                    print(f"✗ Failed to update {sku}: {response.status_code}")

            except Exception as e:
                stats["errors"] += 1
                print(f"✗ Error updating {sku}: {e}")

    return stats


# Usage
if __name__ == "__main__":
    warehouse_inventory = [
        {"sku": "WDG-001", "quantity": 150},
        {"sku": "WDG-002", "quantity": 75},
        {"sku": "GADGET-A", "quantity": 200},
    ]

    results = asyncio.run(sync_inventory_from_warehouse(warehouse_inventory))
    print(f"\nSync complete: {results}")
```

### Find Low Stock Items

Identify products that need reordering.

```python
import asyncio
from typing import Any

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.inventory import get_all_inventory_point
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
        from katana_public_api_client.api.variant import get_variant

        for inv_point in inventory_points:
            if inv_point.in_stock < threshold:
                # Get variant details
                variant_response = await get_variant.asyncio_detailed(
                    client=client,
                    id=inv_point.variant_id
                )

                if variant_response.parsed:
                    variant = variant_response.parsed

                    low_stock_items.append({
                        "sku": variant.sku,
                        "name": variant.name,
                        "current_stock": inv_point.in_stock,
                        "location": inv_point.location_name,
                        "reorder_point": getattr(inv_point, "reorder_point", None),
                        "variant_id": variant.id,
                    })

    return low_stock_items


# Usage
if __name__ == "__main__":
    low_stock = asyncio.run(get_low_stock_alerts(threshold=20))

    print(f"Found {len(low_stock)} low stock items:\n")
    for item in low_stock:
        print(f"  {item['sku']}: {item['current_stock']} units at {item['location']}")
```

### Monitor Negative Stock

Detect and report negative inventory situations.

```python
import asyncio
from datetime import datetime

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.inventory import get_all_negative_stock
from katana_public_api_client.utils import unwrap_data


async def monitor_negative_stock() -> list[dict]:
    """
    Monitor and report negative stock situations.

    Returns:
        List of negative stock items with details
    """
    async with KatanaClient() as client:
        response = await get_all_negative_stock.asyncio_detailed(client=client)
        negative_items = unwrap_data(response)

        issues = []
        for item in negative_items:
            issues.append({
                "variant_sku": item.variant_sku,
                "variant_name": item.variant_name,
                "location": item.location_name,
                "quantity": item.in_stock,  # Negative value
                "timestamp": datetime.now().isoformat(),
            })

        return issues


# Usage
if __name__ == "__main__":
    negative_stock = asyncio.run(monitor_negative_stock())

    if negative_stock:
        print(f"⚠️  WARNING: {len(negative_stock)} items with negative stock!\n")
        for item in negative_stock:
            print(f"  {item['variant_sku']}: {item['quantity']} units at {item['location']}")
    else:
        print("✓ No negative stock issues")
```

## Order Processing

### Process Bulk Sales Orders

Efficiently create multiple sales orders from an external system.

```python
import asyncio
from typing import Any

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.sales_order import create_sales_order
from katana_public_api_client.models import CreateSalesOrderRequest


async def process_bulk_orders(
    orders: list[dict[str, Any]]
) -> tuple[list[int], list[dict]]:
    """
    Process a batch of sales orders efficiently.

    Args:
        orders: List of order dicts with customer_id, items, etc.

    Returns:
        Tuple of (successful_order_ids, failed_orders)

    Example order format:
        {
            "customer_id": 123,
            "items": [
                {"variant_id": 456, "quantity": 5, "price": 29.99},
            ],
            "notes": "Rush order"
        }
    """
    successful = []
    failed = []

    async with KatanaClient() as client:
        for order_data in orders:
            try:
                # Build sales order request
                sales_order = CreateSalesOrderRequest(
                    customer_id=order_data["customer_id"],
                    sales_order_rows=[
                        {
                            "variant_id": item["variant_id"],
                            "quantity": item["quantity"],
                            "price": item["price"],
                        }
                        for item in order_data["items"]
                    ],
                    notes=order_data.get("notes", ""),
                )

                response = await create_sales_order.asyncio_detailed(
                    client=client,
                    body=sales_order
                )

                if response.status_code == 201 and response.parsed:
                    successful.append(response.parsed.id)
                    print(f"✓ Created order {response.parsed.id}")
                else:
                    failed.append({
                        "order": order_data,
                        "status": response.status_code,
                        "error": "Failed to create order"
                    })

            except Exception as e:
                failed.append({
                    "order": order_data,
                    "error": str(e)
                })
                print(f"✗ Error creating order: {e}")

    return successful, failed


# Usage
if __name__ == "__main__":
    orders_to_process = [
        {
            "customer_id": 123,
            "items": [
                {"variant_id": 456, "quantity": 5, "price": 29.99},
                {"variant_id": 457, "quantity": 2, "price": 49.99},
            ],
            "notes": "Express shipping requested"
        },
        {
            "customer_id": 124,
            "items": [
                {"variant_id": 458, "quantity": 10, "price": 19.99},
            ],
        },
    ]

    successful, failed = asyncio.run(process_bulk_orders(orders_to_process))
    print(f"\nProcessed: {len(successful)} successful, {len(failed)} failed")
```

### Monitor Overdue Orders

Find sales orders that are past their expected delivery date.

```python
import asyncio
from datetime import datetime, timedelta

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.sales_order import get_all_sales_orders
from katana_public_api_client.utils import unwrap_data


async def check_overdue_orders(days_overdue: int = 0) -> list[dict]:
    """
    Find all overdue sales orders.

    Args:
        days_overdue: Number of days past due date (0 = due today or earlier)

    Returns:
        List of overdue orders with details
    """
    async with KatanaClient() as client:
        # Get all open/in-progress orders
        response = await get_all_sales_orders.asyncio_detailed(
            client=client,
            status="open"  # or "in_progress"
        )

        orders = unwrap_data(response)
        today = datetime.now().date()
        cutoff_date = today - timedelta(days=days_overdue)

        overdue = []
        for order in orders:
            if hasattr(order, 'expected_delivery_date') and order.expected_delivery_date:
                # Parse the delivery date
                delivery_date = order.expected_delivery_date
                if isinstance(delivery_date, str):
                    delivery_date = datetime.fromisoformat(delivery_date).date()

                if delivery_date <= cutoff_date:
                    days_late = (today - delivery_date).days
                    overdue.append({
                        "order_id": order.id,
                        "customer_name": getattr(order, "customer_name", "Unknown"),
                        "expected_date": delivery_date.isoformat(),
                        "days_late": days_late,
                        "status": order.status,
                    })

        return sorted(overdue, key=lambda x: x["days_late"], reverse=True)


# Usage
if __name__ == "__main__":
    overdue_orders = asyncio.run(check_overdue_orders(days_overdue=0))

    if overdue_orders:
        print(f"⚠️  {len(overdue_orders)} overdue orders:\n")
        for order in overdue_orders:
            print(f"  Order #{order['order_id']}: {order['days_late']} days late")
            print(f"    Customer: {order['customer_name']}")
            print(f"    Expected: {order['expected_date']}\n")
    else:
        print("✓ No overdue orders")
```

## Manufacturing Operations

### Monitor Manufacturing Status

Get real-time view of manufacturing capacity and status.

```python
import asyncio
from collections import defaultdict

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.manufacturing_order import get_all_manufacturing_orders
from katana_public_api_client.utils import unwrap_data


async def check_manufacturing_capacity() -> dict[str, int]:
    """
    Get real-time view of manufacturing capacity by status.

    Returns:
        Dict with counts by status (planned, in_progress, done, etc.)
    """
    async with KatanaClient() as client:
        response = await get_all_manufacturing_orders.asyncio_detailed(client=client)
        manufacturing_orders = unwrap_data(response)

        # Count by status
        status_counts = defaultdict(int)
        for mo in manufacturing_orders:
            status_counts[mo.status] += 1

        return dict(status_counts)


# Usage
if __name__ == "__main__":
    capacity = asyncio.run(check_manufacturing_capacity())

    print("Manufacturing Capacity Overview:\n")
    for status, count in capacity.items():
        print(f"  {status}: {count} orders")
```

### Create Manufacturing Orders from Sales Orders

Automatically create manufacturing orders when sales orders are received.

```python
import asyncio

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.manufacturing_order import make_to_order_manufacturing_order
from katana_public_api_client.models import MakeToOrderManufacturingOrderRequest


async def create_manufacturing_from_sales(sales_order_id: int) -> int | None:
    """
    Automatically create manufacturing orders for a sales order.

    Args:
        sales_order_id: ID of the sales order

    Returns:
        Manufacturing order ID if created, None if failed
    """
    async with KatanaClient() as client:
        try:
            request = MakeToOrderManufacturingOrderRequest(
                sales_order_id=sales_order_id
            )

            response = await make_to_order_manufacturing_order.asyncio_detailed(
                client=client,
                body=request
            )

            if response.status_code == 201 and response.parsed:
                mo_id = response.parsed.id
                print(f"✓ Created manufacturing order {mo_id} for sales order {sales_order_id}")
                return mo_id
            else:
                print(f"✗ Failed to create MO: {response.status_code}")
                return None

        except Exception as e:
            print(f"✗ Error creating manufacturing order: {e}")
            return None


# Usage
if __name__ == "__main__":
    mo_id = asyncio.run(create_manufacturing_from_sales(sales_order_id=12345))
    if mo_id:
        print(f"Manufacturing order {mo_id} ready for production")
```

## Error Handling Patterns

### Retry Failed Operations

Implement custom retry logic for application-level errors.

```python
import asyncio
from typing import Any, TypeVar, Callable

import httpx

from katana_public_api_client import KatanaClient

T = TypeVar('T')


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


# Usage example
async def create_order_with_retry(order_data: dict[str, Any]):
    """Create order with custom retry logic."""
    async with KatanaClient() as client:
        from katana_public_api_client.api.sales_order import create_sales_order
        from katana_public_api_client.models import CreateSalesOrderRequest

        async def create_op():
            request = CreateSalesOrderRequest(**order_data)
            response = await create_sales_order.asyncio_detailed(
                client=client,
                body=request
            )

            if response.status_code != 201:
                raise ValueError(f"Failed to create order: {response.status_code}")

            return response.parsed

        return await retry_with_backoff(create_op, max_attempts=3)


if __name__ == "__main__":
    order = {
        "customer_id": 123,
        "sales_order_rows": [
            {"variant_id": 456, "quantity": 5, "price": 29.99}
        ]
    }

    result = asyncio.run(create_order_with_retry(order))
    print(f"Order created: {result.id}")
```

### Graceful Degradation

Handle API failures with fallback to cached data.

```python
import asyncio
import json
from pathlib import Path
from typing import Any

import httpx

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products
from katana_public_api_client.utils import unwrap_data


CACHE_FILE = Path("product_cache.json")


async def get_products_with_fallback() -> list[Any]:
    """
    Get products with fallback to cached data on failure.

    Returns:
        List of products (from API or cache)
    """
    try:
        async with KatanaClient(timeout=10.0) as client:
            response = await get_all_products.asyncio_detailed(client=client)
            products = unwrap_data(response)

            # Cache successful response
            cache_data = [
                {
                    "id": p.id,
                    "name": p.name,
                    "sku": p.sku,
                }
                for p in products
            ]
            CACHE_FILE.write_text(json.dumps(cache_data, indent=2))

            print(f"✓ Retrieved {len(products)} products from API")
            return products

    except (httpx.TimeoutException, httpx.NetworkError, Exception) as e:
        print(f"⚠️  API request failed: {e}")

        # Fallback to cache
        if CACHE_FILE.exists():
            cache_data = json.loads(CACHE_FILE.read_text())
            print(f"✓ Using {len(cache_data)} cached products")
            return cache_data
        else:
            print("✗ No cache available")
            raise


# Usage
if __name__ == "__main__":
    products = asyncio.run(get_products_with_fallback())
    print(f"Have {len(products)} products available")
```

## Integration Patterns

### Webhook Event Handler

Handle incoming webhook events from Katana.

```python
from typing import Any

from flask import Flask, request, jsonify
import hmac
import hashlib

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.sales_order import get_sales_order


app = Flask(__name__)
WEBHOOK_SECRET = "your-webhook-secret"  # From Katana webhook settings


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Verify webhook signature from Katana.

    Args:
        payload: Raw request body bytes
        signature: X-Katana-Signature header value

    Returns:
        True if signature is valid
    """
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


@app.route("/webhooks/katana", methods=["POST"])
def handle_katana_webhook():
    """Handle incoming webhooks from Katana."""
    # Verify signature
    signature = request.headers.get("X-Katana-Signature", "")
    if not verify_webhook_signature(request.data, signature):
        return jsonify({"error": "Invalid signature"}), 401

    # Parse event
    event = request.json
    event_type = event.get("event_type")

    print(f"Received webhook: {event_type}")

    # Handle different event types
    if event_type == "sales_order.created":
        handle_sales_order_created(event)
    elif event_type == "inventory.low_stock":
        handle_low_stock_alert(event)
    elif event_type == "manufacturing_order.completed":
        handle_mo_completed(event)

    return jsonify({"status": "received"}), 200


def handle_sales_order_created(event: dict[str, Any]) -> None:
    """Process new sales order event."""
    order_id = event["data"]["id"]

    # Fetch full order details from API
    import asyncio

    async def process_order():
        async with KatanaClient() as client:
            response = await get_sales_order.asyncio_detailed(
                client=client,
                id=order_id
            )

            if response.parsed:
                order = response.parsed
                print(f"Processing new order: {order.id}")

                # Add your business logic here:
                # - Send order confirmation email
                # - Create manufacturing orders
                # - Update external systems

    asyncio.run(process_order())


def handle_low_stock_alert(event: dict[str, Any]) -> None:
    """Handle low stock alert."""
    variant_id = event["data"]["variant_id"]
    current_stock = event["data"]["in_stock"]

    print(f"Low stock alert for variant {variant_id}: {current_stock} units")

    # Add your logic:
    # - Send alert to purchasing team
    # - Automatically create purchase order
    # - Update safety stock levels


def handle_mo_completed(event: dict[str, Any]) -> None:
    """Handle completed manufacturing order."""
    mo_id = event["data"]["id"]

    print(f"Manufacturing order {mo_id} completed")

    # Add your logic:
    # - Update production tracking system
    # - Trigger quality inspection workflow
    # - Send completion notification


if __name__ == "__main__":
    app.run(port=8080, debug=True)
```

### Scheduled Sync Task

Periodically sync data between Katana and external systems.

```python
import asyncio
from datetime import datetime, timedelta
from typing import Any

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.sales_order import get_all_sales_orders
from katana_public_api_client.utils import unwrap_data


async def sync_recent_orders_to_external_system(hours_back: int = 24) -> dict[str, int]:
    """
    Sync recent orders to external CRM/ERP system.

    Args:
        hours_back: How many hours back to sync

    Returns:
        Dict with sync statistics
    """
    cutoff_time = datetime.now() - timedelta(hours=hours_back)
    stats = {"synced": 0, "failed": 0, "skipped": 0}

    async with KatanaClient() as client:
        # Get recent orders
        response = await get_all_sales_orders.asyncio_detailed(
            client=client,
            created_after=cutoff_time.isoformat()
        )

        orders = unwrap_data(response)

        for order in orders:
            try:
                # Check if already synced
                if hasattr(order, 'custom_fields'):
                    synced = any(
                        cf.get('name') == 'external_sync' and cf.get('value') == 'true'
                        for cf in (order.custom_fields or [])
                    )
                    if synced:
                        stats["skipped"] += 1
                        continue

                # Sync to external system
                await push_to_external_system({
                    "order_id": order.id,
                    "customer": order.customer_name if hasattr(order, 'customer_name') else None,
                    "total": order.total if hasattr(order, 'total') else 0,
                    "status": order.status,
                })

                # Mark as synced (you'd use update_sales_order API here)
                stats["synced"] += 1
                print(f"✓ Synced order {order.id}")

            except Exception as e:
                stats["failed"] += 1
                print(f"✗ Failed to sync order {order.id}: {e}")

    return stats


async def push_to_external_system(order_data: dict[str, Any]) -> None:
    """Push order to external system (implement your logic)."""
    # Simulate external API call
    await asyncio.sleep(0.1)
    print(f"  → Pushed order {order_data['order_id']} to external system")


async def run_scheduled_sync():
    """Run periodic sync (call this from cron/scheduler)."""
    print(f"Starting scheduled sync at {datetime.now()}")

    stats = await sync_recent_orders_to_external_system(hours_back=24)

    print(f"Sync complete: {stats['synced']} synced, {stats['skipped']} skipped, {stats['failed']} failed")


# Usage with scheduler (e.g., APScheduler)
if __name__ == "__main__":
    # Run once
    asyncio.run(run_scheduled_sync())

    # Or use with APScheduler:
    # from apscheduler.schedulers.asyncio import AsyncIOScheduler
    #
    # scheduler = AsyncIOScheduler()
    # scheduler.add_job(run_scheduled_sync, 'interval', hours=1)
    # scheduler.start()
    #
    # asyncio.get_event_loop().run_forever()
```

## Observability

### Structured Logging Setup

Configure comprehensive logging for production use.

```python
import asyncio
import logging
import sys
from typing import Any

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products
from katana_public_api_client.utils import unwrap_data


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Setup structured logging for production.

    Args:
        level: Logging level (logging.INFO, logging.DEBUG, etc.)

    Returns:
        Configured logger instance
    """
    # Create custom logger
    logger = logging.getLogger("katana_integration")
    logger.setLevel(level)

    # Console handler with detailed format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Structured format
    formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
        '"module": "%(name)s", "message": "%(message)s"}'
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    # Also configure httpx logging for request details
    httpx_logger = logging.getLogger("httpx")
    httpx_logger.setLevel(logging.WARNING)  # Reduce noise

    return logger


async def fetch_products_with_logging() -> list[Any]:
    """Fetch products with comprehensive logging."""
    logger = setup_logging(level=logging.INFO)

    logger.info("Starting product fetch operation")

    try:
        async with KatanaClient(logger=logger) as client:
            logger.debug("KatanaClient initialized")

            response = await get_all_products.asyncio_detailed(client=client)
            products = unwrap_data(response)

            logger.info(f"Successfully fetched {len(products)} products")

            # Log sample data (be careful with PII)
            if products:
                logger.debug(f"First product: {products[0].name}")

            return products

    except Exception as e:
        logger.error(f"Failed to fetch products: {e}", exc_info=True)
        raise


# Usage
if __name__ == "__main__":
    products = asyncio.run(fetch_products_with_logging())
    print(f"Retrieved {len(products)} products")
```

### Metrics and Performance Tracking

Track API performance metrics for monitoring.

```python
import asyncio
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Any

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.sales_order import get_all_sales_orders
from katana_public_api_client.utils import unwrap_data


class MetricsCollector:
    """Simple in-memory metrics collector."""

    def __init__(self):
        self.request_counts = defaultdict(int)
        self.request_durations = defaultdict(list)
        self.error_counts = defaultdict(int)

    def record_request(self, endpoint: str, duration: float, success: bool):
        """Record API request metrics."""
        self.request_counts[endpoint] += 1
        self.request_durations[endpoint].append(duration)

        if not success:
            self.error_counts[endpoint] += 1

    def get_stats(self) -> dict[str, Any]:
        """Get aggregated statistics."""
        stats = {}

        for endpoint, durations in self.request_durations.items():
            count = len(durations)
            avg_duration = sum(durations) / count if count > 0 else 0
            max_duration = max(durations) if count > 0 else 0
            errors = self.error_counts[endpoint]

            stats[endpoint] = {
                "total_requests": count,
                "avg_duration_ms": round(avg_duration * 1000, 2),
                "max_duration_ms": round(max_duration * 1000, 2),
                "errors": errors,
                "error_rate": round(errors / count * 100, 2) if count > 0 else 0,
            }

        return stats

    def print_stats(self):
        """Print formatted statistics."""
        print("\n" + "=" * 60)
        print("API Performance Metrics")
        print("=" * 60)

        for endpoint, stats in self.get_stats().items():
            print(f"\n{endpoint}:")
            print(f"  Total Requests: {stats['total_requests']}")
            print(f"  Avg Duration:   {stats['avg_duration_ms']}ms")
            print(f"  Max Duration:   {stats['max_duration_ms']}ms")
            print(f"  Errors:         {stats['errors']} ({stats['error_rate']}%)")


# Global metrics instance
metrics = MetricsCollector()


@asynccontextmanager
async def track_request(endpoint: str):
    """Context manager to track request timing."""
    start_time = time.time()
    success = False

    try:
        yield
        success = True
    finally:
        duration = time.time() - start_time
        metrics.record_request(endpoint, duration, success)


async def fetch_orders_with_metrics():
    """Fetch orders with performance tracking."""
    async with KatanaClient() as client:
        async with track_request("get_all_sales_orders"):
            response = await get_all_sales_orders.asyncio_detailed(client=client)
            orders = unwrap_data(response)

            print(f"Fetched {len(orders)} orders")
            return orders


# Usage
if __name__ == "__main__":
    # Make several requests
    for _ in range(3):
        asyncio.run(fetch_orders_with_metrics())

    # Print metrics summary
    metrics.print_stats()
```

### OpenTelemetry Integration

Integrate with OpenTelemetry for distributed tracing.

```python
import asyncio

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products
from katana_public_api_client.utils import unwrap_data


# Setup OpenTelemetry
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Export spans to console (use OTLP exporter in production)
span_processor = BatchSpanProcessor(ConsoleSpanExporter())
trace.get_tracer_provider().add_span_processor(span_processor)

# Instrument httpx (used by KatanaClient)
HTTPXClientInstrumentor().instrument()


async def fetch_products_with_tracing():
    """Fetch products with OpenTelemetry tracing."""
    with tracer.start_as_current_span("fetch_products") as span:
        span.set_attribute("operation", "product_sync")

        async with KatanaClient() as client:
            with tracer.start_as_current_span("api.get_all_products"):
                response = await get_all_products.asyncio_detailed(client=client)
                products = unwrap_data(response)

                span.set_attribute("product.count", len(products))

                print(f"Fetched {len(products)} products")
                return products


# Usage
if __name__ == "__main__":
    products = asyncio.run(fetch_products_with_tracing())

    # In production, traces would be sent to your observability backend
    # (Jaeger, Zipkin, Honeycomb, etc.)
```

## Performance Optimization

### Efficient Pagination

Handle large datasets efficiently with pagination control.

```python
import asyncio
from typing import Any

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.sales_order import get_all_sales_orders
from katana_public_api_client.utils import unwrap_data


async def fetch_all_orders_efficiently(
    page_size: int = 100,
    max_pages: int | None = None
) -> list[Any]:
    """
    Fetch all orders with efficient pagination.

    The KatanaClient automatically handles pagination, but you can
    control the page size and limits for better performance.

    Args:
        page_size: Number of items per page (default 100, max 100)
        max_pages: Maximum pages to fetch (None = unlimited)

    Returns:
        List of all orders
    """
    async with KatanaClient(max_pages=max_pages or 1000) as client:
        # Use limit parameter to control page size
        response = await get_all_sales_orders.asyncio_detailed(
            client=client,
            limit=page_size  # Fetch 100 items per page
        )

        orders = unwrap_data(response)

        print(f"Fetched {len(orders)} orders total")

        # Pagination info is available in response object
        if hasattr(response, 'pagination_info'):
            info = response.pagination_info
            print(f"Pages: {info.get('page', 'N/A')}/{info.get('total_pages', 'N/A')}")

        return orders


async def process_orders_in_batches(batch_size: int = 50):
    """
    Process large order lists in batches to avoid memory issues.

    Args:
        batch_size: Number of orders to process at once
    """
    async with KatanaClient() as client:
        # Fetch all orders
        response = await get_all_sales_orders.asyncio_detailed(
            client=client,
            limit=100
        )
        all_orders = unwrap_data(response)

        # Process in batches
        for i in range(0, len(all_orders), batch_size):
            batch = all_orders[i:i + batch_size]

            print(f"Processing batch {i // batch_size + 1}: {len(batch)} orders")

            # Process batch (e.g., update external system)
            for order in batch:
                # Your processing logic here
                pass

            # Optional: small delay between batches
            await asyncio.sleep(0.1)


# Usage
if __name__ == "__main__":
    # Fetch efficiently with pagination control
    orders = asyncio.run(fetch_all_orders_efficiently(page_size=100, max_pages=10))

    # Or process in batches
    asyncio.run(process_orders_in_batches(batch_size=50))
```

### Concurrent Requests

Make multiple API requests concurrently for better performance.

```python
import asyncio
from typing import Any

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_product
from katana_public_api_client.api.variant import get_variant


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
            elif hasattr(response, 'parsed') and response.parsed:
                products.append(response.parsed)

        print(f"Successfully fetched {len(products)}/{len(product_ids)} products")
        return products


async def fetch_variants_for_products(product_ids: list[int]) -> dict[int, list[Any]]:
    """
    Fetch all variants for multiple products concurrently.

    Args:
        product_ids: List of product IDs

    Returns:
        Dict mapping product_id to list of variants
    """
    from katana_public_api_client.api.variant import get_all_variants
    from katana_public_api_client.utils import unwrap_data

    async with KatanaClient() as client:
        # Fetch all variants (this is more efficient than per-product requests)
        response = await get_all_variants.asyncio_detailed(client=client)
        all_variants = unwrap_data(response)

        # Group by product_id
        variants_by_product = {pid: [] for pid in product_ids}

        for variant in all_variants:
            if hasattr(variant, 'product_id') and variant.product_id in product_ids:
                variants_by_product[variant.product_id].append(variant)

        return variants_by_product


async def parallel_data_enrichment(order_ids: list[int]):
    """
    Enrich multiple orders with related data using parallel requests.

    Args:
        order_ids: List of order IDs to enrich
    """
    from katana_public_api_client.api.sales_order import get_sales_order
    from katana_public_api_client.api.customer import get_all_customers

    async with KatanaClient() as client:
        # Fetch orders and customers concurrently
        order_tasks = [
            get_sales_order.asyncio_detailed(client=client, id=order_id)
            for order_id in order_ids
        ]

        # Fetch all customers once
        customers_task = get_all_customers.asyncio_detailed(client=client)

        # Wait for all to complete
        results = await asyncio.gather(*order_tasks, customers_task)

        orders = [r.parsed for r in results[:-1] if hasattr(r, 'parsed') and r.parsed]
        customers_response = results[-1]

        print(f"Fetched {len(orders)} orders with customer data")


# Usage
if __name__ == "__main__":
    # Fetch multiple products concurrently (much faster than sequential)
    product_ids = [1, 2, 3, 4, 5]
    products = asyncio.run(fetch_multiple_products_concurrent(product_ids))

    # Fetch variants efficiently
    variants_map = asyncio.run(fetch_variants_for_products(product_ids))
    for pid, variants in variants_map.items():
        print(f"Product {pid}: {len(variants)} variants")
```

### Caching Strategy

Implement caching to reduce API calls for frequently accessed data.

```python
import asyncio
from datetime import datetime, timedelta
from typing import Any, Optional
import json
from pathlib import Path

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products
from katana_public_api_client.utils import unwrap_data


class SimpleCache:
    """Simple file-based cache with TTL."""

    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def _cache_path(self, key: str) -> Path:
        """Get cache file path for key."""
        return self.cache_dir / f"{key}.json"

    def get(self, key: str, ttl_seconds: int = 3600) -> Optional[Any]:
        """
        Get cached value if not expired.

        Args:
            key: Cache key
            ttl_seconds: Time to live in seconds

        Returns:
            Cached value or None if expired/missing
        """
        cache_file = self._cache_path(key)

        if not cache_file.exists():
            return None

        # Check if expired
        cache_age = datetime.now().timestamp() - cache_file.stat().st_mtime
        if cache_age > ttl_seconds:
            cache_file.unlink()  # Delete expired cache
            return None

        return json.loads(cache_file.read_text())

    def set(self, key: str, value: Any):
        """Set cached value."""
        cache_file = self._cache_path(key)
        cache_file.write_text(json.dumps(value, default=str))


# Global cache instance
cache = SimpleCache()


async def get_products_cached(ttl_seconds: int = 3600) -> list[Any]:
    """
    Get products with caching.

    Args:
        ttl_seconds: Cache TTL in seconds (default 1 hour)

    Returns:
        List of products (from cache or API)
    """
    cache_key = "products_all"

    # Try cache first
    cached = cache.get(cache_key, ttl_seconds=ttl_seconds)
    if cached:
        print(f"✓ Using cached products ({len(cached)} items)")
        return cached

    # Fetch from API
    print("Fetching products from API...")
    async with KatanaClient() as client:
        response = await get_all_products.asyncio_detailed(client=client)
        products = unwrap_data(response)

        # Serialize for caching
        products_data = [
            {
                "id": p.id,
                "name": p.name,
                "sku": p.sku,
            }
            for p in products
        ]

        # Cache the results
        cache.set(cache_key, products_data)

        print(f"✓ Fetched and cached {len(products)} products")
        return products_data


async def get_product_by_sku_cached(sku: str, ttl_seconds: int = 3600) -> Optional[dict]:
    """
    Get product by SKU with caching.

    Args:
        sku: Product SKU
        ttl_seconds: Cache TTL in seconds

    Returns:
        Product data or None
    """
    # Get all products (cached)
    products = await get_products_cached(ttl_seconds=ttl_seconds)

    # Find by SKU
    for product in products:
        if product.get("sku") == sku:
            return product

    return None


# Usage
if __name__ == "__main__":
    # First call - fetches from API
    products1 = asyncio.run(get_products_cached(ttl_seconds=300))  # 5 min cache

    # Second call - uses cache (much faster)
    products2 = asyncio.run(get_products_cached(ttl_seconds=300))

    # Find specific product
    product = asyncio.run(get_product_by_sku_cached("WDG-001"))
    if product:
        print(f"Found product: {product['name']}")
```

## Testing Patterns

### Mocking API Responses

Test your integration code without making real API calls.

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products
from katana_public_api_client.models import Product


@pytest.mark.asyncio
async def test_product_fetch_with_mock():
    """Test product fetching with mocked API response."""

    # Create mock products
    mock_product = Product(
        id=123,
        name="Test Product",
        sku="TEST-001",
    )

    # Mock the API response
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.parsed = [mock_product]

    # Patch the API function
    with patch(
        'katana_public_api_client.api.product.get_all_products.asyncio_detailed',
        new=AsyncMock(return_value=mock_response)
    ):
        async with KatanaClient(api_key="test-key", base_url="https://test.api") as client:
            response = await get_all_products.asyncio_detailed(client=client)

            assert response.status_code == 200
            assert len(response.parsed) == 1
            assert response.parsed[0].sku == "TEST-001"


@pytest.mark.asyncio
async def test_error_handling_with_mock():
    """Test error handling with mocked error response."""

    # Mock an error response
    with patch(
        'katana_public_api_client.api.product.get_all_products.asyncio_detailed',
        new=AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))
    ):
        async with KatanaClient(api_key="test-key", base_url="https://test.api") as client:
            with pytest.raises(httpx.TimeoutException):
                await get_all_products.asyncio_detailed(client=client)


@pytest.mark.asyncio
async def test_rate_limit_handling():
    """Test that rate limits are handled correctly."""

    # Mock a 429 response followed by success
    mock_429 = MagicMock(spec=httpx.Response)
    mock_429.status_code = 429
    mock_429.headers = {"Retry-After": "1"}

    mock_200 = MagicMock(spec=httpx.Response)
    mock_200.status_code = 200
    mock_200.parsed = []

    with patch(
        'katana_public_api_client.api.product.get_all_products.asyncio_detailed',
        new=AsyncMock(side_effect=[mock_429, mock_200])
    ):
        async with KatanaClient(api_key="test-key", base_url="https://test.api") as client:
            # Client should automatically retry after 429
            response = await get_all_products.asyncio_detailed(client=client)
            assert response.status_code == 200
```

### Integration Test Setup

Set up integration tests with real API (for CI/CD).

```python
import asyncio
import os
import pytest

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products
from katana_public_api_client.utils import unwrap_data


# Skip integration tests if no API key
pytestmark = pytest.mark.skipif(
    not os.getenv("KATANA_API_KEY"),
    reason="KATANA_API_KEY not set"
)


@pytest.fixture
async def katana_client():
    """Fixture providing KatanaClient for integration tests."""
    async with KatanaClient() as client:
        yield client


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_products_integration(katana_client):
    """Integration test for fetching products."""
    response = await get_all_products.asyncio_detailed(client=katana_client)

    # Check response structure
    assert response.status_code == 200

    products = unwrap_data(response)
    assert isinstance(products, list)

    # Validate data structure if products exist
    if products:
        product = products[0]
        assert hasattr(product, 'id')
        assert hasattr(product, 'name')


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pagination_integration(katana_client):
    """Integration test for pagination behavior."""
    # Fetch with small page size
    response = await get_all_products.asyncio_detailed(
        client=katana_client,
        limit=10  # Small page size
    )

    products = unwrap_data(response)

    # If there are more than 10 products, pagination should work
    # The client automatically fetches all pages
    assert isinstance(products, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_retry_on_network_error(katana_client):
    """Test that network errors are retried."""
    # This test would need a way to simulate network errors
    # For real integration tests, you might use network fault injection
    pass


# Run integration tests with:
# pytest -m integration tests/
```

### Testing Best Practices

```python
import asyncio
import pytest
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from katana_public_api_client import KatanaClient


class TestHelpers:
    """Helper utilities for testing Katana integrations."""

    @staticmethod
    def create_mock_client() -> KatanaClient:
        """Create a mock KatanaClient for testing."""
        return KatanaClient(
            api_key="test-api-key",
            base_url="https://test.api.katanamrp.com/v1"
        )

    @staticmethod
    def create_mock_response(status_code: int, data: Any = None) -> MagicMock:
        """
        Create a mock API response.

        Args:
            status_code: HTTP status code
            data: Response data

        Returns:
            Mock response object
        """
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.parsed = data
        return mock_response

    @staticmethod
    async def assert_async_raises(exception_class, coroutine):
        """Assert that async function raises specific exception."""
        with pytest.raises(exception_class):
            await coroutine


# Example usage in tests
@pytest.mark.asyncio
async def test_with_helpers():
    """Example test using helper utilities."""
    client = TestHelpers.create_mock_client()
    assert client._base_url == "https://test.api.katanamrp.com/v1"

    # Create mock response
    response = TestHelpers.create_mock_response(200, data=[])
    assert response.status_code == 200
```

## Need Help?

- Check the [API Documentation](https://help.katanamrp.com/api)
- Review [KATANA_CLIENT_GUIDE.md](KATANA_CLIENT_GUIDE.md) for client features
- See
  [examples directory](https://github.com/dougborg/katana-openapi-client/tree/main/examples)
  for runnable code samples
- Open an issue on GitHub for questions or feedback

______________________________________________________________________

**Last Updated:** 2025-01-21
