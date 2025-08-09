# List all customer addresses

**GET** `https://api.katanamrp.com/v1/customer_addresses`

List all customer addresses

## API Specification Details

**Summary:** List all customer addresses **Description:** Returns a list of customer
addresses you’ve previously created. The customer addresses are returned in sorted
order, with the most recent customer addresses appearing first.

### Parameters

- **ids** (query): Filters customer addresses by an array of IDs
- **customer_ids** (query): Filters customer addresses by an array of customer IDs
- **entity_type** (query): Filters customer addresses by a entity_type
- **first_name** (query): Filters customer addresses by a first_name
- **last_name** (query): Filters customer addresses by a last_name
- **company** (query): Filters customer addresses by an company
- **line_1** (query): Filters customer addresses by a line_1
- **line_2** (query): Filters customer addresses by a line_2
- **city** (query): Filters customer addresses by a city
- **state** (query): Filters customer addresses by a state
- **zip** (query): Filters customer addresses by a zip
- **country** (query): Filters customer addresses by a country
- **phone** (query): Filters customer addresses by a phone
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

List all customer addresses

```json
{
  "data": [
    {
      "id": 2,
      "customer_id": 12345,
      "entity_type": "shipping",
      "first_name": "Luke",
      "last_name": "Skywalker",
      "company": "Company",
      "phone": "123456789",
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
