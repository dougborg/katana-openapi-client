# Create a sales order fulfillment

**POST** `https://api.katanamrp.com/v1/sales_order_fulfillments`

Create a sales order fulfillment

## API Specification Details

**Summary:** Create a sales order fulfillment **Description:** Creates a new fulfillment
for an existing sales order.

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "sales_order_id",
    "status"
  ],
  "properties": {
    "sales_order_id": {
      "type": "integer",
      "maximum": 2147483647
    },
    "picked_date": {
      "type": "string"
    },
    "status": {
      "type": "string",
      "enum": [
        "DELIVERED",
        "PACKED"
      ]
    },
    "conversion_rate": {
      "type": "number",
      "maximum": 1000000000000
    },
    "conversion_date": {
      "type": "string"
    },
    "tracking_number": {
      "type": "string",
      "maxLength": 256,
      "nullable": true
    },
    "tracking_url": {
      "type": "string",
      "maxLength": 2048,
      "nullable": true
    },
    "tracking_carrier": {
      "type": "string"
    },
    "tracking_method": {
      "type": "string"
    },
    "sales_order_fulfillment_rows": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "sales_order_row_id",
          "quantity"
        ],
        "properties": {
          "sales_order_row_id": {
            "type": "integer",
            "maximum": 2147483647
          },
          "quantity": {
            "type": "number",
            "maximum": 100000000000000000
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
          },
          "serial_numbers": {
            "type": "array",
            "items": {
              "type": "number"
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

New sales order fulfillment created

```json
{
  "id": 1,
  "sales_order_id": 1,
  "picked_date": "2020-10-23T10:37:05.085Z",
  "status": "DELIVERED",
  "conversion_rate": 2,
  "conversion_date": "2020-10-23T10:37:05.085Z",
  "tracking_number": "12345678",
  "tracking_url": "https://tracking-number-url",
  "tracking_carrier": "UPS",
  "tracking_method": "ground",
  "sales_order_fulfillment_rows": [
    {
      "sales_order_row_id": 1,
      "quantity": 2,
      "batch_transactions": [
        {
          "batch_id": 1,
          "quantity": 2
        }
      ],
      "serial_numbers": [
        1
      ]
    }
  ]
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
