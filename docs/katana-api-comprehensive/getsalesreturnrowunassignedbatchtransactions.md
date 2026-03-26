# Retrieve unassigned batch transactions for a sales return row

**GET**
`https://api.katanamrp.com/v1/sales_return_rows/{id}/unassigned_batch_transactions`

Retrieve unassigned batch transactions for a sales return row

## API Specification Details

**Summary:** Retrieve unassigned batch transactions for a sales return row
**Description:** Retrieves the unassigned batch transactions for a sales return row
based on sales return row id

### Parameters

- **id** (path) *required*: Sales return row id

### Response Examples

#### 200 Response

Unassigned batch transactions for a sales return row

```json
{
  "batch_id": 2288104,
  "quantity": "1.00",
  "batch_number": "b1",
  "batch_created_date": "2025-01-23T08:29:34.913Z",
  "batch_expiration_date": null,
  "barcode": "1234567890"
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
