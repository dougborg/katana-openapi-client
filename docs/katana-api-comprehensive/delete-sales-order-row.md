# Delete sales order row

**DELETE** `https://api.katanamrp.com/v1/sales_order_rows/{id}`

Delete sales order row

## API Specification Details

**Summary:** Delete sales order row **Description:** Deletes a single sales order row by
id. Rows can be deleted only when the sales order row status is NOT_SHIPPED or PENDING

### Parameters

- **id** (path) *required*: Sales order row id

### Response Examples

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
