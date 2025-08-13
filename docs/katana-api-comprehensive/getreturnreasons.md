# Get return reasons

**GET** `https://api.katanamrp.com/v1/sales_returns/return_reasons`

## API Specification Details

**Summary:** Get return reasons **Description:** Get return reasons

### Response Examples

#### 200 Response

Return reasons

```json
[
  {
    "id": 137539,
    "name": "Defective or damaged"
  },
  {
    "id": 137540,
    "name": "Incorrect spec"
  },
  {
    "id": 137541,
    "name": "Warranty"
  },
  {
    "id": 137542,
    "name": "Wrong item"
  },
  {
    "id": 137543,
    "name": "Dissatisfied"
  },
  {
    "id": 137544,
    "name": "Other"
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
