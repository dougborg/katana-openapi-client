# List all sales order rows

**GET** `https://api.katanamrp.com/v1/sales_order_rows`

List all sales order rows

## API Specification Details

**Summary:** List all sales order rows **Description:** Returns a list of sales order
rows you’ve previously created. The sales order rows are returned in a sorted order,
with the most recent sales order rows appearing first.

### Parameters

- **ids** (query): Filters sales order rows by an array of IDs
- **sales_order_ids** (query): Filters sales order rows by an array of sales order ids
- **variant_id** (query): Filters sales order rows by variant id.
- **location_id** (query): Filters sales order rows by location
- **tax_rate_id** (query): Filters sales order rows by tax rate id.
- **linked_manufacturing_order_id** (query): Filters sales order rows manufacturing
  order id.
- **product_availability** (query): Filters sales order rows by product availability
- **extend** (query): Array of objects that need to be added to the response
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

List all sales order rows

```json
{
  "data": [
    {
      "sales_order_id": 1,
      "id": 1,
      "quantity": 1,
      "variant_id": 1,
      "tax_rate_id": 1,
      "location_id": 1,
      "price_per_unit": 150,
      "total_discount": "10.00",
      "price_per_unit_in_base_currency": 300,
      "conversion_rate": 2,
      "conversion_date": "2020-10-23T10:37:05.085Z",
      "product_availability": "EXPECTED",
      "product_expected_date": "2020-10-23T10:37:05.085Z",
      "created_at": "2020-10-23T10:37:05.085Z",
      "updated_at": "2020-10-23T10:37:05.085Z",
      "deleted_at": null,
      "total": 150,
      "total_in_base_currency": 300,
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
      ],
      "variant": {
        "id": 1,
        "sku": "EM",
        "sales_price": 40,
        "product_id": 1,
        "purchase_price": 0,
        "type": "product",
        "created_at": "2020-10-23T10:37:05.085Z",
        "updated_at": "2020-10-23T10:37:05.085Z",
        "internal_barcode": "0316",
        "registered_barcode": "0785223088",
        "supplier_item_codes": [
          "978-0785223085",
          "0785223088"
        ],
        "config_attributes": [
          {
            "config_name": "Type",
            "config_value": "Standard"
          }
        ]
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
