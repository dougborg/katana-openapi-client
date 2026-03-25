# Create a batch

**POST** `https://api.katanamrp.com/v1/batches`

## API Specification Details

**Summary:** Create a batch **Description:** Creates a batch object.

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "batch_number",
    "variant_id"
  ],
  "properties": {
    "batch_number": {
      "type": "string"
    },
    "expiration_date": {
      "type": "string"
    },
    "batch_created_date": {
      "type": "string"
    },
    "variant_id": {
      "type": "integer",
      "maximum": 2147483647
    },
    "batch_barcode": {
      "type": "string",
      "minLength": 3,
      "maxLength": 40,
      "nullable": true
    }
  }
}
```

### Response Examples

#### 200 Response

Batch stock created

```json
{
  "id": 1,
  "batch_number": "BAT-1",
  "expiration_date": "2020-10-23T10:37:05.085Z",
  "batch_created_date": "2020-10-23T10:37:05.085Z",
  "created_at": "2020-10-23T10:37:05.085Z",
  "updated_at": "2020-10-23T10:37:05.085Z",
  "variant_id": 1,
  "batch_barcode": "0040"
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
