# Retrieve a product

**GET** `https://api.katanamrp.com/v1/products/{id}`

## API Specification Details

**Summary:** Retrieve a product **Description:** Retrieves the details of an existing
product based on ID.

### Parameters

- **id** (path) *required*: Product id
- **extend** (query): Array of objects that need to be added to the response

### Response Examples

#### 200 Response

Details of an existing product

```json
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
  "batch_tracked": false,
  "operations_in_sequence": false,
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
