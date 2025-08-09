# Retrieve a manufacturing order operation row

**GET** `https://api.katanamrp.com/v1/manufacturing_order_operation_rows/{id}`

Retrieve a manufacturing order operation row

## API Specification Details

**Summary:** Retrieve a manufacturing order operation row **Description:** Retrieves the
details of an existing manufacturing order operation row.

### Parameters

- **id** (path) *required*: Manufacturing order operaton row id

### Response Examples

#### 200 Response

Manufacturing order operation row

```json
{
  "moOperationRowResponseExample": {
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
