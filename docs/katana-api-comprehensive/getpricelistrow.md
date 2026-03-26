# Retrieve a price list row

**GET** `https://api.katanamrp.com/v1/price_list_rows/{id}`

Retrieve a price list row

## API Specification Details

**Summary:** Retrieve a price list row **Description:** Retrieves the details of an
existing price list row based on ID

### Parameters

- **id** (path) *required*: Price list row id

### Response Examples

#### 200 Response

Price list row

```json
{
  "id": 6,
  "price_list_id": 2,
  "variant_id": 223,
  "adjustment_method": "percentage",
  "amount": 50,
  "created_at": "2024-06-25T08:53:38.864Z",
  "updated_at": "2024-06-25T09:13:56.602Z"
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
