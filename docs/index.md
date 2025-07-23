# Katana OpenAPI Client Documentation

Welcome to the **Katana OpenAPI Client** documentation. This is a modern, pythonic
client for the Katana Manufacturing ERP API with automatic resilience features.

## Features

- **Transport-layer resilience**: Automatic retries, rate limiting, and smart pagination
  at the HTTP transport level
- **Type-safe**: Full type hints and mypy compatibility
- **Async/await support**: Built on httpx for modern Python async patterns
- **Production-ready**: Comprehensive error handling and logging
- **Zero-wrapper philosophy**: All resilience features work transparently with the
  generated API client

## Quick Start

```python
from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products

async def main():
    async with KatanaClient() as client:
        # This call automatically gets retries, rate limiting, and pagination
        response = await get_all_products.asyncio_detailed(
            client=client,
            limit=50  # Will auto-paginate if needed
        )

        if response.status_code == 200:
            products = response.parsed
            print(f"Found {len(products)} products")
```

## Architecture

The client uses a **transport-layer resilience** approach where all resilience features
(retries, rate limiting, pagination) are implemented at the HTTP transport level rather
than as decorators or wrapper methods. This means:

- All 150+ generated API methods automatically get resilience features
- No code changes needed when the OpenAPI spec is updated
- Type safety is preserved throughout the entire client
- Performance is optimized by handling resilience at the lowest level

## Documentation Structure

```{toctree}
:maxdepth: 2
:caption: User Guides

KATANA_CLIENT_GUIDE
TESTING_GUIDE
CONTRIBUTING
```

```{toctree}
:maxdepth: 2
:caption: API Reference

autoapi/katana_public_api_client/index
```

```{toctree}
:maxdepth: 2
:caption: Development

RELEASE_WORKFLOW
SEMANTIC_RELEASE_GUIDE
POETRY_USAGE
```

```{toctree}
:maxdepth: 2
:caption: Project Information

CHANGELOG
CODE_OF_CONDUCT
```

## API Reference

The API reference documentation is automatically generated from the source code
docstrings and includes:

- **Main Client Classes**: `KatanaClient`, `ResilientAsyncTransport`
- **Logging Utilities**: `setup_logging`, `get_logger`
- **Generated API Methods**: 150+ endpoint methods with full type annotations
- **Data Models**: All request/response models with validation

## Installation

```bash
pip install katana-openapi-client
```

## Configuration

The client can be configured through environment variables or direct initialization:

```python
# Via environment variables (.env file)
KATANA_API_KEY=your_api_key_here
KATANA_BASE_URL=https://api.katanamrp.com  # Optional, defaults to production

# Via direct initialization
from katana_public_api_client import KatanaClient

async with KatanaClient(
    api_key="your_api_key_here",
    base_url="https://api.katanamrp.com",
    max_retries=5,
    max_pages=100
) as client:
    # Use the client
    pass
```

## Support

- **Documentation**: [GitHub Pages](https://dougborg.github.io/katana-openapi-client/)
- **Issues**: [GitHub Issues](https://github.com/dougborg/katana-openapi-client/issues)
- **Source**: [GitHub Repository](https://github.com/dougborg/katana-openapi-client)

## License

MIT License - see
[LICENSE](https://github.com/dougborg/katana-openapi-client/blob/main/LICENSE) for
details.
