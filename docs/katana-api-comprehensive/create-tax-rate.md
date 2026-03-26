# Create a tax rate

**POST** `https://api.katanamrp.com/v1/tax_rates`

## API Specification Details

**Summary:** Create a tax rate **Description:** Creates a new tax rate object.

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "rate"
  ],
  "properties": {
    "name": {
      "type": "string"
    },
    "rate": {
      "type": "number",
      "maximum": 999.999,
      "minimum": 0,
      "multipleOf": 0.001
    }
  }
}
```

### Response Examples

#### 200 Response

New tax rate created

```json
{
  "id": 1,
  "name": "15% VAT",
  "rate": 15,
  "is_default_sales": true,
  "is_default_purchases": true,
  "display_name": "15% VAT",
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
