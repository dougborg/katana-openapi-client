# Architecture Quick Reference

Quick reference for key architectural patterns and decisions in this project. For
detailed rationale, see the Architecture Decision Records (ADRs).

## Project Structure

This is a **monorepo** with two packages:

```
katana-openapi-client/              # Monorepo root
├── katana_public_api_client/       # Python client library
│   └── docs/adr/                   # Client-specific ADRs
├── katana_mcp_server/              # MCP server for AI agents
│   └── docs/adr/                   # MCP-specific ADRs
└── docs/adr/                       # Shared/monorepo ADRs
```

## Core Architectural Patterns

### 1. Transport-Layer Resilience ⭐

**Pattern:** Implement resilience at the httpx transport layer instead of wrapping
individual API methods.

**Key Benefits:**

- ALL 76+ API endpoints get automatic retries, rate limiting, pagination
- No modifications to generated code needed
- Single point of configuration

**Implementation:**

```python
from katana_public_api_client import KatanaClient

async with KatanaClient() as client:
    # Automatically gets:
    # - Retry on 429 (rate limit)
    # - Retry on 502/503/504 (server errors)
    # - Exponential backoff
    # - Retry-After header support
    # - Transparent pagination
    response = await get_all_products.asyncio_detailed(client=client)
```

**Retry Strategy:**

- **429 Rate Limiting**: ALL methods retried (including POST/PATCH)
- **502/503/504 Server Errors**: Only idempotent methods (GET, PUT, DELETE)
- **4xx Client Errors**: No retries (client-side issues)
- **Network Errors**: Automatic retry with exponential backoff

**📄 ADR:**
[ADR-001: Transport-Layer Resilience](../../../katana_public_api_client/docs/adr/0001-transport-layer-resilience.md)

______________________________________________________________________

### 2. OpenAPI Code Generation

**Pattern:** Generate Python client from OpenAPI specification with automated quality
fixes.

**Workflow:**

1. Maintain OpenAPI spec: `docs/katana-openapi.yaml`
1. Generate client: `uv run poe regenerate-client` (2+ minutes)
1. Auto-fix 6,589+ lint issues with `ruff --unsafe-fixes`
1. No manual patches required

**Key Files:**

- **Generated (DO NOT EDIT):** `api/**/*.py`, `models/**/*.py`, `client.py`
- **Editable:** `katana_client.py`, `log_setup.py`, tests, docs

**📄 ADR:**
[ADR-002: OpenAPI Code Generation](../../../katana_public_api_client/docs/adr/0002-openapi-code-generation.md)

______________________________________________________________________

### 3. Transparent Automatic Pagination

**Pattern:** Automatically follow pagination links in the background without user
intervention.

**Usage:**

```python
# Request 50 items, but API returns 1000+ across multiple pages
async with KatanaClient() as client:
    response = await get_all_products.asyncio_detailed(
        client=client,
        limit=50  # Transparent pagination handles all pages
    )
    # response.parsed contains ALL results, not just first page
```

**How it works:**

- Transport layer detects paginated responses
- Automatically follows `next` links
- Aggregates all results into single response
- Transparent to API method calls

**📄 ADR:**
[ADR-003: Transparent Pagination](../../../katana_public_api_client/docs/adr/0003-transparent-pagination.md)

______________________________________________________________________

### 4. Defer Observability to httpx

**Pattern:** Use httpx's built-in event hooks for observability instead of custom
instrumentation.

**Implementation:**

```python
import httpx

# httpx provides hooks for:
# - request/response logging
# - metrics collection
# - distributed tracing
# - performance monitoring

async def log_request(request):
    print(f"Request: {request.method} {request.url}")

async def log_response(response):
    print(f"Response: {response.status_code}")

client = httpx.AsyncClient(
    event_hooks={
        'request': [log_request],
        'response': [log_response]
    }
)
```

**Benefits:**

- Standard httpx patterns
- No custom instrumentation code
- Works with existing tools (OpenTelemetry, Sentry, etc.)

