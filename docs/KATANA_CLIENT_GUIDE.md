# KatanaClient Guide

The **KatanaClient** is the modern, pythonic client for the Katana Manufacturing ERP
API. It provides automatic resilience (retries, rate limiting, error handling) using
httpx's native transport layer - no decorators or wrapper methods needed.

## 🎯 Key Features

- **🛡️ Automatic Resilience**: Transport-layer retries and rate limiting
- **🚀 Zero Configuration**: Works out of the box with environment variables
- **📦 Complete Type Safety**: Full type hints and IDE support
- **🔄 Smart Pagination**: Built-in pagination with safety limits
- **🔍 Rich Observability**: Structured logging and metrics
- **⚡ Pythonic Design**: Uses httpx's native extension points

## 🚀 Quick Start

### Installation & Setup

```bash
# Install the client
pip install -e .

# Create .env file with credentials
echo "KATANA_API_KEY=your-api-key-here" > .env
echo "KATANA_BASE_URL=https://api.katanamrp.com/v1" >> .env
```

### Basic Usage

```python
import asyncio

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products

async def main():
    # Automatic configuration from .env file
    async with KatanaClient() as client:
        # Direct API usage - automatic resilience built-in
        response = await get_all_products.asyncio_detailed(
            client=client,
            limit=50
        )

        if response.status_code == 200:
            products = response.parsed.data
            print(f"Retrieved {len(products)} products")

asyncio.run(main())
```

## 🛡️ Automatic Resilience

Every API call through `KatanaClient` automatically includes:

### Smart Retries

- **Network Errors**: Automatic retry with exponential backoff (1s, 2s, 4s, 8s, 16s)
- **Rate Limits (429)**: ALL methods (including POST/PATCH) retry with `Retry-After`
  header support
- **Server Errors (502/503/504)**: Only idempotent methods (GET, PUT, DELETE, etc.) are
  retried
- **Client Errors (4xx except 429)**: No retries

```python
async with KatanaClient(max_retries=5) as client:
    # This call will automatically retry on failures
    # POST/PATCH requests will retry on 429 but not on 5xx errors
    # GET/PUT/DELETE requests will retry on both 429 and 5xx errors
    response = await get_all_products.asyncio_detailed(
        client=client,
        limit=100
    )
    # No decorators or wrapper methods needed!
```

### Rate Limit Handling

```python
# Automatic rate limit handling with Retry-After header support
async with KatanaClient() as client:
    # These calls will automatically be rate limited
    for i in range(100):
        response = await get_all_products.asyncio_detailed(
            client=client,
            page=i,
            limit=50
        )
        # Client automatically waits when rate limited
```

### Error Recovery

```python
import logging

# Configure logging to see resilience in action
logging.basicConfig(level=logging.INFO)

async with KatanaClient() as client:
    # Automatic error recovery with detailed logging
    response = await get_all_products.asyncio_detailed(
        client=client,
        limit=100
    )
    # Logs will show retry attempts and recovery
```

## 🔄 Smart Pagination

All pagination is now handled automatically and transparently:

### Automatic Pagination Usage

```python
async with KatanaClient() as client:
    # Get ALL products across all pages automatically
    all_products = await get_all_products.asyncio_detailed(
        client=client,
        is_sellable=True  # API filter parameters
    )
    print(f"Total products: {len(all_products.parsed.data)}")
```

### Automatic Pagination Features

```python
async with KatanaClient() as client:
    # Built-in safety limits and automatic pagination
    products = await get_all_products.asyncio_detailed(
        client=client,
        limit=250  # Optimize page size - automatically paginated
    )
    # All pages are automatically collected into a single response
```

## ⚙️ Configuration

### Environment Variables

```bash
# Required
KATANA_API_KEY=your-api-key-here

# Optional (defaults shown)
KATANA_BASE_URL=https://api.katanamrp.com/v1
```

### Custom Configuration

```python
import logging

# Custom configuration
async with KatanaClient(
    api_key="custom-key",
    base_url="https://custom.katana.com/v1",
    timeout=60.0,           # Request timeout
    max_retries=5,          # Maximum retry attempts
    logger=logging.getLogger("custom")  # Custom logger
) as client:
    # Your API calls here
    pass
```

### Advanced httpx Configuration

```python
import httpx

# Pass through httpx configuration
async with KatanaClient(
    # Standard KatanaClient options
    api_key="your-key",
    max_retries=3,

    # httpx client options
    verify=False,           # SSL verification
    proxies="http://proxy:8080",
    headers={"Custom": "Header"},
    event_hooks={
        "request": [custom_request_hook],
        "response": [custom_response_hook]
    }
) as client:
    # Client has both resilience AND custom httpx config
    pass
```

