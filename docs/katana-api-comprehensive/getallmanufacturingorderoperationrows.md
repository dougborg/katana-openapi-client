# List all manufacturing order operation rows

**GET** `https://api.katanamrp.com/v1/manufacturing_order_operation_rows`

List all manufacturing order operation rows

## API Specification Details

**Summary:** List all manufacturing order operation rows **Description:** Returns a list
of manufacturing order operation rows you’ve previously created. The manufacturing order
operation rows are returned in sorted order, with the most recent manufacturing order
operation rows appearing first.

### Parameters

- **ids** (query): Filters manufacturing order operation rows by an array of IDs
- **status** (query): Filters manufacturing orders by a status.
- **manufacturing_order_id** (query): Filters manufacturing orders by location.
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

List all manufacturing order operation rows

```json
{
  "data": [
    {
      "id": 1,
      "status": "IN_PROGRESS",
      "type": "process",
      "rank": 1,
      "manufacturing_order_id": 1,
      "operation_id": 1,
      "operation_name": "Pack",
      "resource_id": 1,
      "resource_name": "Table",
      "assigned_operators": [
        {
          "operator_id": 1,
          "name": "Pack",
          "deleted_at": null
        }
      ],
      "completed_by_operators": [],
      "active_operator_id": 1,
      "planned_time_per_unit": 1,
      "planned_time_parameter": 1,
      "total_actual_time": 1,
      "planned_cost_per_unit": 1,
      "total_actual_cost": 1,
      "cost_per_hour": 1,
      "cost_parameter": 1,
      "group_boundary": 1000,
      "is_status_actionable": true,
      "completed_at": "2020-10-23T10:37:05.085Z",
      "created_at": "2020-10-23T10:37:05.085Z",
      "updated_at": "2020-10-23T10:37:05.085Z",
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
