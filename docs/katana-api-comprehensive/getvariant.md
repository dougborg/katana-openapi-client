# Retrieve a variant

**GET** `https://api.katanamrp.com/v1/variants/{id}`

## API Specification Details

**Summary:** Retrieve a variant **Description:** Retrieves the details of an existing
variant based on ID.

### Parameters

- **id** (path) *required*: Variant id
- **extend** (query): Array of objects that need to be added to the response

### Response Examples

#### 200 Response

Details of an existing variant

```json
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
