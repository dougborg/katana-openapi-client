# Update a stock adjustment

**PATCH** `https://api.katanamrp.com/v1/stock_adjustments/{id}`

Update a stock adjustment

## API Specification Details

**Summary:** Update a stock adjustment **Description:** Updates the specified stock
adjustment by setting the values of the parameters passed. Any parameters not provided
will be left unchanged.

### Parameters

- **id** (path) *required*: Stock adjustment id

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "stock_adjustment_number": {
      "type": "string",
      "minLength": 1
    },
    "stock_adjustment_date": {
      "type": "string",
      "minLength": 1
    },
    "location_id": {
      "type": "integer",
      "maximum": 2147483647
    },
    "reason": {
      "type": "string"
    },
    "additional_info": {
      "type": "string",
      "nullable": true
    }
  }
}
```

### Response Examples

#### 200 Response

Stock adjustment updated

```json
{
  "id": 1,
  "stock_adjustment_number": "SA-1",
  "stock_adjustment_date": "2021-10-06T11:47:13.846Z",
  "location_id": 1,
  "reason": "adjustment reason",
  "additional_info": "adjustment additional info",
  "created_at": "2021-10-06T11:47:13.846Z",
  "updated_at": "2021-10-06T11:47:13.846Z",
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
