# API Feedback for Katana Development Team

This document provides systematic feedback on the Katana Public API based on extensive
client development, validation testing, and real-world usage patterns. These insights
come from building a production-ready Python client with comprehensive OpenAPI
specification analysis.

**Last Updated**: August 13, 2025 **Client Version**: v0.7.0 **API Endpoints Analyzed**:
76+ endpoints **Data Models Analyzed**: 150+ schemas **Documentation Pages Analyzed**:
245 comprehensive pages from developer.katanamrp.com

______________________________________________________________________

## 🔴 Critical Issues

### Response Code Inconsistencies for CREATE Operations

**Issue**: Katana API uses non-standard HTTP status codes for CREATE operations.

**Current Behavior**:

- **All CREATE endpoints return `200 OK`** instead of standard `201 Created`
- Verified across 245 comprehensive documentation pages from developer.katanamrp.com
- Consistent behavior: Every CREATE operation documented shows "200 Response"

**Examples**:

- `POST /customers` → Returns `200 OK`
- `POST /products` → Returns `200 OK`
- `POST /sales_orders` → Returns `200 OK`
- `POST /price_lists` → Returns `200 OK`
- `POST /webhooks` → Returns `200 OK`

**Impact**:

- **Standards Violation**: Violates HTTP/REST standards (RFC 7231 Section 6.3.2)
- **Developer Expectations**: Most REST APIs return `201 Created` for successful
  resource creation
- **Client Integration**: May confuse developers familiar with standard REST conventions
- **Semantic Clarity**: `200 OK` typically indicates successful processing, not resource
  creation

**Recommendation**:

- **Consider**: Migrate to `201 Created` for CREATE operations in future API version
- **Breaking Change**: Would require proper versioning and migration strategy
- **Industry Alignment**: Would align Katana API with REST standards and developer
  expectations
- **Benefit**: Better alignment with HTTP standards and developer expectations
- **Migration**: Could support both status codes during transition period
- **Documentation**: Update both OpenAPI spec and developer documentation
- **Breaking Change**: Document as API improvement with proper versioning

### BOM Row Creation Returns No Content

**Issue**: BOM row creation operations return `204 No Content` instead of created
resource data.

**Affected Endpoints**:

- `POST /bom_rows` (single) → Returns `204 No Content`
- `POST /bom_rows/batch` (bulk) → Returns `204 No Content`

**Critical Problems**:

1. **No Resource IDs**: Impossible to determine IDs of newly created BOM rows
1. **Non-Standard Behavior**: `204 No Content` typically indicates successful processing
   with no response body
1. **Integration Limitations**: Prevents immediate follow-up operations on created
   resources
1. **Workflow Disruption**: Forces additional API calls to retrieve created resource
   information
1. **Documentation Gap**: Success scenarios are completely undocumented

**Business Impact**:

- **Automated Workflows**: Cannot chain operations that depend on new BOM row IDs
- **Batch Operations**: No way to map bulk creation results to specific inputs
- **Error Handling**: Difficult to verify which specific rows were created successfully
- **Data Synchronization**: Prevents efficient sync operations with external systems
- **Developer Experience**: Lack of success documentation creates confusion

**Recommendation**:

- **Critical Fix**: Return created resource data with proper status codes
- **Single Creation**: Return `201 Created` with created BOM row object including
  generated ID
- **Bulk Creation**: Return `201 Created` with array of created BOM row objects
  including IDs
- **Documentation**: Add comprehensive success response examples to official
  documentation
- **Consistency**: Align with other CREATE endpoints that return resource data

### BOM Management Operations Severely Limited

**Issue**: BOM row management lacks essential bulk and ordering operations, requiring
excessive API calls for common workflows.

**Missing Critical Operations**:

1. **No Rank/Order Management**:

   - `PATCH /bom_rows/{id}` does not support updating `rank` field
   - Cannot reorder BOM rows efficiently
   - No dedicated reordering endpoints (unlike product operations which have
     `/product_operation_rerank`)
   - **API Inconsistency**: Product operations have reranking support, BOM rows do not

