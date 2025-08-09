# Delete a stock adjustment

**DELETE** `https://api.katanamrp.com/v1/stock_adjustments/{id}`

Delete a stock adjustment

## API Specification Details

**Summary:** Delete a stock adjustment **Description:** Deletes a single stock
adjustment by id.

### Parameters

- **id** (path) *required*: Stock adjustment id

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
