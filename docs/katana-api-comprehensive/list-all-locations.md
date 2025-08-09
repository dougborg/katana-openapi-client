# List all locations

**GET** `https://api.katanamrp.com/v1/locations`

## API Specification Details

**Summary:** List all locations **Description:** Returns a list of locations you’ve
previously created. The locations are returned in sorted order, with the most recent
locations appearing first.

### Parameters

- **ids** (query): Filters locations by an array of IDs
- **name** (query): Filters locations by a name
- **legal_name** (query): Filters locations by a legal_name
- **address_id** (query): Filters locations by an address_id
- **sales_allowed** (query): Filters locations by a sales_allowed
- **manufacturing_allowed** (query): Filters locations by a manufacturing_allowed
- **purchases_allowed** (query): Filters locations by a purchases_allowed
- **rank** (query): Filters locations by a rank
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

List all locations

```json
{
  "data": [
    {
      "id": 1,
      "name": "Main location",
      "legal_name": "Amazon",
      "address_id": 1,
      "address": {
        "id": 1,
        "city": "New York",
        "country": "United States",
        "line_1": "10 East 20th Example St",
        "line_2": "",
        "state": "New York",
        "zip": "10000"
      },
      "is_primary": true,
      "sales_allowed": true,
      "purchase_allowed": true,
      "manufacturing_allowed": true,
      "created_at": "2020-10-23T10:37:05.085Z",
      "updated_at": "2020-10-23T10:37:05.085Z",
      "deleted_at": null
    },
    {
      "id": 2,
      "name": "Secondary location",
      "legal_name": "Amazon",
      "address_id": null,
      "address": null,
      "is_primary": false,
      "sales_allowed": false,
      "purchase_allowed": true,
      "manufacturing_allowed": false,
      "created_at": "2020-10-23T10:37:05.085Z",
      "updated_at": "2020-10-23T10:37:05.085Z",
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
