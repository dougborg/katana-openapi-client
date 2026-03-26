# Create a purchase order row

**POST** `https://api.katanamrp.com/v1/purchase_order_rows`

Create a purchase order row

## API Specification Details

**Summary:** Create a purchase order row **Description:** Creates a new purchase order
row object.

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "purchase_order_id",
    "price_per_unit",
    "quantity",
    "variant_id"
  ],
  "properties": {
    "purchase_order_id": {
      "type": "integer",
      "maximum": 2147483647
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
    "group_id": {
      "type": "integer",
      "maximum": 2147483647
    },
    "price_per_unit": {
      "type": "number",
      "maximum": 100000000000000000,
      "minimum": 0
    },
    "purchase_uom_conversion_rate": {
      "type": "number",
      "maximum": 100000000000000000,
      "minimum": 0
    },
    "purchase_uom": {
      "type": "string",
      "maxLength": 7
    },
    "arrival_date": {
      "type": "string"
    }
  }
}
```

### Response Examples

#### 200 Response

New purchase order row

```json
{
  "id": 1,
  "quantity": 1,
  "variant_id": 1,
  "tax_rate_id": 1,
  "price_per_unit": 1.5,
  "purchase_uom_conversion_rate": 1.1,
  "purchase_uom": "cm",
  "created_at": "2021-02-03T13:13:07.121Z",
  "updated_at": "2021-02-03T13:13:07.121Z",
  "deleted_at": null,
  "batch_transactions": [],
  "currency": "USD",
  "conversion_rate": null,
  "conversion_date": null,
  "received_date": "2021-02-03T13:13:07.000Z",
  "arrival_date": "2021-02-02T13:13:07.000Z",
  "purchase_order_id": 268123,
  "total": 1,
  "total_in_base_currency": 1,
  "landed_cost": 45.5,
  "group_id": 11
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
