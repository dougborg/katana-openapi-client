# Create a sales order

**POST** `https://api.katanamrp.com/v1/sales_orders`

## API Specification Details

**Summary:** Create a sales order **Description:** Creates a new sales order object.

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "order_no",
    "customer_id",
    "sales_order_rows"
  ],
  "properties": {
    "order_no": {
      "type": "string"
    },
    "customer_id": {
      "type": "integer",
      "maximum": 2147483647
    },
    "sales_order_rows": {
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
    },
    "tracking_number": {
      "type": "string",
      "maxLength": 256,
      "nullable": true
    },
    "tracking_number_url": {
      "type": "string",
      "maxLength": 2048,
      "nullable": true
    },
    "addresses": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "entity_type"
        ],
        "properties": {
          "entity_type": {
            "type": "string",
            "enum": [
              "billing",
              "shipping"
            ]
          },
          "first_name": {
            "type": "string",
            "nullable": true
          },
          "last_name": {
            "type": "string",
            "nullable": true
          },
          "company": {
            "type": "string",
            "nullable": true
          },
          "phone": {
            "type": "string",
            "nullable": true
          },
          "line_1": {
            "type": "string",
            "nullable": true
          },
          "line_2": {
            "type": "string",
            "nullable": true
          },
          "city": {
            "type": "string",
            "nullable": true
          },
          "state": {
            "type": "string",
            "nullable": true
          },
          "zip": {
            "type": "string",
            "nullable": true
          },
          "country": {
            "type": "string",
            "nullable": true
          }
        }
      }
    },
    "order_created_date": {
      "type": "string"
    },
    "delivery_date": {
      "type": "string"
    },
    "currency": {
      "description": "E.g.
      USD, EUR.
      All currently active currency codes in ISO 4217 format.",
      "type": "string"
    },
    "location_id": {
      "type": "integer",
      "maximum": 2147483647
    },
    "status": {
      "type": "string",
      "enum": [
        "NOT_SHIPPED",
        "PENDING"
      ],
      "description": "When the status is omitted, NOT_SHIPPED is used as default.\n        Use PENDING when you want to create sales order quotes."
    },
    "additional_info": {
      "type": "string"
    },
    "customer_ref": {
      "type": "string",
      "maxLength": 255,
      "nullable": true
    },
    "ecommerce_order_type": {
      "type": "string"
    },
    "ecommerce_store_name": {
      "type": "string"
    },
    "ecommerce_order_id": {
      "type": "string"
    }
  }
}
```

### Response Examples

#### 200 Response

New sales order created

```json
{
  "id": 1,
  "customer_id": 1,
  "order_no": "SO-3",
  "source": "API",
  "order_created_date": "2020-10-23T10:37:05.085Z",
  "delivery_date": "2020-10-23T10:37:05.085Z",
  "location_id": 1,
  "picked_date": null,
  "status": "NOT_SHIPPED",
  "currency": "USD",
  "conversion_rate": 2,
  "total": 300,
  "total_in_base_currency": 150,
  "conversion_date": "2020-10-23T10:37:05.085Z",
  "product_availability": "IN_STOCK",
  "ingredient_availability": "PROCESSED",
  "production_status": "DONE",
  "invoicing_status": "invoiced",
  "additional_info": "additional info",
  "customer_ref": "my customer reference",
  "ecommerce_order_type": "shopify",
  "ecommerce_store_name": "katana.myshopify.com",
  "ecommerce_order_id": "19433769",
  "created_at": "2020-10-23T10:37:05.085Z",
  "updated_at": "2020-10-23T10:37:05.085Z",
  "deleted_at": null,
  "sales_order_rows": [
    {
      "sales_order_id": 1,
      "id": 1,
      "quantity": 2,
      "variant_id": 1,
      "tax_rate_id": 1,
      "location_id": 1,
      "price_per_unit": 150,
      "total": 300,
      "total_in_base_currency": 150,
      "conversion_rate": null,
      "conversion_date": null,
      "created_at": "2020-10-23T10:37:05.085Z",
      "updated_at": "2020-10-23T10:37:05.085Z",
      "attributes": [
        {
          "key": "key",
          "value": "value"
        }
      ],
      "batch_transactions": []
    }
  ],
  "tracking_number": "12345678",
  "tracking_number_url": "https://tracking-number-url",
  "billing_address_id": 1234,
  "shipping_address_id": 1235,
  "addresses": [
    {
      "id": 1234,
      "sales_order_id": 12345,
      "entity_type": "billing",
      "first_name": "Luke",
      "last_name": "Skywalker",
      "company": "Company",
      "phone": "123456",
      "line_1": "Line 1",
      "line_2": "Line 2",
      "city": "City",
      "state": "State",
      "zip": "Zip",
      "country": "Country",
      "updated_at": "2020-10-23T10:37:05.085Z",
      "created_at": "2020-10-23T10:37:05.085Z"
    },
    {
      "id": 1235,
      "sales_order_id": 12345,
      "entity_type": "shipping",
      "first_name": "Luke",
      "last_name": "Skywalker",
      "company": "Company",
      "phone": "123456",
      "line_1": "Line 1",
      "line_2": "Line 2",
      "city": "City",
      "state": "State",
      "zip": "Zip",
      "country": "Country",
      "updated_at": "2020-10-23T10:37:05.085Z",
      "created_at": "2020-10-23T10:37:05.085Z"
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
