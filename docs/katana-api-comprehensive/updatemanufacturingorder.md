# Update a manufacturing order

**PATCH** `https://api.katanamrp.com/v1/manufacturing_orders/{id}`

Update a manufacturing order

## API Specification Details

**Summary:** Update a manufacturing order **Description:** Updates the specified
manufacturing order by setting the values of the parameters passed. Any parameters not
provided will be left unchanged.

### Parameters

- **id** (path) *required*: manufacturing order id

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "status": {
      "type": "string",
      "enum": [
        "NOT_STARTED",
        "BLOCKED",
        "IN_PROGRESS",
        "DONE"
      ],
      "description": "Not updatable when manufacturing order status is DONE and location is deleted\n      or manufacturing_allowed is false."
    },
    "order_no": {
      "type": "string",
      "description": "Not updatable when manufacturing order status is DONE."
    },
    "variant_id": {
      "type": "number",
      "description": "Not updatable when manufacturing order status is DONE."
    },
    "location_id": {
      "type": "number",
      "description": "Not updatable when manufacturing order status is DONE."
    },
    "planned_quantity": {
      "type": "number",
      "description": "Not updatable when manufacturing order status is DONE."
    },
    "actual_quantity": {
      "type": "number",
      "description": "Not updatable when manufacturing order status is DONE."
    },
    "order_created_date": {
      "type": "string"
    },
    "production_deadline_date": {
      "type": "string",
      "description": "Use only if automatic production deadline calculation for the factory location is switched OFF.\n      Not updatable when manufacturing order status is DONE.\n Not updatable when manufacturing order status is DONE."
    },
    "additional_info": {
      "type": "string"
    },
    "done_date": {
      "type": "string"
    },
    "batch_transactions": {
      "type": "array",
      "description": "Not updatable when manufacturing order status is DONE.",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "quantity": {
            "maximum": 1000000000000000,
            "type": "number"
          },
          "batch_id": {
            "type": "integer"
          }
        }
      }
    }
  }
}
```

### Response Examples

#### 200 Response

New manufacturing order

```json
{
  "id": 21400,
  "status": "NOT_STARTED",
  "order_no": "SO-2 / 1",
  "variant_id": 1418016,
  "planned_quantity": 1,
  "actual_quantity": null,
  "batch_transactions": [],
  "location_id": 2327,
  "order_created_date": "2021-09-01T07:49:29.000Z",
  "done_date": null,
  "production_deadline_date": "2021-10-18T08:00:00.000Z",
  "additional_info": "",
  "is_linked_to_sales_order": true,
  "ingredient_availability": "IN_STOCK",
  "total_cost": 0,
  "total_actual_time": 0,
  "total_planned_time": 18000,
  "sales_order_id": 1,
  "sales_order_row_id": 1,
  "sales_order_delivery_deadline": "2021-09-01T07:49:29.813Z",
  "material_cost": 10,
  "created_at": "2021-09-01T07:49:29.813Z",
  "updated_at": "2021-10-15T14:05:47.625Z",
  "subassemblies_cost": 10,
  "operations_cost": 10,
  "deleted_at": null,
  "serial_numbers": [
    {
      "id": 1,
      "transaction_id": "eb4da756-0842-4495-9118-f8135f681234",
      "serial_number": "SN1",
      "resource_type": "Production",
      "resource_id": 2,
      "transaction_date": "2023-02-10T10:06:14.435Z"
    }
  ]
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
