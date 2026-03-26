# List all suppliers

**GET** `https://api.katanamrp.com/v1/suppliers`

## API Specification Details

**Summary:** List all suppliers **Description:** Returns a list of suppliers you’ve
previously created. The suppliers are returned in sorted order, with the most recent
suppliers appearing first.

### Parameters

- **name** (query): Filters suppliers by name
- **ids** (query): Filters suppliers by an array of IDs
- **email** (query): Filters suppliers by an email
- **phone** (query): Filters suppliers by a phone number
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

List of suppliers

```json
{
  "data": [
    {
      "id": 1,
      "name": "Luke Skywalker",
      "email": "luke.skywalker@example.com",
      "phone": "123456",
      "comment": "Luke Skywalker was a Tatooine farmboy who rose from humble beginnings to become one of the\n              greatest Jedi the galaxy has ever known.",
      "currency": "UAH",
      "created_at": "2020-10-23T10:37:05.085Z",
      "updated_at": "2020-10-23T10:37:05.085Z",
      "deleted_at": null,
      "default_address_id": 1,
      "addresses": [
        {
          "id": 1,
          "supplier_id": 12345,
          "line_1": "Line 1",
          "line_2": "Line 2",
          "city": "City",
          "state": "State",
          "zip": "Zip",
          "country": "Country",
          "updated_at": "2020-10-23T10:37:05.085Z",
          "created_at": "2020-10-23T10:37:05.085Z"
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
