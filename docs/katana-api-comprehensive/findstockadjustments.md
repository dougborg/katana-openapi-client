# List all stock adjustments

**GET** `https://api.katanamrp.com/v1/stock_adjustments`

List all stock adjustments

## API Specification Details

**Summary:** List all stock adjustments **Description:** Returns a list of stock
adjustments you’ve previously created. The stock adjustments are returned in sorted
order, with the most recent stock adjustments appearing first.

### Parameters

- **ids** (query): Filters stock adjustments by an array of IDs
- **stock_adjustment_number** (query): Filters stock adjustments by a stock adjustment
  number
- **location_id** (query): Filters stock adjustments by location
- **include_deleted** (query): Soft-deleted data is excluded from result set by default.
  Set to true to include it.
- **limit** (query): Used for pagination (default is 50)
- **page** (query): Used for pagination (default is 1)
- **created_at_min** (query): Minimum value for created_at range. Must be compatible
  with ISO 8601 format
- **created_at_max** (query): Maximum value for created_at range. Must be compatible
  with ISO 8601 format
- **updated_at_min** (query): Minimum value for updated_at range. Must be compatible
  with ISO 8601 format
- **updated_at_max** (query): Maximum value for updated_at range. Must be compatible
  with ISO 8601 format

### Response Examples

#### 200 Response

List all stock adjustments

```json
{
  "data": [
    {
      "id": 1,
      "stock_adjustment_number": "SA-1",
      "stock_adjustment_date": "2021-10-06T11:47:13.846Z",
      "location_id": 1,
      "reason": "adjustment reason",
      "additional_info": "adjustment additional info",
      "stock_adjustment_rows": [
        {
          "id": 1,
          "variant_id": 1,
          "quantity": 100,
          "cost_per_unit": 123.45,
          "batch_transactions": [
            {
              "batch_id": 1,
              "quantity": 50
            },
            {
              "batch_id": 2,
              "quantity": 50
            }
          ]
        },
        {
          "id": 2,
          "variant_id": 2,
          "quantity": 150,
          "cost_per_unit": 234.56,
          "batch_transactions": [
            {
              "batch_id": 3,
              "quantity": 150
            }
          ]
        }
      ],
      "created_at": "2021-10-06T11:47:13.846Z",
      "updated_at": "2021-10-06T11:47:13.846Z",
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
