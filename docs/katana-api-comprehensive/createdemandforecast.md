# Add planned demand forecast to variant.

**POST** `https://api.katanamrp.com/v1/demand_forecasts`

Add planned demand forecast to variant.Ask AI

## API Specification Details

**Summary:** Add planned demand forecast to variant. **Description:** Add planned demand
forecast for a variant in location for the specified periods.

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "variant_id",
    "location_id",
    "periods"
  ],
  "properties": {
    "variant_id": {
      "type": "integer",
      "maximum": 2147483647
    },
    "location_id": {
      "type": "integer",
      "maximum": 2147483647
    },
    "periods": {
      "type": "array",
      "minItems": 1,
      "maxItems": 100,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "period_start",
          "period_end",
          "committed"
        ],
        "properties": {
          "period_start": {
            "description": "Period start date in ISO 8601 format (inclusive).",
            "type": "string",
            "format": "date-time"
          },
          "period_end": {
            "description": "Period end date in ISO 8601 format (inclusive).",
            "type": "string",
            "format": "date-time"
          },
          "committed": {
            "description": "Total forecasted demand quantity for the period.",
            "type": "string"
          }
        }
      }
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
