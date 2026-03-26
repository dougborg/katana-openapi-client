# Create a sales return

**POST** `https://api.katanamrp.com/v1/sales_returns`

Create a sales return

## API Specification Details

**Summary:** Create a sales return **Description:** Creates a new sales return object.

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "sales_order_id",
    "return_location_id"
  ],
  "properties": {
    "sales_order_id": {
      "type": "integer"
    },
    "order_created_date": {
      "type": "string",
      "description": "Creation date of the return.
      Must be compatible with ISO 8601 format.
      If missing then current timestamp will be used."
    },
    "return_location_id": {
      "type": "integer",
      "maximum": 2147483647
    },
    "order_no": {
      "type": "string",
      "description": "Return order number."
    },
    "additional_info": {
      "type": "string",
      "description": "Additional information about the return."
    }
  }
}
```

### Response Examples

#### 200 Response

New sales return created

```json
{
  "id": 1148,
  "customer_id": 52910306,
  "sales_order_id": 26857265,
  "order_no": "RO-6",
  "return_location_id": 26331,
  "status": "RESTOCKED_ALL",
  "currency": "EUR",
  "return_date": "2025-02-20T11:05:56.738Z",
  "order_created_date": "2025-02-07T07:52:41.237Z",
  "additional_info": "",
  "refund_status": "NOT_REFUNDED",
  "created_at": "2025-02-07T07:52:41.395Z",
  "updated_at": "2025-02-20T11:05:56.753Z"
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
