# List all variants

**GET** `https://api.katanamrp.com/v1/variants`

## API Specification Details

**Summary:** List all variants **Description:** Returns a list of variants you've
previously created. The variants are returned in sorted order, with the most recent
variants appearing first.

### Parameters

- **ids** (query): Filters variants by an array of IDs
- **product_id** (query): Filters variants by a product id
- **material_id** (query): Filters variants by a material id
- **sku** (query): Filters variants by skus
- **sales_price** (query): Filters variants by a sales price
- **purchase_price** (query): Filters variants by a purchase price
- **internal_barcode** (query): Filters variants by an internal barcode
- **registered_barcode** (query): Filters variants by a registered barcode
- **supplier_item_codes** (query): Filters variants by supplier item codes. Returns the
  variants that match with any of the codes in the array.
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

List all product variants

```json
{
  "data": [
    {
      "id": 1,
      "sku": "EM",
      "sales_price": 40,
      "product_id": 1,
      "material_id": null,
      "purchase_price": 0,
      "type": "product",
      "created_at": "2020-10-23T10:37:05.085Z",
      "updated_at": "2020-10-23T10:37:05.085Z",
      "deleted_at": null,
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
      ],
      "product_or_material": {
        "id": 1,
        "name": "Standard-hilt lightsaber",
        "uom": "pcs",
        "category_name": "lightsaber",
        "is_producible": true,
        "default_supplier_id": 1,
        "is_purchasable": true,
        "type": "product",
        "purchase_uom": "pcs",
        "purchase_uom_conversion_rate": 1,
        "batch_tracked": false,
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