**📄 ADR:**
[ADR-004: Defer Observability to httpx](../../../katana_public_api_client/docs/adr/0004-defer-observability-to-httpx.md)

______________________________________________________________________

### 5. Sync and Async APIs

**Pattern:** Provide both synchronous and asynchronous API interfaces.

**Async (Recommended):**

```python
from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products

async with KatanaClient() as client:
    response = await get_all_products.asyncio_detailed(client=client)
```

**Sync (For Simple Scripts):**

```python
from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products

with KatanaClient() as client:
    response = get_all_products.sync_detailed(client=client)
```

**Trade-offs:**

- Async: Better performance, concurrency, non-blocking I/O
- Sync: Simpler for scripts, no async/await complexity

**📄 ADR:**
[ADR-005: Sync and Async APIs](../../../katana_public_api_client/docs/adr/0005-sync-async-apis.md)

______________________________________________________________________

### 6. Response Unwrapping Utilities

**Pattern:** Provide utility functions to simplify common response handling patterns.

**Generated API returns:**

```python
Response[T]  # Contains status_code, headers, parsed, content
```

**Utility for easier access:**

```python
from katana_public_api_client.utils import unwrap_or_raise

response = await get_product.asyncio_detailed(client=client, id=123)
product = unwrap_or_raise(response)  # Returns parsed or raises exception
```

**Common patterns:**

- `unwrap_or_raise(response)` - Get parsed or raise
- `unwrap_or_none(response)` - Get parsed or None for 404
- `is_success(response)` - Boolean check

**📄 ADR:**
[ADR-006: Response Unwrapping](../../../katana_public_api_client/docs/adr/0006-response-unwrapping-utilities.md)

______________________________________________________________________

### 7. Domain Helper Classes

**Pattern:** Generate domain-specific helper classes for common operations.

**Example:**

```python
from katana_public_api_client.domains import Products

async with Products() as products:
    # High-level operations
    all_products = await products.list_all()
    product = await products.get_by_sku("SKU-123")
    new_product = await products.create(name="Widget", sku="SKU-124")
```

**Benefits:**

- Simpler API for common operations
- Hides complexity of pagination, retries
- Domain-focused interface

**📄 ADR:**
[ADR-007: Domain Helper Classes](../../../katana_public_api_client/docs/adr/0007-domain-helper-classes.md)

______________________________________________________________________

### 8. Pydantic Domain Models

**Pattern:** Use Pydantic models for business entities with validation and type safety.

**Implementation:**

```python
from pydantic import BaseModel, Field

class Product(BaseModel):
    id: int
    name: str
    sku: str
    price: Decimal = Field(gt=0)

    def is_in_stock(self) -> bool:
        return self.stock_level > 0
```

**Benefits:**

- Runtime validation
- Type safety with mypy
- Business logic methods
- Easy serialization

**📄 ADR:**
[ADR-011: Pydantic Domain Models](../../../katana_public_api_client/docs/adr/0011-pydantic-domain-models.md)

______________________________________________________________________

### 9. Validation Tiers for Agent Workflows

**Pattern:** Four-tier validation system for different workflow stages.

| Tier | Command                  | Duration | Use When                 |
| ---- | ------------------------ | -------- | ------------------------ |
| 1    | `uv run poe quick-check` | ~5-10s   | During development       |
| 2    | `uv run poe agent-check` | ~8-12s   | Before committing        |
| 3    | `uv run poe check`       | ~30s     | **Before opening PR**    |
| 4    | `uv run poe full-check`  | ~40s     | Before requesting review |

**See:** [VALIDATION_TIERS.md](VALIDATION_TIERS.md) for complete details.

**📄 ADR:**
[ADR-012: Validation Tiers](../../../katana_public_api_client/docs/adr/0012-validation-tiers-for-agent-workflows.md)

______________________________________________________________________

### 10. Katana MCP Server

**Pattern:** Model Context Protocol server for AI agent integration with Katana API.

**Architecture:**

