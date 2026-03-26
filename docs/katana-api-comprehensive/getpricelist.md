# Retrieve a price list

**GET** `https://api.katanamrp.com/v1/price_lists/{id}`

Retrieve a price list

## API Specification Details

**Summary:** Retrieve a price list **Description:** Retrieves the details of an existing
price list based on ID

### Parameters

- **id** (path) *required*: Price list id

### Response Examples

#### 200 Response

Price list

```json
{
  "id": 1,
  "name": "Wholesale price list",
  "is_active": false,
  "created_at": "2020-10-23T10:37:05.085Z",
  "updated_at": "2020-10-23T10:37:05.085Z"
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
