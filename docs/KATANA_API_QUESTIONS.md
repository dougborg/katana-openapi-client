# API Feedback for Katana Development Team

This document provides systematic feedback on the Katana Public API based on extensive
client development, validation testing, and real-world usage patterns. These insights
come from building a production-ready Python client with comprehensive OpenAPI
specification analysis.

**Last Updated**: August 29, 2025 **Client Version**: v0.9.0 **API Endpoints Analyzed**:
76+ endpoints **Data Models Analyzed**: 207 schemas **Documentation Pages Analyzed**:
245 comprehensive pages from developer.katanamrp.com

**Validation Status**: OpenAPI schema validation completed with 6 remaining
discrepancies between external validation examples and actual API behavior (documented
below).

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

### Documentation Accuracy Issues in Material Endpoints

**Issue**: Several inconsistencies and errors found in official API documentation during
comprehensive validation against OpenAPI specification.

**Source**: Comprehensive cross-validation of material endpoints against 245+ pages from
developer.katanamrp.com, completed August 2025.

**Documentation Errors Identified**:

1. **Copy-Paste Errors in Material Configuration Examples**:

   - **Location**: Material object documentation and config examples
   - **Error**: Shows `"product_id": 1` in material configuration objects
   - **Correct**: Should be `"material_id": 1` for material configurations
   - **Impact**: Developer confusion when implementing material management features

1. **Inconsistent Purchase UOM Examples**:

   - **Location**: Material creation and update endpoint documentation
   - **Error**: Examples show redundant purchase UOM conversion rates (e.g.,
     `purchase_uom: "kg"` with `purchase_uom_conversion_rate: 1.0`)
   - **Issue**: When purchase UOM equals inventory UOM, conversion rate should be
     null/omitted
   - **Correct Pattern**: `purchase_uom: null, purchase_uom_conversion_rate: null` when
     no conversion needed
   - **Impact**: Developers may implement unnecessary conversion logic

1. **Missing Conditional Requirements Documentation**:

   - **Location**: Material creation request documentation
   - **Gap**: Purchase UOM fields interdependency not clearly documented
   - **Business Rule**: `purchase_uom` and `purchase_uom_conversion_rate` must be
     provided together or both omitted
   - **Impact**: API integration errors due to incomplete validation requirements

1. **Field Constraint Inconsistencies**:

   - **Location**: Various material and variant endpoint examples
   - **Issue**: Documentation examples don't reflect actual field validation constraints
   - **Examples**:
     - `supplier_item_codes` constraints (1-40 characters per item) not documented
     - `registered_barcode` constraints (3-40 characters) not reflected in examples
     - `config_attributes` minimum requirements not specified
   - **Impact**: Client validation implementations may be too permissive or restrictive

**Validation Findings**:

- **OpenAPI Specification Accuracy**: Client's OpenAPI spec is more accurate than
  official documentation
- **Better Examples**: OpenAPI spec contains corrected examples that reflect actual API
  behavior
- **Proper Constraints**: OpenAPI spec includes comprehensive field validation that
  matches actual API requirements
- **Conditional Logic**: OpenAPI spec properly implements dependentRequired patterns for
  business rules

**Impact on Development**:

- **Integration Issues**: Developers following documentation examples may encounter API
  validation errors
- **Inconsistent Implementation**: Different teams may implement different
  interpretations
- **Support Burden**: Increased support requests due to documentation-reality mismatches
- **Development Velocity**: Slower development due to trial-and-error API integration

**Recommendation**:

- **Documentation Review**: Comprehensive audit of material endpoint documentation for
  accuracy
- **Example Correction**: Update all material configuration examples to use correct
  field names
- **Purchase UOM Clarity**: Clarify when purchase UOM conversion is needed vs. when to
  omit fields
- **Constraint Documentation**: Add comprehensive field validation documentation with
  examples
- **Cross-Validation**: Implement systematic validation between API implementation and
  documentation
- **Living Documentation**: Consider generating documentation from OpenAPI specification
  to ensure consistency

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

### Inconsistent Quantity Field Data Types

**Issue**: Quantity fields have inconsistent data types across different parts of the
API, mixing strings and numbers for similar concepts.

**Examples Found**:

**SalesReturnRow API Pattern**:

- **Main quantity field**: Returns string `"2.00"` (JSON string)
- **Batch transaction quantity**: Returns number `1` (JSON number)
- **Request schema**: Explicitly defines quantity as `type: "string"` in creation
  endpoints

**Evidence from API Documentation**:

