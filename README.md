# Katana Manufacturing ERP - Python API Client

A modern, pythonic Python client for the
[Katana Manufacturing ERP API](https://help.katanamrp.com/api). Built from a
comprehensive OpenAPI 3.1.0 specification with 100% endpoint coverage and automatic
resilience.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/dependency--management-uv-blue.svg)](https://docs.astral.sh/uv/)
[![OpenAPI 3.1.0](https://img.shields.io/badge/OpenAPI-3.1.0-green.svg)](https://spec.openapis.org/oas/v3.1.0)

## ✨ Features

- **🎯 Production Ready**: Automatic retries, rate limiting, and error handling
- **🚀 Zero Configuration**: Works out of the box with environment variables
- **📦 Complete API Coverage**: All 76+ Katana API endpoints with full type hints
- **🔄 Smart Pagination**: Automatic pagination with built-in safety limits
- **🛡️ Transport-Layer Resilience**: httpx-native approach, no decorators needed
- **⚡ Async/Sync Support**: Use with asyncio or traditional synchronous code
- **🔍 Rich Observability**: Built-in logging and metrics
- **🏗️ Streamlined Architecture**: Flattened imports, automated regeneration, zero
  patches

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/dougborg/katana-openapi-client.git
cd katana-openapi-client

# Install with uv (recommended)
uv sync --all-extras

# Or with pip
pip install -e .
```

### 📋 Configuration

Create a `.env` file with your Katana API credentials:

```bash
KATANA_API_KEY=your-api-key-here
# Optional: defaults to https://api.katanamrp.com/v1
KATANA_BASE_URL=https://api.katanamrp.com/v1
```

### Basic Usage

#### KatanaClient (Recommended)

The modern, pythonic client with automatic resilience:

```python
import asyncio

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products
from katana_public_api_client.api.sales_order import get_all_sales_orders

async def main():
    # Automatic configuration from .env file
    async with KatanaClient() as client:
        response = await get_all_products.asyncio_detailed(
            client=client,
            limit=50
        )
        print(f"Status: {response.status_code}")
        print(f"Products: {len(response.parsed.data)}")

        # Automatic pagination happens transparently
        all_products_response = await get_all_products.asyncio_detailed(
            client=client,
            is_sellable=True
        )
        print(f"Total sellable products: {len(all_products_response.parsed.data)}")

        # Direct API usage with automatic resilience
        orders_response = await get_all_sales_orders.asyncio_detailed(
            client=client,
            status="open"
        )
        orders = orders_response.parsed.data if orders_response.parsed else []
        print(f"Open orders: {len(orders)}")

asyncio.run(main())
```

## 📊 API Coverage

The client provides access to all major Katana functionality:

| Category                 | Endpoints | Description                                 |
| ------------------------ | --------- | ------------------------------------------- |
| **Products & Inventory** | 25+       | Products, variants, materials, stock levels |
| **Orders**               | 20+       | Sales orders, purchase orders, fulfillment  |
| **Manufacturing**        | 15+       | BOMs, manufacturing orders, operations      |
| **Business Relations**   | 10+       | Customers, suppliers, addresses             |
| **Configuration**        | 6+        | Locations, webhooks, custom fields          |

**Total**: 76+ endpoints with 150+ fully-typed data models.

## 🎯 Why KatanaClient?

### Automatic Resilience

Every API call through `KatanaClient` automatically includes:

- **Smart Retries**: Exponential backoff (1s, 2s, 4s, 8s, 16s) for network errors and
  server errors
- **Rate Limit Handling**: All HTTP methods (including POST/PATCH) are automatically
  retried on 429 errors with `Retry-After` header support
- **Idempotent Server Error Retry**: Only safe methods (GET, PUT, DELETE) are retried on
  502/503/504 errors
- **Error Recovery**: Intelligent retry logic that doesn't retry other 4xx client errors
- **Observability**: Rich logging for debugging and monitoring

### Pythonic Design

```python
# No decorators, no wrapper methods needed
async with KatanaClient() as client:
    # Just use the generated API methods directly
    response = await get_all_products.asyncio_detailed(
        client=client,
        limit=100
    )
    # Automatic retries, rate limiting, logging - all transparent!
```

### Transport-Layer Architecture

Uses httpx's native transport layer for resilience - the most pythonic approach:

- **Zero Dependencies**: Built on httpx's standard extension points
- **Maximum Compatibility**: Works with any httpx-based code
- **Easy Testing**: Simple to mock and test
- **Performance**: Minimal overhead compared to decorators

## 🔧 Advanced Usage

### Custom Configuration

```python
import logging

from katana_public_api_client import KatanaClient

# Custom configuration
async with KatanaClient(
    api_key="custom-key",
    base_url="https://custom.katana.com/v1",
    timeout=60.0,
    max_retries=3,
    logger=logging.getLogger("katana")
) as client:
    # Your API calls here
    pass
```

### Automatic Pagination

```python
from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products

async with KatanaClient() as client:
    # Get all products with automatic pagination
    all_products_response = await get_all_products.asyncio_detailed(
        client=client,
        is_sellable=True
    )
    sellable_products = all_products_response.parsed.data
    print(f"Found {len(sellable_products)} sellable products")
```

### Response Unwrapping Utilities

Convenient helpers to unwrap responses and handle errors:

```python
from katana_public_api_client import (
    KatanaClient,
    unwrap,
    unwrap_data,
    APIError,
    AuthenticationError,
    ValidationError,
)
from katana_public_api_client.api.product import get_all_products

async with KatanaClient() as client:
    # unwrap() extracts parsed data and raises typed exceptions on errors
    response = await get_all_products.asyncio_detailed(client=client)
    product_list = unwrap(response)  # Raises APIError on failure

    # unwrap_data() directly extracts the .data field from list responses
    products = unwrap_data(response)  # Returns list of Product objects
    for product in products:
        print(f"Product: {product.name}")

    # Handle errors with typed exceptions
    try:
        response = await get_all_products.asyncio_detailed(client=client)
        products = unwrap(response)
    except AuthenticationError as e:
        print(f"Auth failed: {e}")
    except ValidationError as e:
        print(f"Validation error: {e.validation_errors}")
    except APIError as e:
        print(f"API error {e.status_code}: {e}")
```

See [examples/using_utils.py](examples/using_utils.py) for more examples.

## � Project Structure

```text
katana-openapi-client/
├── docs/katana-openapi.yaml     # OpenAPI 3.1.0 specification
├── katana_public_api_client/    # Generated Python client
│   ├── katana_client.py         # KatanaClient with transport-layer resilience
│   ├── client.py                # Base generated client classes
│   ├── api/                     # 76+ API endpoint modules
│   ├── models/                  # 150+ data models
│   └── types.py                 # Type definitions
├── docs/                        # Documentation
├── tests/                       # Test suite
└── scripts/                     # Development utilities
```

## 🧪 Testing

```bash
# Run all tests
uv run poe test

# Run with coverage
uv run poe test-coverage

# Run specific test categories
uv run poe test-unit           # Unit tests only
uv run poe test-integration    # Integration tests only
```

## 📚 Documentation

### User Guides

- [**KatanaClient Guide**](docs/KATANA_CLIENT_GUIDE.md) - Complete KatanaClient usage
  guide
- [**API Reference**](docs/API_REFERENCE.md) - Generated API documentation
- [**Migration Guide**](docs/MIGRATION_GUIDE.md) - Upgrading from previous versions
- [**Testing Guide**](docs/TESTING_GUIDE.md) - Testing patterns and examples

### Architecture & Design

- [**Architecture Decision Records (ADRs)**](docs/adr/README.md) - Key architectural
  decisions
  - [ADR-001: Transport-Layer Resilience](docs/adr/0001-transport-layer-resilience.md)
  - [ADR-002: OpenAPI Code Generation](docs/adr/0002-openapi-code-generation.md)
  - [ADR-003: Transparent Pagination](docs/adr/0003-transparent-pagination.md)
  - [ADR-004: Defer Observability to httpx](docs/adr/0004-defer-observability-to-httpx.md)
  - [ADR-005: Sync and Async APIs](docs/adr/0005-sync-async-apis.md)
  - [ADR-006: Response Unwrapping Utilities](docs/adr/0006-response-unwrapping-utilities.md)
  - [ADR-007: Domain Helper Classes](docs/adr/0007-domain-helper-classes.md)
    (**PROPOSED**)
  - [ADR-008: Avoid Builder Pattern](docs/adr/0008-avoid-builder-pattern.md)
    (**PROPOSED**)

### Project Analysis

- [**Revised Assessment**](docs/REVISED_ASSESSMENT.md) - Comprehensive review (Grade: A,
  95/100)
- [**Coverage Analysis**](docs/COVERAGE_ANALYSIS.md) - Test coverage breakdown (74.8%
  core logic)
- [**Builder Pattern Analysis**](docs/BUILDER_PATTERN_ANALYSIS.md) - Builder vs domain
  helpers
- [**Domain Helpers Design**](docs/DOMAIN_HELPERS_DESIGN.md) - Complete helper design

## 🔄 Development Workflow

### Development Setup

```bash
# Install dependencies
uv sync --all-extras

# Install pre-commit hooks (important!)
uv run poe pre-commit-install

# See all available tasks
uv run poe help

# Quick development check
uv run poe check

# Auto-fix common issues
uv run poe fix
```

### Code Quality Tasks

```bash
# Formatting
uv run poe format              # Format all code and documentation
uv run poe format-check        # Check formatting without changes
uv run poe format-python       # Format Python code only

# Linting and Type Checking
uv run poe lint                 # Run all linters (ruff, mypy, yaml)
uv run poe lint-ruff           # Fast linting with ruff
uv run poe lint-mypy           # Type checking with mypy

# Testing
uv run poe test                 # Run all tests
uv run poe test-coverage       # Run tests with coverage
uv run poe test-unit           # Unit tests only
uv run poe test-integration    # Integration tests only
```

### OpenAPI and Client Generation

```bash
# Regenerate client from OpenAPI spec
uv run poe regenerate-client

# Validate OpenAPI specification
uv run poe validate-openapi

# Full preparation workflow
uv run poe prepare             # Format + lint + test + validate
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks (run once after clone)
uv run poe pre-commit-install

# Run pre-commit on all files manually
uv run poe pre-commit-run

# Update pre-commit hook versions
uv run poe pre-commit-update
```

### CI/Development Workflows

```bash
# Full CI pipeline (what runs in GitHub Actions)
uv run poe ci

# Pre-commit preparation
uv run poe prepare

# Clean build artifacts
uv run poe clean
```

## Configuration

All tool configurations are consolidated in `pyproject.toml` following modern Python
packaging standards:

- **uv**: Fast, modern package and dependency manager
- **Hatchling**: Build backend for package distribution
- **Ruff**: Code formatting and linting (replaces Black, isort, flake8)
- **MyPy**: Type checking configuration
- **Pytest**: Test discovery and execution settings
- **Coverage**: Code coverage reporting
- **Poe**: Task automation and scripts
- **Semantic Release**: Automated versioning and releases

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for
details.

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for
details on our code of conduct and the process for submitting pull requests.
