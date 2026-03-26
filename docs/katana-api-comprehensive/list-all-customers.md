# List all customers

**GET** `https://api.katanamrp.com/v1/customers`

## API Specification Details

**Summary:** List all customers **Description:** Returns a list of customers you’ve
previously created. The customers are returned in sorted order, with the most recent
customers appearing first.

### Parameters

- **name** (query): Filters customers by name
- **first_name** (query): Filters customers by first name
- **last_name** (query): Filters customers by last name
- **company** (query): Filters customers by company
- **ids** (query): Filters customers by an array of IDs
- **email** (query): Filters customers by an email
- **phone** (query): Filters customers by a phone number
- **currency** (query): Filters customers by currency
- **reference_id** (query): Filters customers by a reference ID
- **category** (query): Filters customers by a category
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

List of customers

```json
{
  "data": [
    {
      "id": 12345,
      "name": "Luke Skywalker",
      "first_name": "Luke",
      "last_name": "Skywalker",
      "company": "Company",
      "email": "luke.skywalker@example.com",
      "comment": "Luke Skywalker was a Tatooine farmboy who rose from humble beginnings to become one of the\n              greatest Jedi the galaxy has ever known.",
      "discount_rate": 100,
      "phone": "123456",
      "currency": "USD",
      "reference_id": "ref-12345",
      "category": "category-12345",
      "created_at": "2020-10-23T10:37:05.085Z",
      "updated_at": "2020-10-23T10:37:05.085Z",
      "deleted_at": null,
      "default_billing_id": 1,
      "default_shipping_id": 2,
      "addresses": [
        {
          "id": 1,
          "customer_id": 12345,
          "entity_type": "billing",
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
          "created_at": "2020-10-23T10:37:05.085Z"
        },
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