- `POST /sales_return_rows` request schema: `"quantity": {"type": "string"}`
- `GET /sales_return_rows` response: `"quantity": "2.00"` (string)
- Same response, batch_transactions: `"quantity": 1` (number)

**Current Implementation Decision**:

- **Temporary Fix**: Updated OpenAPI schema to match API behavior (string type for main
  quantities)
- **Schema Updated**: SalesReturnRow.quantity changed to `type: string` with precision
  note

**Questions for Katana Team**:

1. **Design Intent**: Is the string format for main quantity fields intentional for
   decimal precision handling?

1. **Consistency Strategy**: Should all quantity fields across the API use consistent
   data types?

1. **Financial Precision**: Are string quantities specifically for financial/accounting
   precision vs. operational quantities?

1. **Future Direction**: Is this pattern expected to be standardized across other
   quantity fields in the API?

**Business Impact**:

- **Client Complexity**: Developers must handle mixed data types for similar concepts
- **Type Safety**: Generated clients may have inconsistent type definitions
- **Integration Confusion**: Unclear when to expect strings vs numbers for quantities

**Recommendation Options**:

1. **Standardize on Strings**: Use string format for all quantity fields (best for
   precision)
1. **Standardize on Numbers**: Use number format for all quantity fields (most common in
   APIs)
1. **Document Pattern**: Clearly document when to use strings vs numbers for different
   quantity types
1. **Hybrid Approach**: Use strings for financial quantities, numbers for operational
   quantities

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

### Missing Pagination Parameters on Collection Endpoints

**Issue**: Some collection endpoints that return arrays of resources lack standard
pagination parameters, making it difficult to handle large datasets efficiently.

**Affected Endpoints**:

- `GET /serial_numbers_stock` - Returns array but no `limit`, `page`, or `offset`
  parameters
- `GET /custom_fields_collections` - Returns array but no pagination parameters

**Current Behavior**:

- These endpoints return all results in a single response
- No way to paginate through large result sets
- Potentially inefficient for large datasets
- Inconsistent with other collection endpoints that do support pagination

**Verification**: Both endpoints confirmed to lack pagination parameters in the official
API specification (checked against comprehensive documentation).

**Business Impact**:

- **Performance**: Large result sets may cause slow API responses
- **Memory Usage**: Clients must handle potentially large JSON payloads
- **User Experience**: No progressive loading possible for large datasets
- **Consistency**: Inconsistent API behavior compared to other collection endpoints

**Expected Collection Endpoint Patterns**:

Most collection endpoints support:

- `limit` - Maximum number of results per page
- `page` - Page number for pagination
- `offset` - Alternative pagination method
- Response metadata with pagination info

**Recommendation**:

- **Add Pagination Support**: Implement standard pagination parameters for these
  endpoints
- **Consistent Parameters**: Use same pagination parameter names as other endpoints
- **Response Metadata**: Include pagination metadata in responses (`total_count`,
  `page_info`, etc.)
- **Backward Compatibility**: Ensure changes don't break existing clients
- **Documentation**: Update API documentation to reflect pagination capabilities

### Inconsistent 204 No Content Responses

**Issue**: Several endpoints return `204 No Content` where they should return created
resource data or success information with content.

**Affected Endpoints**:

- `POST /manufacturing_order_unlink` - Returns `204 No Content`
- `POST /purchase_order_receive` - Returns `204 No Content`
- `POST /unlink_variant_bin_locations` - Returns `204 No Content`
- `POST /recipes` - Returns `204 No Content`
- `POST /bom_rows` - Returns `204 No Content` (documented above)
- `POST /bom_rows/batch/create` - Returns `204 No Content` (documented above)
- `POST /product_operation_rows` - Returns `204 No Content`

**Current Behavior**:

- These creation/action endpoints return no response body
- Client cannot determine success details or created resource information
- Forces additional API calls to verify operation results

**Problems**:

- **No Confirmation Data**: Impossible to get created resource IDs or operation details
- **Integration Challenges**: Difficult to chain operations that depend on results
- **Non-Standard Pattern**: Most REST APIs return created resources with `201 Created`
- **User Experience**: No immediate feedback on operation success details

**Business Impact**:

- **Workflow Disruption**: Cannot build efficient automated workflows
- **Additional API Calls**: Forced to make extra requests to verify results
- **Development Complexity**: Harder to build reliable integrations
- **Inconsistent API**: Mixed patterns confuse developers

**Recommendation**:

- **Return Resource Data**: Provide created/modified resource information in response
  body
- **Use 201 Created**: For creation operations, return appropriate success status with
  data
- **Consistent Patterns**: Align all similar operations to return useful response data
- **Documentation**: Update examples to show expected response formats

