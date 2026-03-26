# Create a purchase order

**POST** `https://api.katanamrp.com/v1/purchase_orders`

Create a purchase order

## API Specification Details

**Summary:** Create a purchase order **Description:** Creates a new purchase order
object.

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "order_no",
    "supplier_id",
    "location_id",
    "purchase_order_rows"
  ],
  "properties": {
    "order_no": {
      "type": "string"
    },
    "entity_type": {
      "type": "string",
      "enum": [
        "regular",
        "outsourced"
      ]
    },
    "supplier_id": {
      "type": "integer",
      "maximum": 2147483647
    },
    "currency": {
      "description": "E.g.
      USD, EUR.
      All currently active currency codes in ISO 4217 format.",
      "type": "string"
    },
    "status": {
      "type": "string",
      "enum": [
        "NOT_RECEIVED"
      ]
    },
    "expected_arrival_date": {
      "type": "string"
    },
    "order_created_date": {
      "type": "string"
    },
    "location_id": {
      "type": "integer",
      "maximum": 2147483647
    },
    "tracking_location_id": {
      "type": "integer",
      "maximum": 2147483647,
      "description": "Submittable only when entity_type is outsourced"
    },
    "additional_info": {
      "type": "string"
    },
    "purchase_order_rows": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "quantity",
          "variant_id",
          "price_per_unit"
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
          "tax_rate_id": {
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
    }
  }
}
```

### Response Examples

#### 200 Response

New purchase order

```json
{
  "id": 1,
  "status": "NOT_RECEIVED",
  "billing_status": "NOT_BILLED",
  "last_document_status": "NOT_SENT",
  "order_no": "PO-1",
  "entity_type": "regular",
  "default_group_id": 9,
  "supplier_id": 1,
  "currency": "USD",
  "expected_arrival_date": "2021-10-13T15:31:48.490Z",
  "order_created_date": "2021-10-13T15:31:48.490Z",
  "additional_info": "Please unpack",
  "location_id": 1,
  "tracking_location_id": null,
  "total": 1,
  "total_in_base_currency": 1,
  "created_at": "2021-02-03T13:13:07.110Z",
  "updated_at": "2021-02-03T13:13:07.110Z",
  "deleted_at": null,
  "purchase_order_rows": [
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
      "purchase_order_id": 1,
      "total": 1,
      "total_in_base_currency": 1,
      "landed_cost": "45.0000000000",
      "group_id": 11
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
