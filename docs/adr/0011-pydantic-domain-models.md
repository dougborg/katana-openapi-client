# ADR-0011: Pydantic Domain Models for Business Entities

## Status

Accepted

Date: 2025-10-30

## Context

The generated attrs models from OpenAPI represent API request/response structures with
`Unset` sentinel values, nested complexity, and mixed concerns. While suitable for API
transport, they are suboptimal for:

1. **ETL and Data Processing**: Unset sentinels complicate data export and
   transformation
1. **Business Logic**: Methods for display formatting, search, validation belong on
   domain models
1. **Type Safety**: Unset sentinels require constant checking
   (`if not isinstance(x, Unset)`)
1. **Immutability**: No built-in immutability guarantees for safer data handling
1. **JSON Schema Generation**: attrs doesn't provide JSON schema for
   documentation/validation

Users need clean, business-focused models that represent "the thing itself" rather than
"how to transport the thing".

## Decision

We will create a **domain model layer** using Pydantic v2 that sits between generated
attrs models and business logic:

1. **Separate Concerns**: Domain models (`katana_public_api_client/domain/`) represent
   business entities, attrs models handle API transport
1. **Pydantic v2**: Use for validation, immutability, JSON schema generation, and clean
   serialization
1. **Automatic Conversion**: Converter functions (`domain/converters.py`) handle attrs →
   Pydantic transformation
1. **Helper Integration**: Helper classes return domain models instead of attrs models
1. **Business Methods**: Domain models include methods like `get_display_name()`,
   `matches_search()`, `to_csv_row()`

### Initial Implementation

Start with catalog entities (most common use case):

- `KatanaProduct` - Finished goods
- `KatanaMaterial` - Raw materials
- `KatanaService` - External services
- `KatanaVariant` - Product/material SKUs with pricing and inventory
- `KatanaBaseModel` - Shared configuration and ETL methods

## Consequences

### Positive Consequences

- **Clean Types**: No Unset sentinels in domain layer, clean `Optional[T]` types
- **Immutability**: Frozen by default (Pydantic `frozen=True`), prevents accidental
  mutations
- **Business Logic**: Methods live on domain models where they belong
- **ETL-Friendly**: `model_dump_for_etl()`, `to_warehouse_json()`, `to_csv_row()`
  methods
- **JSON Schema**: Automatic generation for documentation and validation
- **Type Safety**: Full mypy support without Unset handling
- **MCP Integration**: Clean, immutable data for LLM contexts
- **Testing**: Easier to test business logic on domain models

### Negative Consequences

- **Two Model Layers**: Developers must understand attrs (transport) vs Pydantic
  (domain)
- **Conversion Overhead**: Small performance cost for attrs → Pydantic conversion
- **Maintenance**: Two parallel model structures to maintain (though attrs is generated)
- **Migration**: Existing code using attrs directly needs updates

### Neutral Consequences

- **Generated Code Unchanged**: attrs models remain unmodified, conversion is opt-in
- **Helper Layer Required**: Conversion happens in helpers, not at transport layer
- **Incremental Adoption**: Can add domain models incrementally per entity type

## Alternatives Considered

### Alternative 1: Enhance attrs Models Directly

- **Description**: Add methods and utilities directly to generated attrs classes
- **Pros**: Single model layer, no conversion overhead
- **Cons**:
  - Generated code modifications get wiped on regeneration
  - Can't change attrs to Pydantic without rewriting generator
  - Unset sentinels remain problematic
  - No immutability guarantees
- **Why Rejected**: Modifying generated code is fragile and doesn't solve core issues

### Alternative 2: Wrapper Classes Around attrs

- **Description**: Create wrapper classes that delegate to attrs models
- **Pros**: No conversion, lazy evaluation possible
- **Cons**:
  - Wrapper complexity (delegation boilerplate)
  - Still dealing with Unset at access time
  - Can't truly guarantee immutability
  - Harder to serialize/deserialize
- **Why Rejected**: Complexity without solving Unset problem

### Alternative 3: Regenerate with Pydantic Generator

- **Description**: Use a different OpenAPI generator that outputs Pydantic
- **Pros**: Single model layer, native Pydantic
- **Cons**:
  - Would require rewriting all existing code
  - Loss of httpx-based async client patterns
  - openapi-python-client is well-maintained and fits our needs
  - Migration cost too high
- **Why Rejected**: Too disruptive, current generator works well

### Alternative 4: Use dataclasses Instead of Pydantic

- **Description**: Use Python standard library dataclasses for domain models
- **Pros**: No external dependency, simpler
- **Cons**:
  - No automatic validation
  - No JSON schema generation
  - No built-in serialization (need custom methods)
  - No computed fields pattern
  - Less ergonomic than Pydantic v2
- **Why Rejected**: Pydantic provides too much value for minimal cost

## References

- [PR #78: feat(client+mcp): add Pydantic domain models for catalog entities](https://github.com/dougborg/katana-openapi-client/pull/78)
- [ADR-007: Generate Domain Helper Classes](0007-domain-helper-classes.md) - Proposed
  helper pattern
- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/)
- [docs/DOMAIN_HELPERS_IMPLEMENTATION_PLAN.md](../DOMAIN_HELPERS_IMPLEMENTATION_PLAN.md)
  \- Implementation plan
