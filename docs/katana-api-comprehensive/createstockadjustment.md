# Create a stock adjustment

**POST** `https://api.katanamrp.com/v1/stock_adjustments`

Create a stock adjustment

## API Specification Details

**Summary:** Create a stock adjustment **Description:** Creates a stock adjustment
object.

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "stock_adjustment_number",
    "location_id",
    "stock_adjustment_rows"
  ],
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
    },
    "stock_adjustment_rows": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "quantity",
          "variant_id"
        ],
        "properties": {
          "quantity": {
            "type": "number",
            "maximum": 100000000000000000
          },
          "variant_id": {
            "type": "integer",
            "maximum": 2147483647
          },
          "cost_per_unit": {
            "type": "number",
            "maximum": 1000000000000000000
          },
          "batch_transactions": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "batch_id",
                "quantity"
              ],
              "properties": {
                "batch_id": {
                  "type": "integer",
                  "maximum": 2147483647
                },
                "quantity": {
                  "type": "number",
                  "maximum": 100000000000000000
                }
              }
            }
          }
        }
      }
    }
  }
}
```

### Response Examples

#### 200 Response

New stock adjustment created

```json
{
  "id": 1,
  "stock_adjustment_number": "SA-1",
  "stock_adjustment_date": "2021-10-06T11:47:13.846Z",
  "location_id": 1,
  "reason": "adjustment reason",
  "additional_info": "adjustment additional info",
  "stock_adjustment_rows": [
    {
      "id": 1,
      "variant_id": 1,
      "quantity": 100,
      "cost_per_unit": 123.45,
      "batch_transactions": [
        {
          "batch_id": 1,
          "quantity": 50
        },
        {
          "batch_id": 2,
          "quantity": 50
        }
      ]
    },
    {
      "id": 2,
      "variant_id": 2,
      "quantity": 150,
      "cost_per_unit": 234.56,
      "batch_transactions": [
        {
          "batch_id": 3,
          "quantity": 150
        }
      ]
    }
  ],
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
