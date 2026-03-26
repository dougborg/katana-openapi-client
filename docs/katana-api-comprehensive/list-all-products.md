# List all products

**GET** `https://api.katanamrp.com/v1/products`

## API Specification Details

**Summary:** List all products **Description:** Returns a list of products you’ve
previously created. The products are returned in sorted order, with the most recent
products appearing first.

### Parameters

- **ids** (query): Filters products by an array of IDs
- **name** (query): Filters products by a name
- **uom** (query): Filters products by a uom
- **is_sellable** (query): Filters products by a is_sellable
- **is_producible** (query): Filters products by an is_producible
- **is_purchasable** (query): Filters products by an is_purchasable
- **is_auto_assembly** (query): Filters products by an is_auto_assembly
- **default_supplier_id** (query): Filters products by a default_supplier_id
- **batch_tracked** (query): Filters products by a batch_tracked
- **serial_tracked** (query): Filters products by a serial_tracked
- **operations_in_sequence** (query): Filters products by a operations_in_sequence
- **purchase_uom** (query): Filters products by a purchase_uom
- **purchase_uom_conversion_rate** (query): Filters products by a
  purchase_uom_conversion_rate
- **extend** (query): Array of objects that need to be added to the response
- **include_deleted** (query): Soft-deleted data is excluded from result set by default.
  Set to true to include it.
- **include_archived** (query): Archived data is excluded from result set by default.
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

List all products

```json
{
  "data": [
    {
      "id": 1,
      "name": "Standard-hilt lightsaber",
      "uom": "pcs",
      "category_name": "lightsaber",
      "is_producible": true,
      "default_supplier_id": 1,
      "is_sellable": true,
      "is_purchasable": true,
      "is_auto_assembly": true,
      "type": "product",
      "purchase_uom": "pcs",
      "purchase_uom_conversion_rate": 1,
      "batch_tracked": true,
      "operations_in_sequence": false,
      "serial_tracked": false,
      "archived_at": "2020-10-20T10:37:05.085Z",
      "variants": [
        {
          "id": 1,
          "sku": "EM",
          "sales_price": 40,
          "product_id": 1,
          "purchase_price": 0,
          "type": "product",
          "created_at": "2020-10-23T10:37:05.085Z",
          "updated_at": "2020-10-23T10:37:05.085Z",
          "lead_time": 1,
          "minimum_order_quantity": 3,
          "config_attributes": [
            {
              "config_name": "Type",
              "config_value": "Standard"
            }
          ],
          "internal_barcode": "internalcode",
          "registered_barcode": "registeredcode",
          "supplier_item_codes": [
            "code"
          ],
          "custom_fields": [
            {
              "field_name": "Power level",
              "field_value": "Strong"
            }
          ]
        }
      ],
      "configs": [
        {
          "id": 1,
          "name": "Type",
          "values": [
            "Standard",
            "Double-bladed"
          ],
          "product_id": 1
        }
      ],
      "additional_info": "additional info",
      "custom_field_collection_id": 1,
      "created_at": "2020-10-23T10:37:05.085Z",
      "updated_at": "2020-10-23T10:37:05.085Z",
      "supplier": {
        "id": 1,
        "name": "Luke Skywalker",
        "email": "luke.skywalker@example.com",
        "comment": "Luke Skywalker was a Tatooine farmboy who rose from humble beginnings to become one of the\n              greatest Jedi the galaxy has ever known.",
        "currency": "UAH",
        "created_at": "2020-10-23T10:37:05.085Z",
        "updated_at": "2020-10-23T10:37:05.085Z",
        "deleted_at": null
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
