# Create a stock transfer

**POST** `https://api.katanamrp.com/v1/stock_transfers`

Create a stock transfer

## API Specification Details

**Summary:** Create a stock transfer **Description:** Creates a stock transfer object.

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "stock_transfer_number",
    "source_location_id",
    "target_location_id",
    "stock_transfer_rows"
  ],
  "properties": {
    "stock_transfer_number": {
      "type": "string",
      "minLength": 1
    },
    "source_location_id": {
      "type": "integer",
      "maximum": 2147483647
    },
    "target_location_id": {
      "type": "integer",
      "maximum": 2147483647
    },
    "transfer_date": {
      "type": "string"
    },
    "order_created_date": {
      "type": "string"
    },
    "expected_arrival_date": {
      "type": "string"
    },
    "additional_info": {
      "type": "string",
      "nullable": true
    },
    "stock_transfer_rows": {
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
            "type": "string",
            "maximum": 100000000000000000
          },
          "variant_id": {
            "type": "integer",
            "maximum": 2147483647
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

New stock transfer created

```json
{
  "id": 1,
  "stock_transfer_number": "ST-1",
  "source_location_id": 1,
  "target_location_id": 2,
  "transfer_date": "2020-10-23T10:37:05.085Z",
  "order_created_date": "2021-10-01T11:47:13.846Z",
  "expected_arrival_date": "2021-10-20T11:47:13.846Z",
  "additional_info": "transfer additional info",
  "stock_transfer_rows": [
    {
      "id": 1,
      "variant_id": 1,
      "quantity": 3,
      "cost_per_unit": 10,
      "batch_transactions": [
        {
          "batch_id": 1,
          "quantity": 3
        }
      ],
      "deleted_at": null
    }
  ],
  "created_at": "2020-10-23T10:37:05.085Z",
  "updated_at": "2020-10-23T10:37:05.085Z",
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