### Parameter Naming Inconsistencies

**Issue**: Related endpoints use different parameter names for the same concepts,
creating confusion and integration complexity.

**Examples of Inconsistent Naming**:

- **ID Parameters**: Some endpoints use `customer_id` while related endpoints use
  `customer_ids` (array)
- **Resource Filters**: Mixed patterns like `sales_order_id` vs `sales_order_ids` for
  filtering
- **Date Ranges**: Inconsistent use of `created_at_min/max` vs other date range patterns
- **Status Filters**: Some endpoints have `status` parameters while related endpoints
  lack them

**Current Impact**:

- **Developer Confusion**: Must check each endpoint's parameters individually
- **Integration Complexity**: Cannot reuse parameter handling logic across similar
  endpoints
- **Documentation Overhead**: Requires extensive parameter documentation per endpoint
- **Client Generation Issues**: Generated clients may have inconsistent method
  signatures

**Business Impact**:

- **Development Time**: Slower integration development due to parameter inconsistencies
- **Error Prone**: Easy to use wrong parameter names when switching between endpoints
- **Maintenance Burden**: Harder to maintain consistent client code

**Recommendation**:

- **Standardize Parameter Names**: Establish consistent naming conventions for common
  parameters
- **Resource ID Patterns**: Use consistent patterns for single vs. multiple resource IDs
- **Date Range Conventions**: Standardize date filtering parameter names across all
  endpoints
- **Documentation**: Create parameter naming guidelines for future endpoints

### Response Schema Documentation via References

**Issue**: Many endpoint responses use `$ref` references to shared response schemas
without providing endpoint-specific context or descriptions.

**Current Pattern**:

```yaml
responses:
  "401":
    $ref: "#/components/responses/UnauthorizedError"
  "422":
    $ref: "#/components/responses/UnprocessableEntityError"
```

**Problems**:

- **No Endpoint Context**: Generic error responses don't explain endpoint-specific error
  conditions
- **Limited Debugging Info**: Developers can't understand what specific validations
  might fail
- **Poor Developer Experience**: No guidance on how to handle errors for specific
  operations
- **Documentation Gaps**: OpenAPI documentation tools show generic descriptions only

**Business Impact**:

- **Integration Difficulty**: Developers struggle to handle errors appropriately
- **Support Burden**: More support requests due to unclear error handling
- **Development Delays**: Time spent figuring out endpoint-specific error conditions

**Recommendation**:

- **Add Endpoint-Specific Descriptions**: Provide context for how shared responses apply
  to each endpoint
- **Error Condition Examples**: Document specific validation failures for each endpoint
- **Hybrid Approach**: Use `$ref` for consistency but add endpoint-specific descriptions
- **Documentation**: Enhance error handling examples in API documentation

### Inconsistent Resource Pattern - Factory Endpoint

**Issue**: The `/factory` endpoint follows a singleton pattern that differs from other
resource endpoints, potentially causing confusion.

**Current Behavior**:

- `GET /factory` - Returns factory information (singleton resource)
- No `/factories` (plural) endpoint
- No individual factory ID-based endpoints like `/factories/{id}`

**Pattern Comparison**:

```yaml
# Standard Collection Pattern:
GET /customers      # List all customers
GET /customers/{id} # Get specific customer

# Factory Singleton Pattern:
GET /factory        # Get factory info (no collection)
```

**Potential Issues**:

- **Developer Expectations**: Most REST APIs use consistent collection patterns
- **Client Generation**: Code generators may handle singleton differently
- **Documentation Clarity**: Pattern inconsistency requires special documentation
- **Future Scaling**: Unclear how pattern would extend if multiple factories supported

**Current Assessment**: This appears to be a legitimate business requirement (single
factory per account), but the pattern inconsistency should be documented.

**Recommendation**:

- **Document Pattern**: Clearly explain why `/factory` uses singleton pattern
- **API Guidelines**: Document when singleton vs. collection patterns are appropriate
- **Client Examples**: Provide specific examples for singleton resource usage
- **Future Planning**: Consider how pattern would evolve for multi-factory scenarios

______________________________________________________________________

## 🟠 Schema Validation Discrepancies

### Mixed Amount Field Data Types Across API

**Issue**: The Katana API uses inconsistent data types for monetary amount fields,
mixing strings and numbers across different endpoints and contexts.

**Validation Source**: Comprehensive schema validation performed August 29, 2025,
comparing external API examples against actual API responses and our OpenAPI 3.1
specification.

#### Confirmed Actual API Behavior (From Real Response Data)

