# Update a product operation row

**PATCH** `https://api.katanamrp.com/v1/product_operation_rows/{id}`

Update a product operation row

## API Specification Details

**Summary:** Update a product operation row **Description:** Updates the specified
product operation row by setting the values of the parameters passed. Any parameters not
provided will be left unchanged. Since one product operation row can apply to multiple
product variants, updating the row will apply to all objects with the same
product_operation_row_id.

### Parameters

- **id** (path) *required*: Product operation row id

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "operation_id": {
      "description": "If operation ID is used to map the operation, then operation_name is ignored.",
      "type": "integer"
    },
    "operation_name": {
      "description": "If operation name is used to map the operation then we match to the existing operations by name.\n        If a match is not found, a new one is created.",
      "type": "string"
    },
    "resource_id": {
      "description": "If resource ID is used to map the resource, then resource_name is ignored.",
      "type": "integer"
    },
    "resource_name": {
      "description": "If resource name is used to map the resource then we match to the existing resources by name.\n        If a match is not found, a new one is created.",
      "type": "string"
    },
    "type": {
      "type": "string",
      "description": "Different operation types allows you to use different cost calculations depending on the type of product operation<br/>\n        Process: The process operation type is best for when products are individually built and time is the main driver of cost.<br/>\n        Setup: The setup operation type is best for setting up a machine for production where the production quantity doesn't affect cost.<br/>\n        Per unit: The per unit operation type is best when cost of time isn't a factor, but only the quantity of product made.<br/>\n        Fixed cost: The fixed cost operation type is useful for adding the expected extra costs that go into producing a product.\n      ",
      "enum": [
        "process",
        "setup",
        "perUnit",
        "fixed"
      ]
    },
    "cost_parameter": {
      "type": "number",
      "description": "The expected cost of an operation, either total or per hour/unit of product (based on type).
      Total cost of the operation on a manufacturing order is calculated as follows:<br/>\n        process: cost = cost_parameter x planned_time_parameter (in hours) x product quantity<br/>\n        setup: cost = cost_parameter x planned_time_parameter (in hours)<br/>\n        perUnit: cost = cost_parameter x product quantity<br/>\n        fixed: cost = cost_parameter\n      ",
      "maximum": 1000000000000000000,
      "minimum": 0
    },
    "cost_per_hour": {
      "type": "number",
      "deprecated": true,
      "description": "(This field is deprecated in favor of cost_parameter) The expected cost of an operation, either total or per hour/unit of product (based on type).
      Total cost of the operation on a manufacturing order is calculated as follows:<br/>\n        process: cost = cost_parameter x planned_time_parameter (in hours) x product quantity<br/>\n        setup: cost = cost_parameter x planned_time_parameter (in hours)<br/>\n        perUnit: cost = cost_parameter x product quantity<br/>\n        fixed: cost = cost_parameter\n      ",
      "minimum": 0
    },
    "planned_time_parameter": {
      "type": "integer",
      "description": "The planned duration of an operation, in seconds, to either manufacture one unit of a product or complete a manufacturing order (based on type).",
      "maximum": 2147483647,
      "minimum": 0
    },
    "planned_time_per_unit": {
      "type": "number",
      "deprecated": true,
      "description": "(This field is deprecated in favor of planned_time_parameter) The planned duration of an operation, in seconds, to either manufacture one unit of a product or complete a manufacturing order (based on type).",
      "minimum": 0
    }
  }
}
```

### Response Examples

#### 200 Response

Product operation row updated

```json
{
  "product_id": 1,
  "product_operation_row_id": 1,
  "product_variant_id": 1,
  "operation_id": 1,
  "operation_name": "Assembly",
  "resource_id": 1,
  "resource_name": "Station #1",
  "type": "process",
  "cost_per_hour": 15,
  "cost_parameter": 15,
  "planned_cost_per_unit": 30,
  "planned_time_per_unit": 7200,
  "planned_time_parameter": 7200,
  "rank": 1000,
  "created_at": "2021-04-05T12:00:00.000Z",
  "updated_at": "2021-04-05T12:00:00.000Z"
}
```

#### 401 Response

Make sure you've entered your API token correctly.

```json
{
  "statusCode": 401,
  "name": "UnauthorizedError",
  "message": "Unauthorized"
}
```

#### 422 Response

Check the details property for a specific error message.

```json
{
  "statusCode": 422,
  "name": "UnprocessableEntityError",
  "message": "The request body is invalid.
  See error object `details` property for more info.",
  "code": "VALIDATION_FAILED",
  "details": [
    {
      "path": ".name",
      "code": "maxLength",
      "message": "should NOT be longer than 10 characters",
      "info": {
        "limit": 10
      }
    }
  ]
}
```

#### 429 Response

The rate limit has been reached. Please try again later.

```json
{
  "statusCode": 429,
  "name": "TooManyRequests",
  "message": "Too Many Requests"
}
```

#### 500 Response

The server encountered an error. If this persists, please contact support

```json
{
  "statusCode": 500,
  "name": "InternalServerError",
  "message": "Internal Server Error"
}
```
