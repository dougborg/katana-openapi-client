# Delete a product operation row

**DELETE** `https://api.katanamrp.com/v1/product_operation_rows/{id}`

Delete a product operation row

## API Specification Details

**Summary:** Delete a product operation row **Description:** Deletes a product operation
row by product_operation_row_id. If one product operation row applies to multiple
product variants then all of them are deleted.

### Parameters

- **id** (path) *required*: Product operation row id

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
