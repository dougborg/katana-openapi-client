# Update a price list

**PATCH** `https://api.katanamrp.com/v1/price_lists/{id}`

## API Specification Details

**Summary:** Update a price list **Description:** Updates the specified price list by
setting the values of the parameters passed. Any parameters not provided will be left
unchanged.

### Parameters

- **id** (path) *required*: Price list ID

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string",
      "description": "Price list name",
      "minLength": 1,
      "maxLength": 100
    },
    "is_active": {
      "type": "boolean",
      "description": "Price list status"
    }
  }
}
```

### Response Examples

#### 200 Response

Price list updated

```json
{
  "id": 1,
  "name": "Platinum customers price list",
  "is_active": true,
  "created_at": "2020-10-23T10:37:05.085Z",
  "updated_at": "2020-10-23T10:37:05.085Z"
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
