# List all sales order accounting metadata

**GET** `https://api.katanamrp.com/v1/sales_order_accounting_metadata`

List all sales order accounting metadata

## API Specification Details

**Summary:** List all sales order accounting metadata **Description:** Returns a list of
sales order accounting metadata entries.

### Parameters

- **sales_order_id** (query): Filters sales order accounting metadata by sales order id
- **fulfillment_id** (query): Filters sales order accounting metadata by fulfillment id
- **limit** (query): Used for pagination (default is 50)
- **page** (query): Used for pagination (default is 1)

### Response Examples

#### 200 Response

List all sales order accounting metadata entries

```json
{
  "data": [
    {
      "id": 20,
      "sales_order_id": 91,
      "fulfillment_id": 44,
      "invoice_id": "977",
      "integration_type": "quickBooks",
      "created_at": "2023-02-15T15:25:00.000Z"
    },
    {
      "id": 21,
      "sales_order_id": 91,
      "fulfillment_id": 45,
      "invoice_id": "978",
      "integration_type": "quickBooks",
      "created_at": "2023-02-15T15:30:00.000Z"
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
