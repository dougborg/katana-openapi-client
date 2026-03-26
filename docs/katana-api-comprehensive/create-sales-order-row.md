# Create a sales order row

**POST** `https://api.katanamrp.com/v1/sales_order_rows`

Create a sales order row

## API Specification Details

**Summary:** Create a sales order row **Description:** Add a sales order row to an
existing sales order. Rows can be added only when the sales order status is NOT_SHIPPED
or PENDING.

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "sales_order_id",
    "quantity",
    "variant_id"
  ],
  "properties": {
    "sales_order_id": {
      "type": "integer"
    },
    "quantity": {
      "type": "number",
      "maximum": 100000000000000000
    },
    "variant_id": {
      "type": "integer",
      "maximum": 2147483647
    },
    "tax_rate_id": {
      "type": "integer",
      "maximum": 2147483647
    },
    "location_id": {
      "type": "integer",
      "maximum": 2147483647
    },
    "attributes": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "key",
          "value"
        ],
        "properties": {
          "key": {
            "type": "string"
          },
          "value": {
            "type": "string"
          }
        }
      }
    },
    "price_per_unit": {
      "type": "number",
      "maximum": 1000000000000000000
    },
    "total_discount": {
      "type": "number",
      "maximum": 1000000000000000000
    }
  }
}
```

### Response Examples

#### 200 Response

New sales order row created

```json
{
  "sales_order_id": 1,
  "id": 1,
  "quantity": 2,
  "variant_id": 1,
  "tax_rate_id": 1,
  "location_id": 1,
  "price_per_unit": 150,
  "total_discount": "10.00",
  "created_at": "2020-10-23T10:37:05.085Z",
  "updated_at": "2020-10-23T10:37:05.085Z",
  "deleted_at": null,
  "conversion_rate": null,
  "conversion_date": null,
  "linked_manufacturing_order_id": null,
  "attributes": [
    {
      "key": "key",
      "value": "value"
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
