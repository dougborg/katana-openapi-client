# Update the safety stock level

**POST** `https://api.katanamrp.com/v1/inventory_safety_stock_levels`

Update the safety stock level

## API Specification Details

**Summary:** Update the safety stock level **Description:** Update an item’s safety
stock level within a certain location and variant combination.

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "location_id",
    "variant_id",
    "value"
  ],
  "properties": {
    "location_id": {
      "type": "integer",
      "maximum": 2147483647
    },
    "variant_id": {
      "type": "integer",
      "maximum": 2147483647
    },
    "value": {
      "type": "number",
      "maximum": 100000000000000000
    }
  }
}
```

### Response Examples

#### 200 Response

New inventory safety stock level created

```json
{
  "variant_id": 1,
  "location_id": 1,
  "value": 10,
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
