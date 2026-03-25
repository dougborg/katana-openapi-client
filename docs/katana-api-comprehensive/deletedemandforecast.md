# Clear planned demand forecast to variant.

**DELETE** `https://api.katanamrp.com/v1/demand_forecasts`

Clear planned demand forecast to variant.Ask AI

## API Specification Details

**Summary:** Clear planned demand forecast to variant. **Description:** Clears planned
demand forecast for a variant in location for the specified periods.

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
          "period_end"
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
