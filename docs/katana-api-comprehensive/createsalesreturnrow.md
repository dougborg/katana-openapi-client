# Create a sales return row

**POST** `https://api.katanamrp.com/v1/sales_return_rows`

Create a sales return row

## API Specification Details

**Summary:** Create a sales return row **Description:** Creates a new sales return row
object.

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "sales_return_id",
    "variant_id",
    "fulfillment_row_id",
    "quantity"
  ],
  "properties": {
    "sales_return_id": {
      "type": "integer",
      "description": "Sales return id",
      "maximum": 2147483647
    },
    "variant_id": {
      "type": "integer",
      "description": "Variant id",
      "maximum": 2147483647
    },
    "fulfillment_row_id": {
      "type": "integer",
      "description": "Fulfillment row id",
      "maximum": 2147483647
    },
    "quantity": {
      "type": "string",
      "description": "Quantity",
      "nullable": false
    },
    "restock_location_id": {
      "type": "integer",
      "description": "Restock location id.
      If missing then default from sales order fulfillment row will be used.",
      "maximum": 2147483647
    },
    "reason_id": {
      "type": "integer",
      "description": "Reason id",
      "maximum": 2147483647
    }
  }
}
```

### Response Examples

#### 200 Response

New sales return row created

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
