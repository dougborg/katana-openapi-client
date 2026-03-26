# Update a material

**PATCH** `https://api.katanamrp.com/v1/materials/{id}`

## API Specification Details

**Summary:** Update a material **Description:** Updates the specified material by
setting the values of the parameters passed. Any parameters not provided will be left
unchanged.

### Parameters

- **id** (path) *required*: Material id

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "uom": {
      "type": "string",
      "maxLength": 7
    },
    "category_name": {
      "type": "string"
    },
    "default_supplier_id": {
      "type": "integer",
      "maximum": 2147483647
    },
    "additional_info": {
      "type": "string"
    },
    "batch_tracked": {
      "type": "boolean"
    },
    "is_sellable": {
      "type": "boolean"
    },
    "is_archived": {
      "type": "boolean"
    },
    "purchase_uom": {
      "type": "string",
      "maxLength": 7,
      "description": "If used, then purchase_uom_conversion_rate must have a value as well."
    },
    "purchase_uom_conversion_rate": {
      "type": "number",
      "description": "If used, then purchase_uom must have a value as well.",
      "maximum": 1000000000000
    },
    "configs": {
      "type": "array",
      "minItems": 1,
      "description": "When updating configs, all configs and values must be provided.
      Existing ones are matched,\n        new ones are created, and configs not provided in the update are deleted.",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "name",
          "values"
        ],
        "properties": {
          "id": {
            "type": "integer",
            "description": "If config ID is used to map the config, then name is ignored."
          },
          "name": {
            "type": "string",
            "description": "If config name is used to map the config, then we match to the existing config by name.\n              If a match is not found, a new one is created."
          },
          "values": {
            "type": "array",
            "items": {
              "type": "string"
            }
          }
        }
      }
    },
    "custom_field_collection_id": {
      "type": "integer",
      "maximum": 2147483647,
      "nullable": true
    }
  }
}
```

### Response Examples

#### 200 Response

Material updated

```json
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
      "sku": "KC",
      "sales_price": null,
      "product_id": 1,
      "purchase_price": 45,
      "type": "material",
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
  "updated_at": "2020-10-23T10:37:05.085Z"
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