## 🔍 Observability

### Logging

```python
import logging

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async with KatanaClient() as client:
    # All resilience actions are logged
    response = await get_all_products.asyncio_detailed(
        client=client,
        limit=100
    )
```

Example log output:

```text
2025-01-15 10:30:15 - katana_client - WARNING - Rate limited on attempt 1, waiting 60.0s
2025-01-15 10:31:16 - katana_client - INFO - Request succeeded after 2 attempts
2025-01-15 10:31:16 - katana_client - DEBUG - Response: 200 GET https://api.katanamrp.com/v1/products (1.24s)
```

### Custom Event Hooks

```python
async def custom_response_hook(response):
    """Custom hook to track API usage."""
    print(f"API call: {response.request.method} {response.request.url}")
    print(f"Status: {response.status_code}")

async with KatanaClient(
    event_hooks={
        "response": [custom_response_hook]
    }
) as client:
    # Your custom hooks are called alongside built-in ones
    response = await get_all_products.asyncio_detailed(
        client=client,
        limit=10
    )
```

## 🧪 Testing

### Mocking for Tests

```python
import pytest
from unittest.mock import AsyncMock, patch
from katana_public_api_client import KatanaClient

@pytest.mark.asyncio
async def test_api_integration():
    """Test API integration with mocked responses."""
    with patch.dict('os.environ', {'KATANA_API_KEY': 'test-key'}):
        async with KatanaClient() as client:
            # Mock the underlying httpx client
            with patch.object(client, 'get_async_httpx_client') as mock_httpx:
                mock_response = AsyncMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"data": [{"id": 1}]}

                mock_httpx.return_value.request = AsyncMock(return_value=mock_response)

                # Test your API logic here
                from katana_public_api_client.api.product import get_all_products
                response = await get_all_products.asyncio_detailed(
                    client=client,
                    limit=10
                )

                assert response.status_code == 200
```

### Integration Tests

```python
import os

import pytest

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products

@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_api():
    """Test against real Katana API (requires KATANA_API_KEY)."""
    api_key = os.getenv('KATANA_API_KEY')
    if not api_key:
        pytest.skip("KATANA_API_KEY not set")

    async with KatanaClient() as client:
        response = await get_all_products.asyncio_detailed(
            client=client,
            limit=1
        )

        assert response.status_code == 200
        assert hasattr(response.parsed, 'data')
```

## 🔧 Advanced Patterns

### Custom Transport

```python
from katana_public_api_client.katana_client import ResilientAsyncTransport

# Create custom transport with different settings
custom_transport = ResilientAsyncTransport(
    max_retries=10,
    max_pages=50,  # Limit automatic pagination
    logger=custom_logger
)

async with KatanaClient(
    transport=custom_transport
) as client:
    # Uses your custom retry logic
    pass
```

### Batch Operations

```python
import asyncio
from katana_public_api_client.api.product import get_product

async def process_products_in_batches(product_ids, batch_size=10):
    """Process products in batches with automatic resilience."""
    async with KatanaClient() as client:
        results = []
        for i in range(0, len(product_ids), batch_size):
            batch = product_ids[i:i + batch_size]

            # Each call automatically has resilience
            batch_results = await asyncio.gather(*[
                get_product.asyncio_detailed(client=client, id=product_id)
                for product_id in batch
            ])

            results.extend(batch_results)

            # Be nice to the API
            await asyncio.sleep(0.1)

        return results
```

### Error Handling

```python
import httpx
from katana_public_api_client.errors import UnexpectedStatus

async with KatanaClient() as client:
    try:
        response = await get_all_products.asyncio_detailed(
            client=client,
            limit=50
        )

        if response.status_code == 200:
            products = response.parsed.data
            print(f"Success: {len(products)} products")
        else:
            print(f"API returned: {response.status_code}")

    except httpx.TimeoutException:
        print("Request timed out after retries")
    except httpx.ConnectError:
        print("Connection failed after retries")
    except UnexpectedStatus as e:
        print(f"Unexpected API response: {e.status_code}")
```

## 📚 Best Practices

### 1. Use Context Managers

```python
# ✅ Good: Properly manages connections
async with KatanaClient() as client:
    response = await get_all_products.asyncio_detailed(
        client=client,
        limit=50
    )

# ❌ Bad: Doesn't close connections
client = KatanaClient()
response = await get_all_products.asyncio_detailed(
    client=client,
    limit=50
)
```

### 2. Configure Appropriate Timeouts

