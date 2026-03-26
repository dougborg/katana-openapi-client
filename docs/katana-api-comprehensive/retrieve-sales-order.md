# Retrieve a sales order

**GET** `https://api.katanamrp.com/v1/sales_orders/{id}`

Retrieve a sales order

## API Specification Details

**Summary:** Retrieve a sales order **Description:** Retrieves the details of an
existing sales order based on ID

### Parameters

- **id** (path) *required*: Sales order id

### Response Examples

#### 200 Response

Sales order

```json
{
  "id": 1,
  "customer_id": 1,
  "order_no": "SO-3",
  "source": "api",
  "order_created_date": "2020-10-23T10:37:05.085Z",
  "delivery_date": "2020-10-23T10:37:05.085Z",
  "location_id": 1,
  "status": "NOT_SHIPPED",
  "currency": "USD",
  "conversion_rate": 2,
  "total": 150,
  "total_in_base_currency": 75,
  "conversion_date": "2020-10-23T10:37:05.085Z",
  "product_availability": "IN_STOCK",
  "product_expected_date": "2021-09-10T08:00:00.000Z",
  "ingredient_availability": "PROCESSED",
  "ingredient_expected_date": "2021-09-10T08:00:00.000Z",
  "production_status": "DONE",
  "invoicing_status": "invoiced",
  "additional_info": "additional info",
  "customer_ref": "my customer reference",
  "picked_date": "2020-10-23T10:37:05.085Z",
  "ecommerce_order_type": "shopify",
  "ecommerce_store_name": "katana.myshopify.com",
  "ecommerce_order_id": "19433769",
  "created_at": "2020-10-23T10:37:05.085Z",
  "updated_at": "2020-10-23T10:37:05.085Z",
  "sales_order_rows": [
    {
      "sales_order_id": 1,
      "id": 1,
      "quantity": 2,
      "variant_id": 1,
      "tax_rate_id": 1,
      "location_id": 1,
      "price_per_unit": 75,
      "total_discount": "10.00",
      "price_per_unit_in_base_currency": 37.5,
      "total": 150,
      "total_in_base_currency": 75,
      "conversion_rate": 2,
      "conversion_date": "2020-10-23T10:37:05.085Z",
      "product_availability": "IN_STOCK",
      "product_expected_date": "2021-09-10T08:00:00.000Z",
      "created_at": "2020-10-23T10:37:05.085Z",
      "updated_at": "2020-10-23T10:37:05.085Z",
      "linked_manufacturing_order_id": 1,
      "attributes": [
        {
          "key": "key",
          "value": "value"
        }
      ],
      "batch_transactions": [
        {
          "batch_id": 1,
          "quantity": 10
        }
      ],
      "serial_numbers": [
        1
      ]
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
  ],
  "shipping_fee": {
    "id": 1,
    "sales_order_id": 1,
    "description": "",
    "amount": "1.0000000000",
    "tax_rate_id": 16582
  }
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
