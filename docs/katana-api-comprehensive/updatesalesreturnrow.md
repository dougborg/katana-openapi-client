# Update a sales return row

**PATCH** `https://api.katanamrp.com/v1/sales_return_rows/{id}`

Update a sales return row

## API Specification Details

**Summary:** Update a sales return row **Description:** Updates the specified sales
return row by setting the values of the parameters passed. Any parameters not provided
will be left unchanged.

### Parameters

- **id** (path) *required*: Sales return row id

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "quantity": {
      "type": "string",
      "description": "New quantity of the sales return row.
      Updatable only when current return status is NOT_RETURNED.",
      "nullable": false
    },
    "restock_location_id": {
      "type": "integer",
      "description": "Restock location id.
      Updatable only when current return status is NOT_RETURNED or RETURNED.",
      "maximum": 2147483647
    },
    "reason_id": {
      "type": "integer",
      "description": "Reason id.
      Updatable only when current return status is NOT_RETURNED.",
      "maximum": 2147483647
    },
    "batch_transactions": {
      "type": "array",
      "description": "Batch transactions.
      Updatable only when current return status is NOT_RETURNED or RETURNED.",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": [
          "batch_id",
          "quantity"
        ],
        "properties": {
          "batch_id": {
            "type": "integer",
            "description": "Batch id",
            "maximum": 2147483647
          },
          "quantity": {
            "type": "number",
            "description": "Quantity",
            "maximum": 100000000000000000
          }
        }
      }
    }
  }
}
```

### Response Examples

#### 200 Response

Sales return row updated

```json
{
  "id": 764,
  "sales_return_id": 1147,
  "variant_id": 19789420,
  "fulfillment_row_id": 30048990,
  "sales_order_row_id": 41899179,
  "quantity": "2.00",
  "net_price_per_unit": "2.0000000000",
  "reason_id": 123,
  "restock_location_id": 26331,
  "batch_transactions": [
    {
      "batch_id": 2288104,
      "quantity": 1
    }
  ],
  "created_at": "2025-02-07T07:51:27.145Z",
  "updated_at": "2025-02-07T07:51:27.145Z"
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

#### 404 Response

Make sure data is correct

```json
{
  "statusCode": 404,
  "name": "NotFoundError",
  "message": "Not found"
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
