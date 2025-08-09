# List all stocktakes

**GET** `https://api.katanamrp.com/v1/stocktakes`

## API Specification Details

**Summary:** List all stocktakes **Description:** Returns a list of stocktakes you’ve
previously created. The stocktakes are returned in sorted order, with the most recent
stocktakes appearing first.

### Parameters

- **ids** (query): Filters stocktakes by an array of IDs
- **stocktake_number** (query): Filters stocktakes by a stocktake number
- **location_id** (query): Filters stocktakes by location
- **status** (query): Filters stocktakes by status
- **stock_adjustment_id** (query): Filters stocktakes by stock adjustment id
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

List all stocktakes

```json
{
  "data": [
    {
      "id": 15,
      "stocktake_number": "STK-15",
      "location_id": 1705,
      "status": "COMPLETED",
      "reason": null,
      "additional_info": "",
      "stocktake_created_date": "2021-12-20T07:50:45.856Z",
      "started_date": "2021-12-20T07:50:58.567Z",
      "completed_date": "2021-12-20T07:51:25.677Z",
      "status_update_in_progress": false,
      "set_remaining_items_as_counted": true,
      "stock_adjustment_id": 118,
      "created_at": "2021-12-20T07:50:45.856Z",
      "updated_at": "2021-12-20T07:51:56.359Z",
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
