# ADR-0010: Katana MCP Server for Claude Code Integration

## Status

Proposed

Date: 2025-10-21

## Context

The Katana OpenAPI Client provides a comprehensive Python SDK for interacting with the
Katana Manufacturing ERP API. However, using this client within Claude Code currently
requires users to manually write integration code, understand the API structure, and
handle common workflow patterns themselves.

The Model Context Protocol (MCP) is an open-source standard that enables AI systems like
Claude Code to connect with external tools and data sources through a standardized
interface. By creating a Katana MCP server, we can:

1. **Enable Natural Language Interactions**: Users can interact with their Katana
   instance using natural language instead of writing code
1. **Provide Pre-built Workflows**: Common manufacturing operations (check inventory,
   create orders, monitor production) become single commands
1. **Leverage Existing Client**: Build on top of our well-tested KatanaClient with its
   transport-layer resilience
1. **Demonstrate Best Practices**: Show how to build production-ready MCP servers using
   the Python SDK

### Forces at Play

**Technological:**

- MCP Python SDK (`mcp.server.fastmcp`) provides FastMCP class for rapid server
  development
- Our KatanaClient already handles authentication, retries, rate limiting, and
  pagination
- The cookbook (ADR-006) demonstrates 20+ common integration patterns
- Type system integration via Pydantic enables automatic schema generation

**User Experience:**

- Users want quick access to Katana data without writing integration code
- Manufacturing workflows often involve multiple API calls (check stock, create MO,
  etc.)
- Natural language is more intuitive than remembering API endpoint structures
- Progress reporting for long-running operations improves user experience

**Project Goals:**

- Demonstrate the value of the client library in real-world scenarios
- Provide a reference implementation for MCP server development
- Lower the barrier to entry for Katana API automation
- Expand the client's ecosystem beyond pure Python usage

## Decision

We will create a `katana-mcp-server` as a **separate package** that depends on
`katana-openapi-client`, implementing the Model Context Protocol to expose Katana
functionality to Claude Code and other MCP clients.

### Architecture

**Package Structure:**

```
katana-mcp-server/
├── pyproject.toml          # Depends on katana-openapi-client + mcp
├── src/
│   └── katana_mcp/
│       ├── __init__.py
│       ├── server.py       # FastMCP server implementation
│       ├── tools/          # Tool implementations
│       │   ├── inventory.py
│       │   ├── sales_orders.py
│       │   ├── purchase_orders.py
│       │   └── manufacturing.py
│       ├── resources/      # Resource endpoints
│       │   ├── inventory.py
│       │   ├── orders.py
│       │   └── manufacturing.py
│       └── prompts/        # Reusable prompts
│           └── workflows.py
├── tests/
└── README.md
```

**Core Components:**

1. **Tools** (Actions with side effects):

   **Inventory (3 tools):**

   - `check_inventory` - Check stock levels for specific SKU
   - `list_low_stock_items` - Find products below reorder point
   - `search_products` - Search products by name/SKU

   **Sales Orders (3 tools):**

   - `create_sales_order` - Create new sales order
   - `get_sales_order_status` - Get order details and status
   - `list_recent_sales_orders` - List recent sales orders

   **Purchase Orders (3 tools):**

   - `create_purchase_order` - Create new purchase order
   - `get_purchase_order_status` - Get PO details and status
   - `receive_purchase_order` - Mark PO as received

   **Manufacturing (3 tools):**

   - `create_manufacturing_order` - Create manufacturing order
   - `get_manufacturing_order_status` - Get MO details and status
   - `list_active_manufacturing_orders` - List in-progress MOs

1. **Resources** (Read-only data):

   - `inventory://products` - List all products
   - `inventory://stock/{sku}` - Get stock for specific SKU
   - `orders://sales` - Recent sales orders
   - `orders://purchase` - Recent purchase orders
   - `manufacturing://status` - Manufacturing capacity overview

1. **Prompts** (Workflow templates):

   - `check-low-stock` - Generate low stock report
   - `create-order-from-template` - Guide order creation
   - `manufacturing-dashboard` - Show production status

### Implementation Approach

**1. Server Setup:**

```python
from mcp.server.fastmcp import FastMCP
from katana_public_api_client import KatanaClient

mcp = FastMCP("katana-erp")

@mcp.tool()
async def check_inventory(sku: str, ctx: Context) -> InventoryStatus:
    """Check inventory status for a specific SKU."""
    async with KatanaClient() as client:
        # Use existing client methods
        await ctx.report_progress(0.5, 1.0)
        # ... implementation
```

**2. Leverage Cookbook Patterns:**

Each tool will implement patterns from our cookbook:

- Concurrent requests for performance (Cookbook §7.2)
- Error handling with retries (Cookbook §4.1)
- Structured logging (Cookbook §6.1)
- Caching for frequently accessed data (Cookbook §7.3)

**3. Type Safety:**

Use Pydantic models for all tool return types:

```python
from pydantic import BaseModel

class InventoryStatus(BaseModel):
    sku: str
    in_stock: int
    location: str
    reorder_point: int | None

@mcp.tool()
async def check_inventory(sku: str) -> InventoryStatus:
    # MCP automatically generates schema from return type
    ...
```