```python
# ✅ Good: Reasonable timeout for your use case
async with KatanaClient(timeout=30.0) as client:
    # Timeout is appropriate for expected response time
    pass

# ❌ Bad: Too short timeout causes unnecessary retries
async with KatanaClient(timeout=1.0) as client:
    # Will likely timeout and retry frequently
    pass
```

### 3. Use Automatic Pagination for Large Datasets

```python
# ✅ Good: Automatic pagination for large datasets
all_products = await get_all_products.asyncio_detailed(
    client=client,
    # Automatically handles all pages with built-in safety limits
)

# ❌ Bad: Manual pagination without safety limits
page = 1
while True:  # Could run forever!
    response = await get_all_products.asyncio_detailed(
        client=client,
        page=page,
        limit=100
    )
    # ... handle response
    page += 1
```

### 4. Handle Different Response Types

```python
async with KatanaClient() as client:
    response = await get_all_products.asyncio_detailed(
        client=client,
        limit=50
    )

    # ✅ Good: Check status before accessing data
    if response.status_code == 200:
        products = response.parsed.data
        print(f"Retrieved {len(products)} products")
    elif response.status_code == 401:
        print("Authentication failed")
    else:
        print(f"Unexpected status: {response.status_code}")
```

### 5. Use Direct API Calls

```python
from katana_public_api_client.api.product import get_all_products

# ✅ Good: Direct API calls with automatic resilience
async with KatanaClient() as client:
    response = await get_all_products.asyncio_detailed(
        client=client,
        is_sellable=True
    )
    if response.status_code == 200:
        products = response.parsed.data
```

## 🚀 Performance Tips

### 1. Reuse Client Instances

```python
from katana_public_api_client.api.product import get_all_products
from katana_public_api_client.api.sales_order import get_all_sales_orders
from katana_public_api_client.api.inventory import get_all_inventory_points

# ✅ Good: One client for multiple operations
async with KatanaClient() as client:
    products = await get_all_products.asyncio_detailed(client=client)
    orders = await get_all_sales_orders.asyncio_detailed(client=client)
    inventory = await get_all_inventory_points.asyncio_detailed(client=client)

# ❌ Bad: New client for each operation
for operation in [get_all_products, get_all_sales_orders]:
    async with KatanaClient() as client:
        await operation.asyncio_detailed(client=client)
```

### 2. Optimize Page Sizes

```python
# ✅ Good: Reasonable page size
products = await get_all_products.asyncio_detailed(
    client=client,
    limit=250  # Good balance of efficiency and memory - automatically paginated
)

# ❌ Bad: Too small (many requests)
products = await get_all_products.asyncio_detailed(
    client=client,
    limit=10   # Will make many small requests
)

# ❌ Bad: Too large (may hit API limits)
products = await get_all_products.asyncio_detailed(
    client=client,
    limit=10000  # May exceed API limits
)
```

### 3. Use Concurrent Requests Wisely

```python
import asyncio
from katana_public_api_client.api.product import get_product

# ✅ Good: Limited concurrency respects rate limits
async def get_multiple_products(product_ids):
    async with KatanaClient() as client:
        # Process in small batches
        results = []
        for i in range(0, len(product_ids), 5):  # 5 concurrent requests
            batch = product_ids[i:i+5]
            batch_results = await asyncio.gather(*[
                get_product.asyncio_detailed(client=client, id=pid)
                for pid in batch
            ])
            results.extend(batch_results)

            # Small delay between batches
            if i + 5 < len(product_ids):
                await asyncio.sleep(0.2)

        return results
```

## 📖 API Reference

### KatanaClient

```python
class KatanaClient(AuthenticatedClient):
    """The pythonic Katana API client with automatic resilience and pagination."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 5,
        max_pages: int = 100,
        logger: Optional[logging.Logger] = None,
        **httpx_kwargs: Any,
    ): ...

    async def __aenter__(self) -> "KatanaClient": ...
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...
```

### ResilientAsyncTransport

Factory function that creates a layered transport with automatic resilience:

```python
def ResilientAsyncTransport(
    max_retries: int = 5,
    max_pages: int = 100,
    logger: Optional[logging.Logger] = None,
    **kwargs: Any
) -> RetryTransport:
    """
    Creates a chained transport with:
    1. AsyncHTTPTransport (base HTTP transport)
    2. ErrorLoggingTransport (logs detailed 4xx errors)
    3. PaginationTransport (auto-collects paginated responses)
    4. RetryTransport (handles retries with Retry-After header support)
    """
    ...
```

______________________________________________________________________

**Next Steps**: Check out the
[API Reference](reference/katana_public_api_client/index.md) for detailed endpoint
documentation, or see [Testing Guide](TESTING_GUIDE.md) for testing patterns.
