# List all additional costs

**GET** `https://api.katanamrp.com/v1/additional_costs`

List all additional costs

## API Specification Details

**Summary:** List all additional costs **Description:** Returns a list of additional
costs you’ve previously created.

### Parameters

- **ids** (query): Filters additional costs by an array of IDs
- **name** (query): Filters additional costs by a name
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

List all additional costs

```json
{
  "data": [
    {
      "id": 1,
      "name": "Shipping",
      "updated_at": "2023-10-01T10:37:05.085Z",
      "created_at": "2023-10-21T10:37:05.085Z",
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
