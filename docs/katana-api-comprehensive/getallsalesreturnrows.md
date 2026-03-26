# List all sales return rows

**GET** `https://api.katanamrp.com/v1/sales_return_rows`

List all sales return rows

## API Specification Details

**Summary:** List all sales return rows **Description:** Returns a list of sales return
rows you've previously created. The sales return rows are returned in a sorted order,
with the most recent sales return row appearing first.

### Parameters

- **ids** (query): Filters sales returns by an array of IDs
- **sales_return_id** (query): Filters sales return rows by a sales return id
- **variant_id** (query): Filters sales return rows by a variant id
- **sales_order_row_id** (query): Filters sales return rows by a sales order row id
- **reason_id** (query): Filters sales return rows by a reason id
- **restock_location_id** (query): Filters sales return rows by a restock location id
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

List all sales return rows

```json
{
  "data": [
    {
      "id": 764,
      "sales_return_id": 1147,
      "variant_id": 19789420,
      "fulfillment_row_id": 30048990,
      "sales_order_row_id": 41899179,
      "quantity": "2.00",
      "net_price_per_unit": "2.0000000000",
      "reason_id": 123,
      "restock_location_id": 26331,
      "batch_transactions": [
        {
          "batch_id": 2288104,
          "quantity": 1
        }
      ],
      "created_at": "2025-02-07T07:51:27.145Z",
      "updated_at": "2025-02-07T07:51:27.145Z"
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
