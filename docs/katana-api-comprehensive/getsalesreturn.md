# Retrieve a sales return

**GET** `https://api.katanamrp.com/v1/sales_returns/{id}`

Retrieve a sales return

## API Specification Details

**Summary:** Retrieve a sales return **Description:** Retrieves the details of an
existing sales return based on ID

### Parameters

- **id** (path) *required*: Sales return id

### Response Examples

#### 200 Response

Sales return

```json
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
