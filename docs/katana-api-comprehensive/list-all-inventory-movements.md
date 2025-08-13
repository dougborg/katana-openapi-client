# List all inventory movements

**GET** `https://api.katanamrp.com/v1/inventory_movements`

List all inventory movements

## API Specification Details

**Summary:** List all inventory movements **Description:** Returns a list of inventory
movements created by your Katana resources. The inventory movements are returned in
sorted order, with the most recent movements appearing first.

### Parameters

- **ids** (query): Filters inventory movements by an array of IDs
- **variant_ids** (query): Filters inventory movements by an array of variant ids
- **location_id** (query): Filters inventory movements by a location_id
- **resource_type** (query): Filters inventory movements by a resource type
- **resource_id** (query): Filters inventory movements by a resource_id
- **caused_by_order_no** (query): Filters inventory movements by a caused_by_order_no
- **caused_by_resource_id** (query): Filters inventory movements by a
  caused_by_resource_id
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

List all inventory movements

```json
{
  "data": [
    {
      "id": 1,
      "variant_id": 1,
      "location_id": 1,
      "resource_type": "PurchaseOrderRow",
      "resource_id": 1,
      "caused_by_order_no": "PO-1",
      "caused_by_resource_id": 1,
      "movement_date": "2020-10-23T10:37:05.085Z",
      "quantity_change": 1,
      "balance_after": 1,
      "value_per_unit": 1,
      "value_in_stock_after": 1,
      "average_cost_after": 1,
      "rank": 1,
      "created_at": "2020-10-23T10:37:05.085Z",
      "updated_at": "2020-10-23T10:37:05.085Z"
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
