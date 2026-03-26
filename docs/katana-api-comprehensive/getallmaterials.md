# List all materials

**GET** `https://api.katanamrp.com/v1/materials`

## API Specification Details

**Summary:** List all materials **Description:** Returns a list of materials you’ve
previously created. The materials are returned in sorted order, with the most recent
materials appearing first.

### Parameters

- **ids** (query): Filters materials by an array of IDs
- **name** (query): Filters materials by a name
- **uom** (query): Filters materials by a uom
- **default_supplier_id** (query): Filters materials by a default_supplier_id
- **is_sellable** (query): Filters materials by a is_sellable
- **batch_tracked** (query): Filters materials by a batch_tracked
- **purchase_uom** (query): Filters materials by a purchase_uom
- **purchase_uom_conversion_rate** (query): Filters materials by a
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

List all materials

```json
{
  "data": [
    {
      "id": 1,
      "name": "Kyber Crystal",
      "uom": "pcs",
      "category_name": "Lightsaber components",
      "default_supplier_id": 1,
      "type": "material",
      "purchase_uom": "pcs",
      "purchase_uom_conversion_rate": 1,
      "batch_tracked": false,
      "is_sellable": false,
      "archived_at": "2020-10-20T10:37:05.085Z",
      "variants": [
        {
          "id": 1,
          "product_id": null,
          "material_id": 1,
          "sku": "KC",
          "sales_price": null,
          "purchase_price": 45,
          "config_attributes": [
            {
              "config_name": "Type",
              "config_value": "Standard"
            }
          ],
          "type": "material",
          "deleted_at": null,
          "internal_barcode": "internalcode",
          "registered_barcode": "registeredcode",
          "supplier_item_codes": [
            "code"
          ],
          "lead_time": 1,
          "minimum_order_quantity": 3,
          "custom_fields": [
            {
              "field_name": "Power level",
              "field_value": "Strong"
            }
          ],
          "updated_at": "2020-10-23T10:37:05.085Z",
          "created_at": "2020-10-23T10:37:05.085Z"
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
