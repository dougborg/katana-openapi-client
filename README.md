# Katana Manufacturing ERP - Python API Client

A modern, pythonic Python client for the
[Katana Manufacturing ERP API](https://help.katanamrp.com/api). Built from a
comprehensive OpenAPI 3.1.0 specification with 100% endpoint coverage and automatic
resilience.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/badge/dependency--management-poetry-blue.svg)](https://python-poetry.org/)
[![OpenAPI 3.1.0](https://img.shields.io/badge/OpenAPI-3.1.0-green.svg)](https://spec.openapis.org/oas/v3.1.0)

## ✨ Features

- **🎯 Production Ready**: Automatic retries, rate limiting, and error handling
- **🚀 Zero Configuration**: Works out of the box with environment variables
- **📦 Complete API Coverage**: All 76+ Katana API endpoints with full type hints
- **🔄 Smart Pagination**: Automatic pagination with built-in safety limits
- **🛡️ Transport-Layer Resilience**: httpx-native approach, no decorators needed
- **⚡ Async/Sync Support**: Use with asyncio or traditional synchronous code
- **🔍 Rich Observability**: Built-in logging and metrics

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/dougborg/katana-openapi-client.git
cd katana-openapi-client

# Install with Poetry (recommended)
poetry install

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
from katana_public_api_client.generated.api.product import get_all_products
from katana_public_api_client.generated.api.sales_order import get_all_sales_orders

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

#### Generated Client (Direct)

For maximum control and custom resilience patterns:

```python
import asyncio

from katana_public_api_client import AuthenticatedClient
from katana_public_api_client.generated.api.product import get_all_products

async def main():
    client = AuthenticatedClient(
        base_url="https://api.katanamrp.com/v1",
        token="your-api-key"
    )

    async with client:
        response = await get_all_products.asyncio_detailed(
            client=client,
            limit=50
        )
        if response.status_code == 200:
            products = response.parsed.data
            print(f"Found {len(products)} products")

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

- **Smart Retries**: Exponential backoff for network errors and 5xx responses
- **Rate Limit Handling**: Automatic retry with `Retry-After` header support
- **Error Recovery**: Intelligent retry logic that doesn't retry 4xx client errors
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
from katana_public_api_client.generated.api.product import get_all_products

async with KatanaClient() as client:
    # Get all products with automatic pagination
    all_products_response = await get_all_products.asyncio_detailed(
        client=client,
        is_sellable=True
    )
    sellable_products = all_products_response.parsed.data
    print(f"Found {len(sellable_products)} sellable products")
```

### Direct API Usage

```python
from katana_public_api_client import KatanaClient
from katana_public_api_client.generated.api.inventory import get_all_inventory_points
from katana_public_api_client.generated.api.manufacturing_order import get_all_manufacturing_orders
from katana_public_api_client.generated.api.product import get_all_products, get_product
from katana_public_api_client.generated.api.sales_order import get_all_sales_orders, get_sales_order

async with KatanaClient() as client:
    # Direct API methods with automatic pagination and resilience
    products = await get_all_products.asyncio_detailed(
        client=client, is_sellable=True
    )
    orders = await get_all_sales_orders.asyncio_detailed(
        client=client, status="open"
    )
    inventory = await get_all_inventory_points.asyncio_detailed(
        client=client
    )
    manufacturing = await get_all_manufacturing_orders.asyncio_detailed(
        client=client, status="planned"
    )

    # Individual item lookup
    product = await get_product.asyncio_detailed(
        client=client, id=123
    )
    order = await get_sales_order.asyncio_detailed(
        client=client, id=456
    )
```

## � Project Structure

```text
katana-openapi-client/
├── katana-openapi.yaml          # OpenAPI 3.1.0 specification
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
poetry run poe test

# Run with coverage
poetry run poe test-coverage

# Run specific test categories
poetry run poe test-unit           # Unit tests only
poetry run poe test-integration    # Integration tests only
```

## 📚 Documentation

- [**KatanaClient Guide**](docs/KATANA_CLIENT_GUIDE.md) - Complete KatanaClient usage
  guide
- [**API Reference**](docs/API_REFERENCE.md) - Generated API documentation
- [**Migration Guide**](docs/MIGRATION_GUIDE.md) - Upgrading from previous versions
- [**Testing Guide**](docs/TESTING_GUIDE.md) - Testing patterns and examples

## 🔄 Development

### Quick Start

```bash
# Install dependencies
poetry install

# Install pre-commit hooks (important!)
poetry run poe pre-commit-install

# See all available tasks
poetry run poe help

# Quick development check
poetry run poe check

# Auto-fix common issues
poetry run poe fix
```

## 🔄 Development Workflow

### Development Setup

```bash
# Install dependencies
poetry install

# Install pre-commit hooks (important!)
poetry run poe pre-commit-install

# See all available tasks
poetry run poe help

# Quick development check
poetry run poe check

# Auto-fix common issues
poetry run poe fix
```

### Code Quality Tasks

```bash
# Formatting
poetry run poe format              # Format all code and documentation
poetry run poe format-check        # Check formatting without changes
poetry run poe format-python       # Format Python code only

# Linting and Type Checking
poetry run poe lint                 # Run all linters (ruff, mypy, yaml)
poetry run poe lint-ruff           # Fast linting with ruff
poetry run poe lint-mypy           # Type checking with mypy

# Testing
poetry run poe test                 # Run all tests
poetry run poe test-coverage       # Run tests with coverage
poetry run poe test-unit           # Unit tests only
poetry run poe test-integration    # Integration tests only
```

### OpenAPI and Client Generation

```bash
# Regenerate client from OpenAPI spec
poetry run poe regenerate-client

# Validate OpenAPI specification
poetry run poe validate-openapi

# Full preparation workflow
poetry run poe prepare             # Format + lint + test + validate
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks (run once after clone)
poetry run poe pre-commit-install

# Run pre-commit on all files manually
poetry run poe pre-commit-run

# Update pre-commit hook versions
poetry run poe pre-commit-update
```

### CI/Development Workflows

```bash
# Full CI pipeline (what runs in GitHub Actions)
poetry run poe ci

# Pre-commit preparation
poetry run poe prepare

# Clean build artifacts
poetry run poe clean
```

## Configuration

All tool configurations are consolidated in `pyproject.toml` following modern Python
packaging standards:

- **Poetry**: Package metadata and dependencies
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
