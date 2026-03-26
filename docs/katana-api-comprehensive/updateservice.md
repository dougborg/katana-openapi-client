# Update a service

**PATCH** `https://api.katanamrp.com/v1/services/{id}`

## API Specification Details

**Summary:** Update a service **Description:** Updates the specified service by setting
the values of the parameters passed. Any parameters not provided will be left unchanged.

### Parameters

- **id** (path) *required*: Service id

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
    "additional_info": {
      "type": "string"
    },
    "is_sellable": {
      "type": "boolean"
    },
    "is_archived": {
      "type": "boolean"
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
    "sku": {
      "type": "string"
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

Service updated

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
