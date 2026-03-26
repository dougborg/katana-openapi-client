# Retrieve a webhook

**GET** `https://api.katanamrp.com/v1/webhooks/{id}`

## API Specification Details

**Summary:** Retrieve a webhook **Description:** Retrieves the details of an existing
webhook based on ID

### Parameters

- **id** (path) *required*: Webhook id

### Response Examples

#### 200 Response

Webhook

```json
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
