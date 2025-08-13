# Create a manufacturing order operation row

**POST** `https://api.katanamrp.com/v1/manufacturing_order_operation_rows`

Create a manufacturing order operation row

## API Specification Details

**Summary:** Create a manufacturing order operation row **Description:** Add an
operation row to an existing manufacturing order. Operation rows cannot be added when
the manufacturing order status is DONE.

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "manufacturing_order_id",
    "status"
  ],
  "properties": {
    "manufacturing_order_id": {
      "type": "number"
    },
    "operation_id": {
      "type": "number",
      "description": "If operation ID is used to map the operation, then operation_name is ignored."
    },
    "type": {
      "type": "string",
      "enum": [
        "process",
        "setup",
        "perUnit",
        "fixed"
      ],
      "description": "Different operation types allows you to use different cost calculations depending on the type of product operation<br/>\n        Process: The process operation type is best for when products are individually built and time is the main driver of cost.<br/>\n        Setup: The setup operation type is best for setting up a machine for production where the production quantity doesn't affect cost.<br/>\n        Per unit: The per unit operation type is best when cost of time isn't a factor, but only the quantity of product made.<br/>\n        Fixed cost: The fixed cost operation type is useful for adding the expected extra costs that go into producing a product.\n       "
    },
    "operation_name": {
      "type": "string",
      "description": "If operation name is used to map the operation then we match to the existing operations by name.\n        If a match is not found, a new one is created."
    },
    "resource_id": {
      "type": "number",
      "description": "If resource ID is used to map the resource, then resource_name is ignored."
    },
    "resource_name": {
      "type": "string",
      "description": "If resource name is used to map the resource then we match to the existing resources by name.\n        If a match is not found, a new one is created."
    },
    "planned_time_parameter": {
      "type": "number",
      "maximum": 10000000000000000,
      "description": "The planned duration of an operation, in seconds, to either manufacture one unit of a product or\n        complete a manufacturing order (based on type).\n      "
    },
    "planned_time_per_unit": {
      "type": "number",
      "maximum": 10000000000000000,
      "deprecated": true,
      "description": "(This field is deprecated in favor of planned_time_parameter)\n        The planned duration of an operation, in seconds, to either manufacture one unit of a product or\n         complete a manufacturing order (based on type)\n      "
    },
    "cost_parameter": {
      "type": "number",
      "description": "The expected cost of an operation, either total or per hour/unit of product (based on type).<br/>\n        Total cost of the operation on a manufacturing order is calculated as follows:<br/>\n        process: cost = cost_parameter x planned_time_parameter (in hours) x product quantity<br/>\n        setup: cost = cost_parameter x planned_time_parameter (in hours)<br/>\n        perUnit: cost = cost_parameter x product quantity <br/>\n        fixed: cost = cost_parameter\n      "
    },
    "cost_per_hour": {
      "type": "number",
      "deprecated": true,
      "description": "(This field is deprecated in favor of cost_parameter)\n        The expected cost of an operation, either total or per hour/unit of product (based on type).<br/>\n        Total cost of the operation on a manufacturing order is calculated as follows:<br/>\n        process: cost = cost_parameter x planned_time_parameter (in hours) x product quantity<br/>\n        setup: cost = cost_parameter x planned_time_parameter (in hours)<br/>\n        perUnit: cost = cost_parameter x product quantity<br/>\n        fixed: cost = cost_parameter\n      "
    },
    "status": {
      "type": "string",
      "enum": [
        "NOT_STARTED"
      ]
    },
    "assigned_operators": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "operator_id": {
            "type": "number",
            "description": "If operator ID is used to map the operator, then name is ignored."
          },
          "name": {
            "type": "string",
            "description": "If operator name is used to map the operator then we match to the existing operators by name."
          }
        }
      }
    }
  }
}
```

### Response Examples

#### 200 Response

New manufacturing order operation row

```json
{
  "id": 1,
  "status": "IN_PROGRESS",
  "type": "process",
  "rank": 1,
  "manufacturing_order_id": 1,
  "operation_id": 1,
  "operation_name": "Pack",
  "resource_id": 1,
  "resource_name": "Table",
  "assigned_operators": [
    {
      "operator_id": 1,
      "name": "Pack",
      "deleted_at": null
    }
  ],
  "completed_by_operators": [],
  "active_operator_id": 1,
  "planned_time_per_unit": 1,
  "planned_time_parameter": 1,
  "total_actual_time": 1,
  "planned_cost_per_unit": 1,
  "total_actual_cost": 1,
  "cost_per_hour": 1,
  "cost_parameter": 1,
  "group_boundary": 1000,
  "is_status_actionable": true,
  "completed_at": "2020-10-23T10:37:05.085Z",
  "created_at": "2020-10-23T10:37:05.085Z",
  "updated_at": "2020-10-23T10:37:05.085Z",
  "deleted_at": null
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