- **Tools (10)**: Inventory search, order creation, catalog management
- **Resources (6)**: Dynamic access to inventory and orders
- **Prompts (3)**: Complete workflow templates

**Integration:**

```json
// claude_desktop_config.json
{
  "mcpServers": {
    "katana": {
      "command": "uvx",
      "args": ["katana-mcp-server"],
      "env": {
        "KATANA_API_KEY": "your-api-key"
      }
    }
  }
}
```

**📄 ADR:**
[ADR-010: Katana MCP Server](../../../katana_mcp_server/docs/adr/0010-katana-mcp-server.md)

______________________________________________________________________

### 11. uv Package Manager

**Pattern:** Use uv for fast, reliable Python package management in monorepo.

**Key Commands:**

```bash
uv sync --all-extras        # Install/update dependencies
uv run poe <task>           # Run tasks in virtual environment
uv add <package>            # Add dependency
uv run pytest               # Run tests
```

**Benefits:**

- **10-100x faster** than pip
- Lockfile for reproducibility
- Workspace support for monorepo
- Compatible with pip/PyPI

**📄 ADR:** [ADR-009: Migrate to uv](../../../docs/adr/0009-migrate-from-poetry-to-uv.md)

______________________________________________________________________

### 12. Module-Local Documentation

**Pattern:** Each package has its own `docs/` directory with package-specific
documentation.

**Structure:**

```
katana-openapi-client/
├── docs/                           # Shared/monorepo docs
│   ├── adr/                        # Shared ADRs
│   └── CONTRIBUTING.md
├── katana_public_api_client/
│   └── docs/                       # Client-specific docs
│       ├── adr/                    # Client ADRs
│       ├── guide.md
│       └── testing.md
└── katana_mcp_server/
    └── docs/                       # MCP-specific docs
        ├── adr/                    # MCP ADRs
        ├── architecture.md
        └── implementation-plan.md
```

**Benefits:**

- Documentation lives with the code
- Clear ownership and scope
- Easy to find relevant docs

**📄 ADR:**
[ADR-013: Module-Local Documentation](../../../docs/adr/0013-module-local-documentation.md)

______________________________________________________________________

## API Coverage

### Client Library (76+ Endpoints)

- **Products & Inventory** (25+): Products, variants, materials, stock levels
- **Orders** (20+): Sales orders, purchase orders, fulfillment
- **Manufacturing** (15+): BOMs, manufacturing orders, operations
- **Business Relations** (10+): Customers, suppliers, addresses
- **Configuration** (6+): Locations, webhooks, custom fields

### Data Models (150+ Fully-Typed)

All models generated from OpenAPI specification with:

- Type hints for mypy
- attrs/dataclasses for immutability
- Serialization/deserialization
- Nested object support

______________________________________________________________________

## Technology Stack

### Core Technologies

- **Python**: 3.11, 3.12, 3.13
- **httpx**: Async HTTP client
- **attrs**: Data classes
- **uv**: Package management

### Development Tools

- **ruff**: Linting and formatting
- **mypy**: Type checking
- **pytest**: Testing framework
- **pytest-xdist**: Parallel test execution
- **poethepoet (poe)**: Task runner

### Code Generation

- **openapi-python-client**: Client generation
- **Redocly**: OpenAPI validation

### Documentation

- **MkDocs**: Documentation site
- **mkdocstrings**: API reference from docstrings

______________________________________________________________________

## Common Patterns

### Error Handling

```python
from katana_public_api_client import KatanaClient
from katana_public_api_client.errors import UnexpectedStatus

async with KatanaClient() as client:
    try:
        response = await get_product.asyncio_detailed(client=client, id=123)
        if response.status_code == 200:
            product = response.parsed
        elif response.status_code == 404:
            print("Product not found")
    except UnexpectedStatus as e:
        print(f"API error: {e.status_code}")
    except Exception as e:
        print(f"Network error: {e}")
```

### Testing Patterns

