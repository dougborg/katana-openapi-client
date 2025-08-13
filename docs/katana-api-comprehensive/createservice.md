# Create a service

**POST** `https://api.katanamrp.com/v1/services`

## API Specification Details

**Summary:** Create a service **Description:** Creates a service object.

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "name",
    "variants"
  ],
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
    "additional_info": {
      "type": "string"
    },
    "is_sellable": {
      "type": "boolean"
    },
    "custom_field_collection_id": {
      "type": "integer",
      "maximum": 2147483647,
      "nullable": true
    },
    "variants": {
      "type": "array",
      "minItems": 1,
      "maxItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "sku": {
            "type": "string"
          },
          "sales_price": {
            "type": "number",
            "maximum": 100000000000,
            "minimum": 0,
            "nullable": true
          },
          "default_cost": {
            "type": "number",
            "maximum": 100000000000,
            "minimum": 0,
            "nullable": true
          },
          "custom_fields": {
            "type": "array",
            "maxItems": 3,
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "field_name",
                "field_value"
              ],
              "properties": {
                "field_name": {
                  "maxLength": 40,
                  "type": "string"
                },
                "field_value": {
                  "maxLength": 100,
                  "type": "string"
                }
              }
            }
          }
        }
      }
    }
  }
}
```

### Response Examples

#### 200 Response

New service created

```json
{
  "id": 1,
  "name": "Service name",
  "uom": "pcs",
  "category_name": "Service",
  "type": "service",
  "is_sellable": true,
  "custom_field_collection_id": 1,
  "additional_info": "additional info",
  "created_at": "2020-10-23T10:37:05.085Z",
  "updated_at": "2020-10-23T10:37:05.085Z",
  "deleted_at": null,
  "archived_at": "2020-10-20T10:37:05.085Z",
  "variants": [
    {
      "id": 1,
      "sku": "S-2486",
      "sales_price": null,
      "default_cost": null,
      "service_id": 1,
      "type": "service",
      "created_at": "2020-10-23T10:37:05.085Z",
      "updated_at": "2020-10-23T10:37:05.085Z",
      "deleted_at": null,
      "custom_fields": [
        {
          "field_name": "Power level",
          "field_value": "Strong"
        }
      ]
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