**Shipping Fee Amounts - Always Strings**:

```json
// Actual API Response - shipping_fee objects
"shipping_fee": {
  "id": 4933554,
  "sales_order_id": 33066353,
  "description": "Shipping",
  "amount": "7.8500000000",    // STRING with 10 decimal places
  "tax_rate_id": 402909
}
```

**Sales Order Row Amounts - Always Strings**:

```json
// Actual API Response - sales_order_rows objects
"sales_order_rows": [{
  "price_per_unit": "4599.0000000000",      // STRING with 10 decimal places
  "total_discount": "0.0000000000",         // STRING with 10 decimal places
  "price_per_unit_in_base_currency": 4599,  // NUMBER (integer)
  "total": 4599,                           // NUMBER (integer)
  "total_in_base_currency": 4599           // NUMBER (integer)
}]
```

**Sales Order Main Amounts - Always Numbers**:

```json
// Actual API Response - sales order object
{
  "total": 4943.925,                    // NUMBER (decimal)
  "total_in_base_currency": 4943.925,   // NUMBER (decimal)
  "conversion_rate": 1                  // NUMBER (integer)
}
```

#### External Validation Example Discrepancies

**Problem**: External validation examples (from downloaded API spec) show **numeric
values** (`3.14`, `0`) for shipping fee amounts, but **actual API consistently returns
string values** like `"7.8500000000"`.

**Schema Decision**: Our OpenAPI specification correctly uses `type: string` for
`SalesOrderShippingFee.amount` to match actual API behavior.

#### Current Validation Errors (6 remaining)

These validation errors occur because external validation examples don't match actual
API format:

1. **bin_locations** - External data uses `name` vs our schema expects `bin_name` ✅
   **Our schema correct**
1. **manufacturing_order_operation_rows** - External data wrapped in response objects vs
   direct objects ✅ **Our schema correct**
1. **sales_order_shipping_fee endpoints** - External examples show numbers (`3.14`) vs
   actual API strings (`"7.8500000000"`) ✅ **Our schema correct**
1. **stock_transfers status** - External data wrapped in response objects vs direct
   objects ✅ **Our schema correct**

#### Impact on Client Development

**Positive**: Our OpenAPI schema accurately reflects actual API behavior

- ✅ Generated clients correctly handle string amounts for shipping fees
- ✅ Generated clients correctly handle number amounts for order totals
- ✅ Type safety matches real API responses

**Complexity**: Developers must handle mixed data types

- Mixed string/number amounts require careful client-side handling
- Financial calculations need decimal precision considerations
- Different serialization patterns across related endpoints

#### Questions for Katana Team

1. **Design Rationale**: Is the string format intentional for high-precision monetary
   fields (`price_per_unit`, `amount`)?

1. **Precision Requirements**: Are 10-decimal-place strings needed for accounting
   precision vs standard 2-decimal currency handling?

1. **Consistency Strategy**: Would standardizing on either all-string or all-number
   amounts be considered for future API versions?

1. **External Examples**: Can the external validation examples be updated to match
   actual API behavior?

#### Recommendations

**For Katana API Team**:

- **Documentation**: Clearly document the mixed data type strategy and precision
  requirements
- **Validation Examples**: Update external API examples to match actual API response
  formats
- **Consistency**: Consider long-term strategy for amount field data types across all
  endpoints

**For Client Developers**:

- Our OpenAPI specification correctly handles the actual API behavior
- Use string-based decimal libraries for financial calculations involving
  `price_per_unit` and shipping `amount` fields
- Handle mixed types appropriately in client applications

### Storage Bin Field Name Discrepancy

**Issue**: External validation examples use `name` field while actual API specification
expects `bin_name`.

**Status**: ✅ **Our schema is correct** - this is an external example data issue, not a
schema problem.

**Details**: Our StorageBin schema correctly requires `bin_name` field, matching the
actual API specification and business logic.

### Manufacturing Order Operation Response Structure

**Issue**: External validation examples wrap response data in container objects while
our schema expects direct object responses.

**Status**: ✅ **Our schema is correct** - this reflects proper REST API response
structure expectations.

**Details**: Our ManufacturingOrderOperationRow schema correctly expects direct object
responses with `id` as a required property, not wrapped in additional container objects.

### Stock Transfer Status Response Structure

**Issue**: External validation examples wrap response data in `example` container
objects while our schema expects direct StockTransfer objects.

**Status**: ✅ **Our schema is correct** - this matches standard REST API response
patterns.

**Details**: Our StockTransfer schema correctly expects direct object responses with
proper required fields, not wrapped in additional container structures.
