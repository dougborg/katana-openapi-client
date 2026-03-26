# List all price list rows

**GET** `https://api.katanamrp.com/v1/price_list_rows`

List all price list rows

## API Specification Details

**Summary:** List all price list rows **Description:** Returns a list of price list rows
you’ve previously created. The price list rows are returned in a sorted order, with the
most recent price list rows appearing first.

### Parameters

- **ids** (query): Filters price list rows by an array of IDs
- **variant_ids** (query): Filters price list rows by an array of variant IDs
- **price_list_ids** (query): Filters price list rows by an array of price list IDs
- **limit** (query): Used for pagination (default is 50)
- **page** (query): Used for pagination (default is 1)

### Response Examples

#### 200 Response

List all price list rows

```json
{
  "data": [
    {
      "id": 9,
      "price_list_id": 2,
      "variant_id": 531,
      "adjustment_method": "fixed",
      "amount": 5,
      "created_at": "2024-06-24T12:35:42.823Z",
      "updated_at": "2024-06-24T12:35:42.823Z"
    },
    {
      "id": 8,
      "price_list_id": 2,
      "variant_id": 530,
      "adjustment_method": "percentage",
      "amount": 50,
      "created_at": "2024-06-24T09:08:59.018Z",
      "updated_at": "2024-06-24T09:08:59.018Z"
    },
    {
      "id": 10,
      "price_list_id": 2,
      "variant_id": 532,
      "adjustment_method": "markup",
      "amount": 10,
      "created_at": "2024-06-24T09:08:59.018Z",
      "updated_at": "2024-06-24T09:08:59.018Z"
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
