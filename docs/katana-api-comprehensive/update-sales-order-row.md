# Update a sales order row

**PATCH** `https://api.katanamrp.com/v1/sales_order_rows/{id}`

Update a sales order row

## API Specification Details

**Summary:** Update a sales order row **Description:** Updates the specified sales order
row by setting the values of the parameters passed. Any parameters not provided will be
left unchanged.

### Parameters

- **id** (path) *required*: Sales order row id

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "quantity": {
      "type": "number",
      "maximum": 100000000000000000,
      "description": "Updatable only when sales order row status is NOT_SHIPPED or PENDING."
    },
    "variant_id": {
      "type": "integer",
      "description": "Updatable only when sales order row status is NOT_SHIPPED or PENDING."
    },
    "tax_rate_id": {
      "type": "integer",
      "description": "Updatable only when sales order row status is NOT_SHIPPED or PENDING."
    },
    "location_id": {
      "type": "integer",
      "description": "Updatable only when sales order row status is NOT_SHIPPED or PENDING and sales order row is not linked to a manufacturing order (linked_manufacturing_order_id is null)."
    },
    "price_per_unit": {
      "type": "number",
      "maximum": 1000000000000000000,
      "description": "Updatable only when sales order row status is NOT_SHIPPED or PENDING."
    },
    "total_discount": {
      "type": "number",
      "maximum": 1000000000000000000,
      "description": "Updatable only when sales order row status is NOT_SHIPPED or PENDING."
    },
    "batch_transactions": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "quantity": {
            "maximum": 100000000000000000,
            "type": "number"
          },
          "batch_id": {
            "type": "integer"
          }
        }
      }
    },
    "serial_number_transactions": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "quantity": {
            "maximum": 1,
            "minimum": 0,
            "type": "number"
          },
          "serial_number_id": {
            "type": "integer"
          }
        }
      }
    },
    "attributes": {
      "type": "array",
      "description": "When updating attributes, all keys and values must be provided.\n      Existing ones are replaced with new attributes.",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "key": {
            "type": "string"
          },
          "value": {
            "type": "string"
          }
        }
      }
    }
  }
}
```

### Response Examples

#### 200 Response

Sales order row updated

```json
{
  "sales_order_id": 1,
  "id": 1,
  "quantity": 2,
  "variant_id": 1,
  "tax_rate_id": 1,
  "location_id": 1,
  "price_per_unit": 150,
  "total_discount": "10.00",
  "created_at": "2020-10-23T10:37:05.085Z",
  "updated_at": "2020-10-23T10:37:05.085Z",
  "deleted_at": null,
  "linked_manufacturing_order_id": 1,
  "attributes": [
    {
      "key": "key",
      "value": "value"
    }
  ],
  "batch_transactions": [
    {
      "batch_id": 1,
      "quantity": 10
    }
  ],
  "serial_numbers": [
    1
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
