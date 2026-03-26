# List planned demand forecast for variant in location

**GET** `https://api.katanamrp.com/v1/demand_forecasts`

List planned demand forecast for variant in location

## API Specification Details

**Summary:** List planned demand forecast for variant in location **Description:**
Returns planned forecasted demand for a variant in given location.

### Parameters

- **variant_id** (query) *required*: ID of variant for which to retrieve demand forecast
  for.
- **location_id** (query) *required*: ID of location for which to retrieve variant
  demand forecast for.

### Response Examples

#### 200 Response

Planned demand forecast for variant in location.

```json
{
  "variant_id": 1,
  "location_id": 1,
  "in_stock": "100",
  "periods": [
    {
      "period_start": "2024-01-01T00:00:00.000Z",
      "period_end": "2024-01-06T23:59:59.999Z",
      "in_stock": "125",
      "expected": "50",
      "committed": "25"
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
