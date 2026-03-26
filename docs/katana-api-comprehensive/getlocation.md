# Retrieve a location

**GET** `https://api.katanamrp.com/v1/locations/{id}`

## API Specification Details

**Summary:** Retrieve a location **Description:** Retrieves the details of an existing
location based on ID.

### Parameters

- **id** (path) *required*: Location id

### Response Examples

#### 200 Response

Location

```json
{
  "id": 1,
  "name": "Main location",
  "legal_name": "Amazon",
  "address_id": 1,
  "address": {
    "id": 1,
    "city": "New York",
    "country": "United States",
    "line_1": "10 East 20th Example St",
    "line_2": "",
    "state": "New York",
    "zip": "10000"
  },
  "is_primary": true,
  "sales_allowed": true,
  "purchase_allowed": true,
  "manufacturing_allowed": true,
  "created_at": "2020-10-23T10:37:05.085Z",
  "updated_at": "2020-10-23T10:37:05.085Z",
  "deleted_at": null
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
