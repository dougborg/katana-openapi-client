# Retrieve a sales return row

**GET** `https://api.katanamrp.com/v1/sales_return_rows/{id}`

Retrieve a sales return row

## API Specification Details

**Summary:** Retrieve a sales return row **Description:** Retrieves the details of an
existing sales return row based on ID

### Parameters

- **id** (path) *required*: Sales return row id

### Response Examples

#### 200 Response

Sales return row

```json
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
