# Katana OpenAPI Client Examples

This directory contains various examples demonstrating different features and usage
patterns of the KatanaClient.

## Prerequisites

Before running any examples, make sure you have:

1. **Installed the client**:

   ```bash
   poetry install
   ```

1. **Set up your API key**:

   - Create a `.env` file in the project root (or set environment variable):

     ```env
     KATANA_API_KEY=your_api_key_here
     ```

   - Or export it in your shell:

     ```bash
     export KATANA_API_KEY="your_api_key_here"
     ```

## Available Examples

### Basic Usage (`basic_usage.py`)

Demonstrates the core features of KatanaClient including:

- Automatic pagination
- Single page requests
- Limited pagination
- Automatic resilience and retry logic

**Run:**

```bash
poetry run python examples/basic_usage.py
```

**Key Features Shown:**

- Auto-pagination happens automatically for GET requests with `limit` parameter
- Disable auto-pagination by adding explicit `page` parameter
- Configure maximum pages to collect with `max_pages`
- All requests get automatic retries and error handling

## Error Handling

All examples include proper error handling patterns. The client automatically:

- **Retries** network errors and 5xx server errors with exponential backoff
- **Handles rate limiting** with Retry-After header support
- **Logs detailed error information** for 4xx client errors
- **Provides structured error parsing** for validation errors (422 responses)

## Configuration Options

The `KatanaClient` supports various configuration options:

```python
client = KatanaClient(
    api_key="your_key",           # Or set KATANA_API_KEY env var
    base_url="https://...",       # Custom base URL
    timeout=30.0,                 # Request timeout in seconds
    max_retries=5,                # Maximum retry attempts
    max_pages=100,                # Maximum pages for auto-pagination
    logger=custom_logger,         # Custom logger instance
)
```

## Transport Layer Features

The client uses a custom `ResilientAsyncTransport` that provides:

- **Automatic retries** with exponential backoff
- **Rate limiting** detection and handling
- **Smart pagination** based on request parameters
- **Request/response logging** and metrics

## API Usage Pattern

The client inherits from `AuthenticatedClient` and can be passed directly to generated
API methods:

```python
from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products

async with KatanaClient() as client:
    # Pass client directly - no .client property needed
    response = await get_all_products.asyncio_detailed(
        client=client,
        limit=50  # Automatically paginates if more data available
    )
```

## Additional Resources

- [Main Documentation](../docs/KATANA_CLIENT_GUIDE.md)
- [Testing Guide](../docs/TESTING_GUIDE.md)
- [Poetry Usage](../docs/POETRY_USAGE.md)

## Contributing Examples

When adding new examples:

1. Create a new Python file in this directory
1. Include a comprehensive docstring explaining the example
1. Add proper error handling
1. Update this README with the new example
1. Test the example works with a real API key