**4. Configuration:**

Support multiple authentication methods:

```json
{
  "mcpServers": {
    "katana-erp": {
      "command": "uvx",
      "args": ["katana-mcp-server"],
      "env": {
        "KATANA_API_KEY": "your-key",
        "KATANA_BASE_URL": "https://api.katanamrp.com/v1"
      }
    }
  }
}
```

### Scope

**Phase 1 (MVP):**

- 12 core tools covering inventory, sales orders, purchase orders, and manufacturing
- 5 resources for read-only data access
- 2-3 workflow prompts for common scenarios
- Basic error handling and progress reporting
- Comprehensive documentation and examples

**Phase 2 (Expansion):**

- Advanced workflows (multi-step order processing)
- Webhook integration for real-time updates
- Caching layer for performance
- Metrics and observability
- OAuth 2.0 support for multi-tenant deployments

**Out of Scope:**

- Admin/configuration operations (user management, settings)
- Direct database access (only via Katana API)
- Historical data analysis (beyond what API provides)
- Custom reporting (use API directly for this)

## Consequences

### Positive Consequences

1. **Lower Barrier to Entry**: Users can access Katana without learning the API
   structure or writing integration code

1. **Natural Language Interface**: Manufacturing teams can use plain English to interact
   with their ERP system through Claude Code

1. **Demonstrates Client Value**: Shows the client library's capabilities in a
   real-world integration scenario

1. **Reference Implementation**: Provides a blueprint for others building MCP servers
   with our client or similar OpenAPI-generated clients

1. **Ecosystem Growth**: Expands beyond Python developers to include Claude Code users
   and LLM-based automation

1. **Workflow Acceleration**: Common tasks (check inventory, create orders) become
   one-line commands instead of multi-step code

1. **Leverages Existing Work**: Built on battle-tested KatanaClient with 96% test
   coverage and production-ready resilience

### Negative Consequences

1. **Maintenance Burden**: Another package to maintain, document, and release

1. **API Surface Duplication**: Tools mirror some client functionality, requiring
   synchronization

1. **Limited Customization**: Pre-built tools may not fit every use case; users might
   still need the client directly for complex workflows

1. **Dependency Chain**: MCP server depends on client, which depends on generated code
   from OpenAPI spec

1. **Authentication Complexity**: Managing API keys through MCP configuration adds
   another security consideration

1. **Version Compatibility**: Must ensure MCP server versions align with client library
   versions

### Neutral Consequences

1. **Separate Repository**: Keeping it as a separate package maintains clear boundaries
   but requires coordination for releases

1. **Testing Requirements**: Need integration tests that run against real Katana API (or
   mock server)

1. **Documentation Split**: MCP server docs separate from client docs, but linked
   together

## Alternatives Considered

### Alternative 1: Build as Claude Code Skill Instead

**Description:**

Implement as a Claude Code skill (`.claude/skills/katana.md`) instead of an MCP server.
Skills are simpler to set up and don't require running a separate server process.

**Pros:**

- Simpler deployment (just a markdown file)
- No separate package to maintain
- Easier for users to customize
- Direct integration with project context

**Cons:**

- Limited to Claude Code (MCP works with any MCP client)
- No structured tool output (just text)
- Can't leverage FastMCP's type safety and schema generation
- Less reusable across different contexts

**Why Rejected:**

MCP provides better type safety, reusability, and works across multiple clients. The
skill approach is too limited for a production-ready integration.

### Alternative 2: Extend Client Library with MCP Support

**Description:**

Add MCP server functionality directly to `katana-openapi-client` as an optional feature
activated with `pip install katana-openapi-client[mcp]`.

**Pros:**

- Single package to maintain
- Guaranteed version compatibility
- Simpler for users (one install)

**Cons:**

- Violates single responsibility principle
- Adds MCP dependencies to all users (even those not using it)
- Complicates client library testing
- Makes client repo more complex
- Harder to version independently

**Why Rejected:**

Separation of concerns is clearer with separate packages. Not all client users need MCP,
and mixing concerns would complicate both packages.

### Alternative 3: Direct API Integration (No Client)

**Description:**

Build MCP server directly on httpx/requests without using our client library.

**Pros:**

- No dependency on our client
- Full control over API interactions
- Could be lighter weight

**Cons:**

- Duplicates all the work in our client (retries, rate limiting, pagination)
- No type safety from generated models
- 96% test coverage would need to be recreated
- Missing resilience features
- Cookbook patterns not available

**Why Rejected:**

This wastes the significant investment in the client library and its battle-tested
resilience features. Building on the client provides immediate production-ready
behavior.

## References

