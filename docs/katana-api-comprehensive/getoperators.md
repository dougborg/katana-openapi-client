# Get all operators

**GET** `https://api.katanamrp.com/v1/operators`

## API Specification Details

**Summary:** Get all operators **Description:** Retrieves a list of operators based on
the provided filters.

### Parameters

- **working_area** (query): Filters operators by their working area.
- **resource_id** (query): Filters operators by resource ID.
- **limit** (query): Used for pagination (default is 50)
- **page** (query): Used for pagination (default is 1)

### Response Examples

#### 200 Response

A list of operators

```json
[
  {
    "id": 1,
    "operator_name": "Shopfloor Thomas"
  },
  {
    "id": 2,
    "operator_name": "Warehouse Mike"
  }
]
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
