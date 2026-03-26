# Update stock transfers status

**PATCH** `https://api.katanamrp.com/v1/stock_transfers/{id}/status`

Update stock transfers status

## API Specification Details

**Summary:** Update stock transfers status **Description:** Updates the specified stock
transfers status.

### Parameters

- **id** (path) *required*: Stock transfer id

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "status": {
      "type": "string",
      "enum": [
        "received",
        "created"
      ]
    }
  }
}
```

### Response Examples

#### 200 Response

Stock transfer status updated

```json
{
  "example": {
    "id": 1,
    "stock_transfer_number": "ST-1",
    "source_location_id": 1,
    "target_location_id": 2,
    "status": "received",
    "transfer_date": "2020-10-23T10:37:05.085Z",
    "order_created_date": "2021-10-01T11:47:13.846Z",
    "expected_arrival_date": "2021-10-20T11:47:13.846Z",
    "additional_info": "transfer additional info",
    "stock_transfer_rows": [
      {
        "variant_id": 1,
        "quantity": 3,
        "cost_per_unit": 10,
        "batch_transactions": [
          {
            "batch_id": 1,
            "quantity": 3
          }
        ],
        "deleted_at": null
      }
    ],
    "created_at": "2020-10-23T10:37:05.085Z",
    "updated_at": "2020-10-23T10:37:05.085Z",
    "deleted_at": null
  }
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
