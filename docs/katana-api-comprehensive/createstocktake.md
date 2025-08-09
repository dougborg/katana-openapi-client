# Create a stocktake

**POST** `https://api.katanamrp.com/v1/stocktakes`

## API Specification Details

**Summary:** Create a stocktake **Description:** Create a new stocktake object.

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "stocktake_number",
    "location_id"
  ],
  "properties": {
    "stocktake_number": {
      "type": "string",
      "minLength": 1
    },
    "location_id": {
      "type": "integer",
      "maximum": 2147483647
    },
    "reason": {
      "type": "string",
      "maxLength": 540,
      "nullable": true
    },
    "additional_info": {
      "type": "string",
      "nullable": true
    },
    "created_date": {
      "type": "string",
      "minLength": 1
    },
    "set_remaining_items_as_counted": {
      "type": "boolean",
      "default": false
    },
    "stocktake_rows": {
      "type": "array",
      "maxItems": 250,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "variant_id"
        ],
        "properties": {
          "variant_id": {
            "type": "integer",
            "maximum": 2147483647
          },
          "batch_id": {
            "type": "integer",
            "maximum": 2147483647,
            "nullable": true
          },
          "notes": {
            "type": "string",
            "nullable": true,
            "maxLength": 540
          },
          "counted_quantity": {
            "type": "number",
            "minimum": 0,
            "nullable": true
          }
        }
      }
    }
  }
}
```

### Response Examples

#### 200 Response

New stocktake created

```json
{
  "id": 15,
  "stocktake_number": "STK-15",
  "location_id": 1705,
  "status": "NOT_STARTED",
  "reason": "reason",
  "additional_info": "",
  "stocktake_created_date": "2021-12-20T07:50:45.856Z",
  "started_date": "2021-12-20T07:50:58.567Z",
  "completed_date": "2021-12-20T07:51:25.677Z",
  "status_update_in_progress": false,
  "set_remaining_items_as_counted": true,
  "stock_adjustment_id": null,
  "created_at": "2021-12-20T07:50:45.856Z",
  "updated_at": "2021-12-20T07:51:56.359Z",
  "deleted_at": null,
  "stocktake_rows": [
    {
      "id": 90,
      "variant_id": 21002,
      "batch_id": null,
      "stocktake_id": 2,
      "notes": "test 2",
      "in_stock_quantity": null,
      "counted_quantity": 21,
      "discrepancy_quantity": null,
      "created_at": "2022-01-13T14:30:18.174Z",
      "updated_at": "2022-01-13T14:30:18.174Z",
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

#### 422 Response

Check the details property for a specific error message.

```json
{
  "statusCode": 422,
  "name": "UnprocessableEntityError",
  "message": "The request body is invalid.
  See error object `details` property for more info.",
  "code": "VALIDATION_FAILED",
  "details": [
    {
      "path": ".name",
      "code": "maxLength",
      "message": "should NOT be longer than 10 characters",
      "info": {
        "limit": 10
      }
    }
  ]
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
