# List all storage bins

**GET** `https://api.katanamrp.com/v1/bin_locations`

List all storage bins

## API Specification Details

**Summary:** List all storage bins **Description:** Returns a list of storage bins
you’ve previously created. The storage bins are returned in sorted order, with the most
recent storage bin appearing first.

### Parameters

- **location_id** (query): Filters storage bins by location. By storage bins are
  returned for all locations
- **bin_name** (query): Filters storage bins by name
- **include_deleted** (query): Soft-deleted data is excluded from result set by default.
  Set to true to include it.
- **limit** (query): Used for pagination (default is 50)
- **page** (query): Used for pagination (default is 1)

### Response Examples

#### 200 Response

List of storage bins

```json
{
  "data": [
    {
      "id": 12345,
      "name": "Bin-2",
      "location_id": 12346,
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