- [Model Context Protocol Documentation](https://modelcontextprotocol.io)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Claude Code MCP Guide](https://docs.claude.com/en/docs/claude-code/mcp)
- [FastMCP Documentation](https://github.com/modelcontextprotocol/python-sdk#fastmcp)
- [ADR-001: Transport-Layer Resilience](0001-transport-layer-resilience.md)
- [ADR-006: Response Unwrapping Utilities](0006-response-unwrapping-utilities.md)
- [Cookbook Documentation](../COOKBOOK.md)
- [GitHub Issue #XX: Create Katana MCP Server](#) <!-- TODO: Create issue -->

## Implementation Plan

### Phase 1: MVP (2-3 weeks)

**Week 1: Core Infrastructure**

- Set up package structure and dependencies
- Implement FastMCP server with basic configuration
- Add authentication via environment variables
- Create 2-3 simple tools (check_inventory, list_products)
- Write unit tests with mocked KatanaClient

**Week 2: Essential Tools**

- Implement remaining 9-10 tools across all domains:
  - Inventory tools (list_low_stock_items, search_products)
  - Sales order tools (create, get_status, list_recent)
  - Purchase order tools (create, get_status, receive)
  - Manufacturing tools (create, get_status, list_active)
- Add 5 resources for read-only data
- Implement progress reporting for long operations
- Add integration tests for each tool
- Document tool signatures and usage

**Week 3: Polish and Documentation**

- Create 2-3 workflow prompts
- Write comprehensive README
- Add usage examples for Claude Code
- Create configuration templates
- Integration testing with real Katana API

### Phase 2: Enhancement (Future)

- Advanced workflow tools
- Performance optimizations (caching, concurrent requests)
- OAuth 2.0 support
- Metrics and monitoring integration
- Additional prompts and workflows based on user feedback

## Success Criteria

The MCP server will be considered successful if it achieves:

1. **Functionality**: Implements 12 tools covering inventory, sales orders, purchase
   orders, and manufacturing
1. **Reliability**: Handles errors gracefully with proper retry logic
1. **Usability**: Clear documentation enables setup in < 5 minutes
1. **Type Safety**: All tools have proper type hints and return structured data
1. **Testing**: 80%+ test coverage with both unit and integration tests
1. **Performance**: Responses within acceptable timeframes (< 5s for most operations)
1. **Adoption**: Used by at least 3 external projects/users within first quarter

## Decisions on Open Questions

### 1. Naming: `katana-mcp-server`

**Decision**: Use `katana-mcp-server` as the package name.

**Rationale**:

- Follows standard pattern: `{service}-mcp-server` (e.g., `postgres-mcp-server`)
- Clear that it's a server, not just an integration
- Sorts well in package listings (katana prefix keeps it near `katana-openapi-client`)
- Distinguishable from potential future packages

### 2. Granularity: 12 tools grouped by domain

**Decision**: Implement 12 focused tools organized into 4 domain groups (inventory,
sales orders, purchase orders, manufacturing).

**Rationale**:

- Covers 80% of common use cases without overwhelming users
- Domain grouping aids discoverability
- Balanced between too few (< 5, limiting) and too many (> 20, overwhelming)
- Easy to extend with additional tools in Phase 2 based on user feedback

### 3. State Management: No caching in Phase 1

**Decision**: Start without caching, add TTL-based caching in Phase 2 for static data
only.

**Rationale**:

- **Phase 1**: Simpler implementation, always fresh data, no staleness issues
- **Phase 2**: Add optional TTL cache for static resources (products, locations)
- Never cache mutable data (inventory levels, order statuses) - too risky for incorrect
  business decisions

### 4. Versioning: Independent semantic versioning

**Decision**: Use independent semantic versioning with compatible range dependencies on
the client library.

**Strategy**:

```toml
[project]
name = "katana-mcp-server"
version = "0.1.0"  # Independent versioning
dependencies = [
    "katana-openapi-client>=0.21.0,<0.23.0",  # Compatible minor versions
    "mcp>=1.0.0",
]
```

**Version Policy**:

- **MAJOR**: Breaking changes in tool signatures or behavior
- **MINOR**: New tools, new features (backward compatible)
- **PATCH**: Bug fixes, documentation updates

Compatibility matrix will be documented in README.

### 5. Distribution: PyPI + uvx (Phase 1), Docker optional (Phase 2)

**Decision**: Distribute via PyPI with uvx as the primary installation method. Docker
image is optional for Phase 2 if demand exists.

**Installation Methods**:

```bash
# Primary method (uvx - recommended in Claude Code docs)
uvx katana-mcp-server

# Alternative (pip install)
pip install katana-mcp-server
python -m katana_mcp
```

### 6. Multi-tenancy: Single instance (Phase 1)

**Decision**: Single Katana instance per server process in Phase 1. Users run multiple
server instances for multiple Katana environments.

**Configuration**:

```json
{
  "mcpServers": {
    "katana-production": {
      "command": "uvx",
      "args": ["katana-mcp-server"],
      "env": {"KATANA_API_KEY": "prod-key"}
    },
    "katana-staging": {
      "command": "uvx",
      "args": ["katana-mcp-server"],
      "env": {"KATANA_API_KEY": "staging-key"}
    }
  }
}
```

**Phase 2**: Consider adding instance parameter to tools if multi-tenancy becomes a
common requirement.

## Next Steps

1. Create GitHub issue to track implementation
1. Set up repository: `katana-mcp-server`
1. Create initial package structure with pyproject.toml
1. Implement 1-2 proof-of-concept tools
1. Test integration with Claude Code
1. Gather feedback and iterate on design
