# Update a sales order

**PATCH** `https://api.katanamrp.com/v1/sales_orders/{id}`

## API Specification Details

**Summary:** Update a sales order **Description:** Updates the specified sales order by
setting the values of the parameters passed. Any parameters not provided will be left
unchanged.

### Parameters

- **id** (path) *required*: Sales order id

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "order_no": {
      "type": "string",
      "description": "Updatable only when sales order status is NOT_SHIPPED or PENDING.",
      "minLength": 1
    },
    "customer_id": {
      "type": "integer",
      "description": "Updatable only when sales order status is NOT_SHIPPED or PENDING.",
      "maximum": 2147483647
    },
    "order_created_date": {
      "type": "string"
    },
    "delivery_date": {
      "type": "string",
      "description": "Updatable only when sales order status is NOT_SHIPPED or PENDING."
    },
    "picked_date": {
      "type": "string",
      "description": "Updatable only when sales order status is NOT_SHIPPED or PENDING."
    },
    "location_id": {
      "type": "integer",
      "description": "Updatable only when sales order status is NOT_SHIPPED or PENDING.",
      "maximum": 2147483647
    },
    "status": {
      "type": "string",
      "description": "When the status is omitted, NOT_SHIPPED is used as default.\n        Use PENDING when you want to create sales order quotes.",
      "enum": [
        "NOT_SHIPPED",
        "PENDING",
        "PACKED",
        "DELIVERED"
      ]
    },
    "currency": {
      "description": "E.g.
      USD, EUR.
      All currently active currency codes in ISO 4217 format.\n        Updatable only when sales order status is NOT_SHIPPED or PENDING.",
      "type": "string"
    },
    "conversion_rate": {
      "description": "Updatable only when sales order status is PACKED or DELIVERED, otherwise it will fail with 422.",
      "type": "number"
    },
    "conversion_date": {
      "description": "Updatable only when sales order status is PACKED or DELIVERED, otherwise it will fail with 422.",
      "type": "string"
    },
    "additional_info": {
      "type": "string",
      "nullable": true
    },
    "customer_ref": {
      "type": "string",
      "maxLength": 255,
      "nullable": true
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
    }
  }
}
```

### Response Examples

#### 200 Response

Sales order updated

```json
{
  "id": 1,
  "customer_id": 1,
  "order_no": "SO-3",
  "source": "API",
  "order_created_date": "2020-10-23T10:37:05.085Z",
  "delivery_date": "2020-10-23T10:37:05.085Z",
  "location_id": 1,
  "status": "NOT_SHIPPED",
  "currency": "USD",
  "conversion_rate": 0.7,
  "conversion_date": "2020-10-23T10:37:05.085Z",
  "product_availability": "IN_STOCK",
  "ingredient_availability": "PROCESSED",
  "production_status": "DONE",
  "invoicing_status": "invoiced",
  "additional_info": "additional info",
  "customer_ref": "my customer reference",
  "picked_date": "2020-10-23T10:37:05.085Z",
  "ecommerce_order_type": "shopify",
  "ecommerce_store_name": "katana.myshopify.com",
  "ecommerce_order_id": "19433769",
  "tracking_number": "12345678",
  "tracking_number_url": "https://tracking-number-url",
  "billing_address_id": 1234,
  "shipping_address_id": 1235,
  "linked_manufacturing_order_id": 1,
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
