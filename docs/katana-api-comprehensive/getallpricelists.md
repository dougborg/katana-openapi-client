# List all price lists

**GET** `https://api.katanamrp.com/v1/price_lists`

## API Specification Details

**Summary:** List all price lists **Description:** Returns a list of price lists you’ve
previously created. The price lists are returned in a sorted order, with the most recent
price lists appearing first.

### Parameters

- **ids** (query): Filters price lists by an array of IDs
- **name** (query): Filters price lists by an name
- **is_active** (query): Filters price lists by a status
- **limit** (query): Used for pagination (default is 50)
- **page** (query): Used for pagination (default is 1)

### Response Examples

#### 200 Response

List all price lists

```json
{
  "data": [
    {
      "id": 1,
      "name": "Wholesale price list",
      "is_active": false,
      "created_at": "2020-10-23T10:37:05.085Z",
      "updated_at": "2020-10-23T10:37:05.085Z"
    },
    {
      "id": 2,
      "name": "Premium customers price list",
      "is_active": true,
      "created_at": "2020-10-23T10:37:05.085Z",
      "updated_at": "2020-10-23T10:37:05.085Z"
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
