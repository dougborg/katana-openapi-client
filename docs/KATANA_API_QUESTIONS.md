# Questions for Katana API Development Team

This document tracks questions and discrepancies discovered during systematic validation
of the Katana Public API OpenAPI specification against the official documentation at
developer.katanamrp.com.

## Storage Bins (Bin Locations)

### Missing CREATE Endpoint

**Issue**: No `POST /bin_locations` endpoint exists to create new storage bins.

- **Current endpoints**: GET (list), PATCH (update), DELETE (delete)
- **Missing**: POST (create)
- **Question**: How do users create new storage bins through the API? Is this
  intentionally managed only through the UI?
- **Business impact**: Automated warehouse setup and inventory management workflows
  cannot programmatically create storage locations.

### Schema Inconsistencies

**Issue**: Original OpenAPI spec shows PATCH operation requires `bin_name` and
`location_id` as required fields.

- **Current behavior**: PATCH operations typically make all fields optional (partial
  updates)
- **Question**: Should PATCH /bin_locations/{id} require both fields, or should they be
  optional for partial updates?
- **Recommendation**: Make fields optional for true PATCH semantics, or provide a PUT
  endpoint for full replacement.

## Batch Endpoints

### Schema Validation Questions

**Issue**: During validation, we found discrepancies between the original OpenAPI spec
and current API documentation.

- **Batch creation**: Original spec had different field names and structure
- **Question**: Has the batch API been updated since the original OpenAPI spec was
  created?
- **Recommendation**: Ensure OpenAPI spec is kept in sync with actual API
  implementation.

## BOM Row Endpoints

### Documentation Response Code Discrepancy

**Issue**: Official documentation shows incorrect response code for BOM row creation.

- **Documentation states**: `POST /bom_rows` returns `204 No Content`
- **Actual API behavior**: Returns `200 OK` (verified through testing)
- **Question**: Should documentation be updated to reflect the actual 200 response?
- **Impact**: Integration developers may expect 204 status and implement incorrect
  response handling.
- **Recommendation**: Update documentation to show correct 200 response code for BOM row
  creation.

## Inventory Endpoints

### Deprecated Reorder Point Endpoint

**Issue**: Reorder point update endpoint exists but is deprecated in favor of safety
stock levels.

- **Endpoint**: `POST /inventory_reorder_points`
- **Official documentation**:
  <https://developer.katanamrp.com/reference/update-reorder-point>
- **Status**: "(Endpoint deprecation, we recommend using safety_stock instead)"
- **Replacement**: `POST /inventory_safety_stock_levels`
- **Resolution**: Added deprecated POST endpoint to OpenAPI spec with proper deprecation
  warning
- **Question**: Should deprecated endpoints be included in client SDKs, or excluded to
  encourage migration?
- **Business impact**: Existing integrations may rely on reorder point endpoint, but new
  integrations should use safety stock levels.

## General API Design Questions

### CRUD Pattern Completeness

**Observation**: Not all resources follow complete CRUD patterns.

- **Storage Bins**: Missing CREATE (POST)
- **Question**: Is there a design principle that determines which resources support full
  CRUD vs. partial operations?
- **Recommendation**: Document which resources are read-only, which support partial
  CRUD, and the business reasons.

### Common Schema Patterns

**Improvement Made**: We introduced `BaseEntity`, `UpdatableEntity`, `DeletableEntity`,
and `ArchivableEntity` patterns.

- **Question**: Would the Katana team like to adopt these common schema patterns in the
  official spec?
- **Benefits**: Reduces duplication, improves consistency, easier maintenance.

### Parameter Standardization

**Improvement Made**: We standardized common parameter descriptions (e.g.,
`include_deleted`, `include_empty`, `limit`, `page`).

- **Question**: Should parameter descriptions be generic for reusability across
  endpoints?
- **Current**: Some parameters had endpoint-specific descriptions
- **Recommendation**: Use generic descriptions for common parameters.

## Documentation Sync Issues

### OpenAPI Spec vs. Documentation

**Issue**: Discrepancies found between OpenAPI spec and developer.katanamrp.com
documentation.

- **Example**: Batch endpoint schemas differed significantly
- **Question**: Which is the source of truth - OpenAPI spec or web documentation?
- **Recommendation**: Establish single source of truth and automated sync process.

### Missing Endpoint Documentation

**Question**: Are there any endpoints that exist in the API but are not documented in
either the OpenAPI spec or web documentation?

- **Use case**: Advanced users may need access to internal/admin endpoints
- **Recommendation**: Audit all available endpoints and document public vs. private
  APIs.

## Webhooks and Event Coverage

### Event Completeness

**Question**: The current OpenAPI spec lists only 2 webhook events
(`sales_order.created`, `product_recipe_row.deleted`).

- **Documentation mentions**: "50+ event types including sales orders, manufacturing
  orders, inventory changes"
- **Question**: Can we get the complete list of available webhook events?
- **Business impact**: Integration developers need to know all available real-time
  events.

## Rate Limiting and Pagination

### Rate Limit Implementation

**Current spec**: 60 requests per 60 seconds, with retry headers

- **Question**: Are there different rate limits for different endpoint categories?
- **Question**: Do bulk operations (like batch create) have different limits?

### Pagination Consistency

**Observation**: All list endpoints use `limit` (max 250, default 50) and `page`
parameters.

- **Question**: Are there any endpoints that use cursor-based pagination instead?
- **Question**: For large datasets (>10k records), are there more efficient bulk export
  options?

## Authentication and Permissions

### API Key Permissions

**Question**: Are there different permission levels for API keys?

- **Use case**: Read-only keys for reporting vs. full-access keys for integrations
- **Question**: Can API key permissions be scoped to specific resources or operations?

### Multi-tenant Considerations

**Question**: How does the API handle multi-company/multi-location scenarios?

- **Question**: Are there tenant isolation guarantees in the API responses?
- **Question**: Do location_id filters provide proper data isolation?

## Integration Patterns

### Bulk Operations

**Question**: Are there bulk operation endpoints for high-volume data scenarios?

- **Example**: Bulk product creation, bulk inventory updates
- **Current**: Most endpoints appear to be single-record operations
- **Business impact**: Large integrations may need efficient bulk operations.

### Data Export/Import

**Question**: Are there dedicated endpoints for full data export/import?

- **Use case**: Migration scenarios, backup/restore operations
- **Question**: What's the recommended approach for syncing large datasets?

______________________________________________________________________

## Next Steps

1. **Validation Priority**: Continue systematic validation of remaining endpoints
1. **Documentation**: Update findings as we validate more endpoints
1. **Katana Contact**: Schedule discussion with Katana API team to review these
   questions
1. **Schema Improvements**: Propose our common schema patterns for official adoption

## Document Information

*Document created during systematic API validation - Last updated: August 7, 2025*