1. **No Bulk Operations**:

   - ❌ Bulk update: No `PATCH /bom_rows/batch` endpoint
   - ❌ Bulk delete: No `DELETE /bom_rows/batch` endpoint
   - ❌ Bulk replace: No `PUT /variants/{id}/bom_rows` to replace entire BOM

1. **Inefficient BOM Management**:

   - Updating BOM structure requires many individual API calls
   - No atomic operations for BOM modifications
   - No way to replace entire BOM in single request

**Common Workflow Impact**:

- **BOM Reordering**: Must delete and recreate rows or PATCH changes by rank order to
  change order
- **BOM Updates**: Each row requires separate PATCH request
- **BOM Replacement**: Must delete all rows, then create new ones individually
- **Recipe Management**: What should be simple recipe changes require dozens of API
  calls

**Business Impact**:

- **Performance**: Excessive API calls slow down BOM management operations
- **Reliability**: Multiple requests increase failure points and partial update risks
- **Rate Limiting**: High request volume may hit API rate limits
- **User Experience**: Slow response times for common manufacturing operations
- **Data Consistency**: No atomic operations risk leaving BOMs in inconsistent states

**Recommendation**:

- **Add Rank Support**: Enable rank field updates in `PATCH /bom_rows/{id}`
- **BOM Rerank Endpoint**: Add `POST /bom_row_rerank` endpoint similar to existing
  `/product_operation_rerank`
- **Bulk Operations**: Add endpoints for batch update, delete, and create operations:
  - `PATCH /bom_rows/batch` for bulk updates
  - `DELETE /bom_rows/batch` for bulk deletions
  - `PUT /variants/{id}/bom_rows` for atomic BOM replacement
- **Consistency**: Align BOM row management capabilities with product operation
  management
- **Atomic Operations**: Ensure BOM modifications can be done transactionally

### Missing CREATE Endpoint - Storage Bins

**Issue**: No `POST /storage_bins` endpoint exists despite having update/delete
operations.

**Current CRUD Coverage**:

- ✅ GET `/storage_bins` (list)
- ✅ PATCH `/storage_bins/{id}` (update)
- ✅ DELETE `/storage_bins/{id}` (delete)
- ❌ POST `/storage_bins` (create) - **MISSING**

**Business Impact**:

- Prevents automated warehouse setup workflows
- Forces manual UI creation of storage locations
- Breaks CRUD completeness expectations
- Limits programmatic inventory management capabilities

**Recommendation**: Add `POST /storage_bins` endpoint with proper `201 Created`
response.

______________________________________________________________________

## 🟡 Documentation & Specification Issues

### Extend Parameter Documentation Gap

**Issue**: The `extend` query parameter is available on many endpoints but the valid
object names for each endpoint are not documented.

**Current Behavior**:

- Many endpoints support an `extend` parameter to include related objects in responses
- Parameter accepts a comma-separated list of object names to expand
- Valid object names vary by endpoint and resource type
- No documentation exists listing available extend options per endpoint

**Examples of Undocumented Extend Options**:

- `GET /products?extend=variants,bom_rows` - Works but variants/bom_rows not documented
  as valid options
- `GET /sales_orders?extend=customer,rows` - Available extends unknown without trial and
  error
- `GET /manufacturing_orders?extend=productions,recipe_rows` - Extend capabilities
  undiscovered

**Developer Impact**:

- **Trial and Error**: Developers must guess valid extend object names
- **Inefficient Discovery**: No systematic way to find all available relationships
- **Missed Optimization**: Developers may not use extend due to unclear documentation
- **Integration Delays**: Time spent testing which extend options work

**Business Impact**:

- **API Efficiency**: Extend parameter can reduce API calls significantly when used
  properly
- **Developer Experience**: Poor documentation discourages optimal API usage patterns
- **Performance**: Missed opportunities for single-request data retrieval

**Recommendation**:

- **Document All Extend Options**: List valid extend object names for each endpoint
- **Relationship Documentation**: Clearly document which related objects can be expanded
- **Examples**: Provide practical examples showing extend usage for common scenarios
- **API Reference**: Include extend options in endpoint documentation consistently

______________________________________________________________________

