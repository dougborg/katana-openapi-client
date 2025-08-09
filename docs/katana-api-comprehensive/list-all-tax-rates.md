# List all tax rates

**GET** `https://api.katanamrp.com/v1/tax_rates`

## API Specification Details

**Summary:** List all tax rates **Description:** Returns a list of tax rate you’ve
previously created. The tax rate are returned in sorted order, with the most recent tax
rate appearing first.

### Parameters

- **rate** (query): Filters tax rates by rate
- **ids** (query): Filters tax rates by an array of IDs
- **name** (query): Filters tax rates by a name
- **is_default_sales** (query): Filters tax rates by an is_default_sales
- **is_default_purchases** (query): Filters tax rates by an is_default_purchases
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

List of tax rates

```json
{
  "data": [
    {
      "id": 1,
      "name": "15% VAT",
      "rate": 15,
      "is_default_sales": true,
      "is_default_purchases": true,
      "display_name": "15% VAT",
      "created_at": "2020-10-23T10:37:05.085Z",
      "updated_at": "2020-10-23T10:37:05.085Z"
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
