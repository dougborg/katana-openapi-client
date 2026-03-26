# List all custom fields collections

**GET** `https://api.katanamrp.com/v1/custom_fields_collections`

List all custom fields collections

## API Specification Details

**Summary:** List all custom fields collections **Description:** Retrieves a list of
custom fields collections

### Response Examples

#### 200 Response

Custom field collection

```json
{
  "data": [
    {
      "id": 1,
      "name": "Collection 1",
      "created_at": "2020-10-23T10:37:05.085Z",
      "updated_at": "2020-10-23T10:37:05.085Z",
      "deleted_at": null
    },
    {
      "id": 2,
      "name": "Collection 2",
      "created_at": "2020-10-23T10:37:05.085Z",
      "updated_at": "2020-10-23T10:37:05.085Z",
      "deleted_at": null
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
