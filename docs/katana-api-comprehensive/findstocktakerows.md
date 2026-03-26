# List all stocktake rows

**GET** `https://api.katanamrp.com/v1/stocktake_rows`

List all stocktake rows

## API Specification Details

**Summary:** List all stocktake rows **Description:** Returns a list of stocktake rows
you’ve previously created. The stocktake rows are returned in sorted order, with the
most recent stocktake rows appearing first.

### Parameters

- **ids** (query): Filters stocktake rows by an array of IDs
- **stocktake_ids** (query): Filters stocktake rows by an array of stocktake IDs
- **variant_id** (query): Filters stocktake rows by variant id
- **batch_id** (query): Filters stocktake rows by batch id
- **stock_adjustment_id** (query): Filters stocktake rows by stock adjustment id
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

List stocktake rows

```json
{
  "data": [
    {
      "id": 14,
      "variant_id": 21002,
      "batch_id": null,
      "stocktake_id": 2,
      "notes": null,
      "in_stock_quantity": 10,
      "counted_quantity": null,
      "discrepancy_quantity": null,
      "created_at": "2021-11-22T15:04:37.324Z",
      "updated_at": "2021-11-30T11:56:27.627Z",
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
