# List all price list customers

**GET** `https://api.katanamrp.com/v1/price_list_customers`

List all price list customers

## API Specification Details

**Summary:** List all price list customers **Description:** Returns a list of price list
customers you’ve previously created. The price list customers are returned in a sorted
order, with the most recent price list customers appearing first.

### Parameters

- **ids** (query): Filters price list customers by an array of IDs
- **customer_ids** (query): Filters price list customers by an array of customer IDs
- **price_list_ids** (query): Filters price list customers by an array of price list IDs
- **limit** (query): Used for pagination (default is 50)
- **page** (query): Used for pagination (default is 1)

### Response Examples

#### 200 Response

List all price list customers

```json
{
  "data": [
    {
      "id": 9,
      "price_list_id": 2,
      "customer_id": 531,
      "created_at": "2024-06-24T12:35:42.823Z",
      "updated_at": "2024-06-24T12:35:42.823Z"
    },
    {
      "id": 8,
      "price_list_id": 2,
      "customer_id": 530,
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
