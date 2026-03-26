# Update a supplier address

**PATCH** `https://api.katanamrp.com/v1/supplier_addresses/{id}`

Update a supplier address

## API Specification Details

**Summary:** Update a supplier address **Description:** Updates the specified supplier
address by setting the values of the parameters passed. Any parameters not provided will
be left unchanged.

### Parameters

- **id** (path) *required*: Supplier address id

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "line_1": {
      "type": "string",
      "nullable": true
    },
    "line_2": {
      "type": "string",
      "nullable": true
    },
    "city": {
      "type": "string",
      "nullable": true
    },
    "state": {
      "type": "string",
      "nullable": true
    },
    "zip": {
      "type": "string",
      "nullable": true
    },
    "country": {
      "type": "string",
      "nullable": true
    }
  }
}
```

### Response Examples

#### 200 Response

Supplier address updated

```json
{
  "id": 2,
  "supplier_id": 12345,
  "line_1": "Line 1",
  "line_2": "Line 2",
  "city": "City",
  "state": "State",
  "zip": "Zip",
  "country": "Country",
  "updated_at": "2020-10-23T10:37:05.085Z",
  "created_at": "2020-10-23T10:37:05.085Z"
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
