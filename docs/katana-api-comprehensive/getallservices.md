# List all services

**GET** `https://api.katanamrp.com/v1/services`

## API Specification Details

**Summary:** List all services **Description:** Returns a list of services you’ve
previously created. The services are returned in sorted order, with the most recent
services appearing first.

### Parameters

- **ids** (query): Filters services by an array of IDs
- **name** (query): Filters services by a name
- **uom** (query): Filters services by a uom
- **is_sellable** (query): Filters services by ability to sell
- **category_name** (query): Filters services by a category name
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

List all services

```json
{
  "data": [
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
