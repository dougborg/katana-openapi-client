# Retrieve a service

**GET** `https://api.katanamrp.com/v1/services/{id}`

## API Specification Details

**Summary:** Retrieve a service **Description:** Retrieves the details of an existing
service based on ID.

### Parameters

- **id** (path) *required*: Service id

### Response Examples

#### 200 Response

Details of an existing service

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