```python
import pytest
from katana_public_api_client import KatanaClient

@pytest.mark.asyncio
async def test_get_product():
    async with KatanaClient() as client:
        try:
            response = await get_product.asyncio_detailed(client=client, id=1)
            assert response.status_code in [200, 404]  # 404 OK if empty
        except Exception as e:
            # Network/auth errors expected in tests
            error_msg = str(e).lower()
            assert any(word in error_msg for word in ["connection", "network", "auth"])
```

### Environment Configuration

```bash
# .env file
KATANA_API_KEY=your-api-key-here
KATANA_BASE_URL=https://api.katanamrp.com/v1  # Optional, has default
```

```python
from katana_public_api_client import KatanaClient

# Automatic from environment
async with KatanaClient() as client:
    pass

# Explicit configuration
async with KatanaClient(
    api_key="explicit-key",
    base_url="https://custom.api.com"
) as client:
    pass
```

______________________________________________________________________

## ADR Index

### Shared/Monorepo ADRs

- [ADR-009: Migrate to uv Package Manager](../../../docs/adr/0009-migrate-from-poetry-to-uv.md)
- [ADR-013: Module-Local Documentation](../../../docs/adr/0013-module-local-documentation.md)

### Client Package ADRs

- [ADR-001: Transport-Layer Resilience](../../../katana_public_api_client/docs/adr/0001-transport-layer-resilience.md)
- [ADR-002: OpenAPI Code Generation](../../../katana_public_api_client/docs/adr/0002-openapi-code-generation.md)
- [ADR-003: Transparent Pagination](../../../katana_public_api_client/docs/adr/0003-transparent-pagination.md)
- [ADR-004: Defer Observability to httpx](../../../katana_public_api_client/docs/adr/0004-defer-observability-to-httpx.md)
- [ADR-005: Sync and Async APIs](../../../katana_public_api_client/docs/adr/0005-sync-async-apis.md)
- [ADR-006: Response Unwrapping Utilities](../../../katana_public_api_client/docs/adr/0006-response-unwrapping-utilities.md)
- [ADR-007: Domain Helper Classes](../../../katana_public_api_client/docs/adr/0007-domain-helper-classes.md)
- [ADR-008: Avoid Builder Pattern](../../../katana_public_api_client/docs/adr/0008-avoid-builder-pattern.md)
  **(PROPOSED)**
- [ADR-011: Pydantic Domain Models](../../../katana_public_api_client/docs/adr/0011-pydantic-domain-models.md)
- [ADR-012: Validation Tiers](../../../katana_public_api_client/docs/adr/0012-validation-tiers-for-agent-workflows.md)

### MCP Server ADRs

- [ADR-010: Katana MCP Server](../../../katana_mcp_server/docs/adr/0010-katana-mcp-server.md)

______________________________________________________________________

## Quick Links

### Documentation

- **[README.md](../../../README.md)** - Project overview
- **[CLAUDE.md](../../../CLAUDE.md)** - AI agent instructions
- **[CONTRIBUTING.md](../../../docs/CONTRIBUTING.md)** - Contribution guidelines

### Client Documentation

- **[Client Guide](../../../katana_public_api_client/docs/guide.md)** - User guide
- **[Testing Guide](../../../katana_public_api_client/docs/testing.md)** - Testing
  strategy

### MCP Documentation

- **[MCP Architecture](../../../katana_mcp_server/docs/architecture.md)** - MCP design
- **[Implementation Plan](../../../katana_mcp_server/docs/implementation-plan.md)** -
  MCP roadmap

______________________________________________________________________

## Summary

**Key Architectural Principles:**

1. ⚡ **Transport-Layer Resilience** - Single point for retries, rate limiting,
   pagination
1. 🔧 **Code Generation** - OpenAPI spec drives client generation
1. 📄 **Separation of Concerns** - Generated vs editable code
1. 🎯 **Validation Tiers** - Right validation at right time
1. 🏗️ **Monorepo Structure** - Client + MCP server with shared tooling
1. 📚 **Module-Local Docs** - Documentation lives with code
1. 🚀 **uv for Speed** - Fast, reliable package management

**Remember:** When in doubt about architectural decisions, check the ADRs first!