## 🔵 API Design & Consistency Improvements

### PATCH vs PUT Semantics

**Issue**: PATCH operations sometimes require fields that should be optional.

**Example**: `PATCH /storage_bins/{id}` spec shows `bin_name` and `location_id` as
required.

**REST Standard**: PATCH should allow partial updates with all fields optional.

**Recommendation**:

- Make all PATCH operation fields optional
- Consider adding PUT endpoints for full replacement operations
- Document partial update behavior clearly

### Webhook Payload Documentation Gaps

**Issue**: Webhook payload structure includes undocumented fields.

**Specific Finding**: Webhook examples show a `status` field in the event payload's
`object` property, but this field is not documented anywhere in the official API
documentation.

**Example Webhook Payload Structure**:

```json
{
  "resource_type": "sales_order",
  "action": "sales_order.delivered",
  "webhook_id": 123,
  "object": {
    "id": "12345",
    "status": "DELIVERED",  // ← This field is undocumented
    "href": "https://api.katanamrp.com/v1/sales_orders/12345"
  }
}
```

**Documentation Gap**:

- No specification of what values `status` can contain
- No indication of whether this field is always present
- Unknown if `status` values vary by resource type
- Unclear relationship between `status` and the actual resource state

**Business Impact**:

- Developers cannot rely on `status` field for automation
- Webhook integration requires additional API calls to get reliable status
- Increases development complexity and API usage

**Recommendation**:

- Document all fields present in webhook payloads
- Specify possible `status` values for each resource type
- Clarify the relationship between webhook `status` and resource state
- Consider removing undocumented fields or making them official

______________________________________________________________________

## 🟢 Feature Gaps & Enhancement Opportunities

### Bulk Operations Support

**Current State**: Limited bulk operations available, but not comprehensive across all
resource types.

**Available Bulk Operations**:

- `/bom_rows/batch/create` - Bulk creation of BOM (Bill of Materials) rows using
  `BatchCreateBomRowsRequest` schema

**Business Need**:

- Large integrations need efficient bulk operations
- Migration scenarios require bulk data transfer
- Inventory updates often involve hundreds of records

**Missing Operations**:

- Bulk product creation/updates
- Bulk inventory adjustments
- Bulk order processing
- Bulk customer/supplier import

**API Efficiency Issues**:

- Most resource types still require individual API calls for creation/updates
- BOM row management has some bulk support but other related resources (products,
  variants) do not
- High-volume scenarios (product imports, customer imports) require careful rate
  limiting

**Recommendation**:

- Add bulk endpoints for high-volume operations beyond BOM rows
- Implement proper transaction handling for bulk operations
- Provide progress tracking for long-running bulk jobs
- Extend bulk support to products, variants, customers, and inventory adjustments

### Authentication & Permission Granularity

**Questions**:

- Are there different API key permission levels?
- Can permissions be scoped to specific resources?
- How is multi-location/multi-company data isolation handled?

**Business Need**:

- Read-only keys for reporting systems
- Scoped keys for integration partners
- Audit trails for API access

## 📊 Rate Limiting & Performance

### Current Implementation

- 60 requests per 60 seconds
- Retry-After headers provided
- No apparent distinction between endpoint types

**Developer Feedback**: The current 60 requests per minute limitation has been
frustrating for production integrations, especially when combined with the lack of bulk
operations for most endpoints. Consider increasing limits while maintaining system
stability.

### Questions

- Do different endpoint categories have different limits?
- Are there separate limits for bulk operations?
- How are rate limits calculated for different API key tiers?

### Recommendations

- **Increase Rate Limits**: Consider raising from 60 to 120-300 requests per minute to
  reduce integration friction
- **Tiered Rate Limiting**: Implement higher limits for production API keys vs.
  development keys
- **Endpoint-Specific Limits**: Higher limits for read operations (GET) vs. write
  operations (POST/PATCH)
- **Bulk Operation Limits**: Separate, higher limits for bulk endpoints to encourage
  their use
- **Rate Limit Monitoring**: Provide dashboards for API usage monitoring and limit
  tracking
- **Documentation**: Clearly document rate limiting strategy and best practices
