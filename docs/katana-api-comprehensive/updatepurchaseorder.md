# Update a purchase order

**PATCH** `https://api.katanamrp.com/v1/purchase_orders/{id}`

Update a purchase order

## API Specification Details

**Summary:** Update a purchase order **Description:** Updates the specified purchase
order by setting the values of the parameters passed. Any parameters not provided will
be left unchanged.

### Parameters

- **id** (path) *required*: Purchase order id

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "order_no": {
      "type": "string",
      "minLength": 3,
      "description": "Updatable only when status is in NOT_RECEIVED and PARTIALLY_RECEIVED"
    },
    "supplier_id": {
      "type": "integer",
      "maximum": 2147483647,
      "description": "Updatable only when status is in NOT_RECEIVED"
    },
    "currency": {
      "type": "string",
      "description": "Updatable only when status is in NOT_RECEIVED"
    },
    "tracking_location_id": {
      "type": "string",
      "maximum": 2147483647,
      "description": "Updatable only when status is in NOT_RECEIVED and\n        entity_type is outsourced"
    },
    "status": {
      "type": "string",
      "enum": [
        "NOT_RECEIVED",
        "RECEIVED",
        "PARTIALLY_RECEIVED"
      ]
    },
    "expected_arrival_date": {
      "type": "string",
      "description": "Updatable only when status is in NOT_RECEIVED and PARTIALLY_RECEIVED.
      Update will override arrival_date on purchase order rows"
    },
    "order_created_date": {
      "type": "string"
    },
    "location_id": {
      "type": "integer",
      "maximum": 2147483647,
      "description": "Updatable only when status is in NOT_RECEIVED"
    },
    "additional_info": {
      "type": "string"
    }
  }
}
```

### Response Examples

#### 200 Response

Purchase order updated

```json
{
  "id": 1,
  "status": "NOT_RECEIVED",
  "billing_status": "NOT_BILLED",
  "last_document_status": "NOT_SENT",
  "order_no": "PO-1",
  "entity_type": "regular",
  "default_group_id": 9,
  "supplier_id": 1,
  "currency": "USD",
  "expected_arrival_date": "2021-10-13T15:31:48.490Z",
  "order_created_date": "2021-10-13T15:31:48.490Z",
  "additional_info": "Please unpack",
  "location_id": 1,
  "tracking_location_id": null,
  "total": 1,
  "total_in_base_currency": 1,
  "created_at": "2021-02-03T13:13:07.110Z",
  "updated_at": "2021-02-03T13:13:07.110Z",
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
