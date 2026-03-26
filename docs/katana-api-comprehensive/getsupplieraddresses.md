# List all supplier addresses

**GET** `https://api.katanamrp.com/v1/supplier_addresses`

List all supplier addresses

## API Specification Details

**Summary:** List all supplier addresses **Description:** Returns a list of supplier
addresses you’ve previously created. The supplier addresses are returned in sorted
order, with the most recent supplier addresses appearing first.

### Parameters

- **ids** (query): Filters supplier addresses by an array of IDs
- **supplier_ids** (query): Filters supplier addresses by an array of supplier IDs
- **line_1** (query): Filters supplier addresses by a line_1
- **line_2** (query): Filters supplier addresses by a line_2
- **city** (query): Filters supplier addresses by a city
- **state** (query): Filters supplier addresses by a state
- **zip** (query): Filters supplier addresses by a zip
- **country** (query): Filters supplier addresses by a country
- **include_deleted** (query): Soft-deleted data is excluded from result set by default.
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

List all supplier addresses

```json
{
  "data": [
    {
      "id": 2,
      "supplier_id": 12345,
      "line_1": "Line 1",
      "line_2": "Line 2",
      "city": "City",
      "state": "State",
      "zip": "Zip",
      "country": "Country",
      "updated_at": "2020-10-23T10:37:05.085Z",
      "created_at": "2020-10-23T10:37:05.085Z",
      "deleted_at": null
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
