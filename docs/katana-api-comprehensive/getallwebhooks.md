# List all webhooks

**GET** `https://api.katanamrp.com/v1/webhooks`

## API Specification Details

**Summary:** List all webhooks **Description:** Returns a list of webhooks you’ve
previously created. The entries are returned in a sorted order, with the most recent
ones appearing first.

### Parameters

- **ids** (query): Filters webhooks by an array of IDs
- **url** (query): Filters webhooks by an url
- **enabled** (query): Filters webhooks by enabled flag
- **limit** (query): Used for pagination (default is 50)
- **page** (query): Used for pagination (default is 1)

### Response Examples

#### 200 Response

List all webhooks

```json
{
  "data": [
    {
      "id": 1,
      "url": "https://katanamrp.com",
      "token": "73f82127d57a2cea",
      "enabled": true,
      "description": "Webhook description",
      "subscribed_events": [
        "sales_order.created"
      ],
      "created_at": "2021-01-28T04:58:40.492Z",
      "updated_at": "2021-01-28T04:58:40.493Z"
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
