# Delete a recipe row

**DELETE** `https://api.katanamrp.com/v1/recipe_rows/{id}`

## API Specification Details

**Summary:** Delete a recipe row **Description:** (This endpoint is deprecated in favor
of BOM rows) Deletes a recipes row by recipe_row_id. If one recipe row applies to
multiple product variants then all of them are deleted.

### Parameters

- **id** (path) *required*: Recipe row id

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
