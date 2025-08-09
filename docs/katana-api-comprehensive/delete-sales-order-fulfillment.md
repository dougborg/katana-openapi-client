# Delete a sales order fulfillment

**DELETE** `https://api.katanamrp.com/v1/sales_order_fulfillments/{id}`

Delete a sales order fulfillment

## API Specification Details

**Summary:** Delete a sales order fulfillment **Description:** Deletes a single sales
order fulfillment by id.

### Parameters

- **id** (path) *required*: Sales order fulfillment id

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
