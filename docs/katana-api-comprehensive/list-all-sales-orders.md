# List all sales orders

**GET** `https://api.katanamrp.com/v1/sales_orders`

List all sales orders

## API Specification Details

**Summary:** List all sales orders **Description:** Returns a list of sales orders
you’ve previously created. The sales orders are returned in a sorted order, with the
most recent sales orders appearing first.

### Parameters

- **ids** (query): Filters sales orders by an array of IDs
- **order_no** (query): Filters sales orders by an order number
- **source** (query): Filters sales orders by a creation source
- **location_id** (query): Filters sales orders by location
- **customer_id** (query): Filters sales orders by customer
- **status** (query): Filters sales orders by a status
- **currency** (query): Filters sales orders by currency
- **invoicing_status** (query): Filters sales orders by an invoicing status
- **product_availability** (query): Filters sales orders by product availability
- **ingredient_availability** (query): Filters sales orders by ingredient availability
- **production_status** (query): Filters sales orders by production status
- **ecommerce_order_type** (query): Filters sales orders by an e-commerce order type
- **ecommerce_store_name** (query): Filters sales orders by an e-commerce store name
- **ecommerce_order_id** (query): Filters sales orders by an e-commerce order id
- **include_deleted** (query): Soft-deleted data is excluded from result set by default.
  Set to true to include it.
- **limit** (query): Used for pagination (default is 50)
- **page** (query): Used for pagination (default is 1)
- **created_at_min** (query): Minimum value for created_at range. Must be compatible
  with ISO 8601 format
- **created_at_max** (query): Maximum value for created_at range. Must be compatible
  with ISO 8601 format
- **updated_at_min** (query): Minimum value for updated_at range. Must be compatible
  with ISO 8601 format
- **updated_at_max** (query): Maximum value for updated_at range. Must be compatible
  with ISO 8601 format

### Response Examples

#### 200 Response

List all sales orders

```json
{
  "data": [
    {
      "id": 1,
      "customer_id": 1,
      "order_no": "SO-3",
      "source": "api",
      "order_created_date": "2020-10-23T10:37:05.085Z",
      "delivery_date": "2020-10-23T10:37:05.085Z",
      "picked_date": "2020-10-23T10:37:05.085Z",
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
