# Update a stocktake

**PATCH** `https://api.katanamrp.com/v1/stocktakes/{id}`

## API Specification Details

**Summary:** Update a stocktake **Description:** Updates the specified stocktake by
setting the values of the parameters passed. Any parameters not provided will be left
unchanged. Status updates can take a long time so 204 is returned. If you need to
continue with updates on same entity or its rows, you need to poll if status update has
ended (status_update_in_progress) and continue after that.

### Parameters

- **id** (path) *required*: Stocktake id

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "stocktake_number": {
      "type": "string",
      "minLength": 1
    },
    "location_id": {
      "type": "integer",
      "maximum": 2147483647
    },
    "status": {
      "type": "string",
      "enum": [
        "NOT_STARTED",
        "IN_PROGRESS",
        "COUNTED",
        "COMPLETED"
      ]
    },
    "reason": {
      "type": "string",
      "maxLength": 540,
      "nullable": true
    },
    "additional_info": {
      "type": "string",
      "nullable": true
    },
    "created_date": {
      "type": "string",
      "minLength": 1
    },
    "completed_date": {
      "type": "string",
      "minLength": 1,
      "nullable": true
    },
    "set_remaining_items_as_counted": {
      "type": "boolean",
      "default": false
    }
  }
}
```

### Response Examples

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
