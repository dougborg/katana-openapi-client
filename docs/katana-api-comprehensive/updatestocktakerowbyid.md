# Update a stocktake row

**PATCH** `https://api.katanamrp.com/v1/stocktake_rows/{id}`

Update a stocktake row

## API Specification Details

**Summary:** Update a stocktake row **Description:** Updates the specified stocktake row
by setting the values of the parameters passed. Any parameters not provided will be left
unchanged.

### Parameters

- **id** (path) *required*: Stocktake row id

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "variant_id": {
      "type": "integer",
      "maximum": 2147483647
    },
    "batch_id": {
      "type": "integer",
      "maximum": 2147483647,
      "nullable": true
    },
    "notes": {
      "type": "string",
      "nullable": true,
      "maxLength": 540
    },
    "counted_quantity": {
      "type": "number",
      "minimum": 0,
      "nullable": true
    }
  }
}
```

### Response Examples

#### 200 Response

Updated stocktake row

```json
{
  "id": 90,
  "variant_id": 21002,
  "batch_id": null,
  "stocktake_id": 2,
  "notes": "test 2",
  "in_stock_quantity": null,
  "counted_quantity": 21,
  "discrepancy_quantity": null,
  "created_at": "2022-01-13T14:30:18.174Z",
  "updated_at": "2022-01-13T14:30:18.174Z",
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
