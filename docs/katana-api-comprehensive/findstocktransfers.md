# List all stock transfers

**GET** `https://api.katanamrp.com/v1/stock_transfers`

List all stock transfers

## API Specification Details

**Summary:** List all stock transfers **Description:** Returns a list of stock transfers
you’ve previously created. The stock transfers are returned in sorted order, with the
most recent stock transfers appearing first.

### Parameters

- **ids** (query): Filters stock transfers by an array of IDs
- **stock_transfer_number** (query): Filters stock transfers by a stock transfer number
- **source_location_id** (query): Filters stock transfers by source location
- **target_location_id** (query): Filters stock transfers by target location
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

List all stock transfers

```json
{
  "data": [
    {
      "id": 1,
      "stock_transfer_number": "ST-1",
      "source_location_id": 1,
      "target_location_id": 2,
      "transfer_date": "2021-10-06T11:47:13.846Z",
      "order_created_date": "2021-10-01T11:47:13.846Z",
      "expected_arrival_date": "2021-10-20T11:47:13.846Z",
      "additional_info": "transfer additional info",
      "stock_transfer_rows": [
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
          ],
          "deleted_at": null
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
          ],
          "deleted_at": null
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
