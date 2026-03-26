# List current inventory

**GET** `https://api.katanamrp.com/v1/inventory`

List current inventory

## API Specification Details

**Summary:** List current inventory **Description:** Returns a list for current
inventory. The inventory is returned in sorted order, with the oldest locations
appearing first.

### Parameters

- **location_id** (query): Filters inventories by a valid location id
- **variant_id** (query): Filters inventories by valid variant ids
- **include_archived** (query): Includes archived inventories
- **extend** (query): Array of objects that need to be added to the response
- **limit** (query): Used for pagination (default is 50)
- **page** (query): Used for pagination (default is 1)

### Response Examples

#### 200 Response

List all inventories

```json
{
  "data": [
    {
      "variant_id": 1,
      "location_id": 1,
      "reorder_point": "5.00000",
      "average_cost": "10.0000000000",
      "value_in_stock": "70.0000000000",
      "quantity_in_stock": "7.00000",
      "quantity_committed": "0.00000",
      "quantity_expected": "100.00000",
      "quantity_missing_or_excess": "102.00000",
      "quantity_potential": "200.00000",
      "variant": {
        "id": 1,
        "sku": "EM",
        "sales_price": 40,
        "product_id": 1,
        "purchase_price": 0,
        "product_or_material_name": "New Product",
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
      },
      "location": {
        "id": 1,
        "name": "Main location",
        "legal_name": "Amazon",
        "address_id": 1,
        "address": {
          "id": 1,
          "city": "New York",
          "country": "United States",
          "line_1": "10 East 20th Example St",
          "line_2": "",
          "state": "New York",
          "zip": "10000"
        },
        "is_primary": true,
        "sales_allowed": true,
        "manufacturing_allowed": true,
        "created_at": "2020-10-23T10:37:05.085Z",
        "updated_at": "2020-10-23T10:37:05.085Z"
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
