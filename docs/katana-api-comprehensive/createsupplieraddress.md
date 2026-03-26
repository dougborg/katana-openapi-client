# Create a supplier address

**POST** `https://api.katanamrp.com/v1/supplier_addresses`

Create a supplier address

## API Specification Details

**Summary:** Create a supplier address **Description:** Add an address to an existing
supplier. If the new address is the first one, it is assigned as the default. (A
Supplier can have only one address for now)

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "supplier_id"
  ],
  "properties": {
    "supplier_id": {
      "type": "integer",
      "nullable": false
    },
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

New supplier address created

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
