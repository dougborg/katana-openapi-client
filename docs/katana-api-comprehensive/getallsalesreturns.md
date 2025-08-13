# List all sales returns

**GET** `https://api.katanamrp.com/v1/sales_returns`

List all sales returns

## API Specification Details

**Summary:** List all sales returns **Description:** Returns a list of sales returns
you've previously created. The sales returns are returned in a sorted order, with the
most recent sales return appearing first.

### Parameters

- **ids** (query): Filters sales returns by an array of IDs
- **return_order_no** (query): Filters sales returns by an order number
- **sales_order_id** (query): Filters sales returns by a sales order id
- **status** (query): Filters sales returns by a (return) status
- **refund_status** (query): Filters sales returns by a refund status
- **return_date_min** (query): Minimum value for return_date range. Must be compatible
  with ISO 8601 format
- **return_date_max** (query): Maximum value for return_date range. Must be compatible
  with ISO 8601 format
- **order_created_date_min** (query): Minimum value for order_created_date range. Must
  be compatible with ISO 8601 format
- **order_created_date_max** (query): Maximum value for order_created_date range. Must
  be compatible with ISO 8601 format
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

List all sales returns

```json
{
  "data": [
    {
      "id": 1148,
      "customer_id": 52910306,
      "sales_order_id": 26857265,
      "order_no": "RO-6",
      "return_location_id": 26331,
      "status": "RESTOCKED_ALL",
      "currency": "EUR",
      "return_date": "2025-02-20T11:05:56.738Z",
      "order_created_date": "2025-02-07T07:52:41.237Z",
      "additional_info": "",
      "refund_status": "NOT_REFUNDED",
      "created_at": "2025-02-07T07:52:41.395Z",
      "updated_at": "2025-02-20T11:05:56.753Z"
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

#### 404 Response

Make sure data is correct

```json
{
  "statusCode": 404,
  "name": "NotFoundError",
  "message": "Not found"
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
