# List all manufacturing orders

**GET** `https://api.katanamrp.com/v1/manufacturing_orders`

List all manufacturing orders

## API Specification Details

**Summary:** List all manufacturing orders **Description:** Returns a list of
manufacturing orders you’ve previously created. The manufacturing orders are returned in
sorted order, with the most recent manufacturing orders appearing first.

### Parameters

- **ids** (query): Filters manufacturing orders by an array of IDs
- **status** (query): Filters manufacturing orders by a status.
- **order_no** (query): Filters manufacturing orders by an order number.
- **location_id** (query): Filters manufacturing orders by location.
- **is_linked_to_sales_order** (query): Filters based on whether a manufacturing order
  is linked to a sales order or not.
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

List all materials

```json
{
  "data": [
    {
      "id": 21400,
      "status": "NOT_STARTED",
      "order_no": "SO-2 / 1",
      "variant_id": 1418016,
      "planned_quantity": 1,
      "actual_quantity": null,
      "batch_transactions": [],
      "location_id": 2327,
      "order_created_date": "2021-09-01T07:49:29.000Z",
      "done_date": null,
      "production_deadline_date": "2021-10-18T08:00:00.000Z",
      "additional_info": "",
      "is_linked_to_sales_order": true,
      "ingredient_availability": "IN_STOCK",
      "total_cost": 0,
      "total_actual_time": 0,
      "total_planned_time": 18000,
      "sales_order_id": 1,
      "sales_order_row_id": 1,
      "sales_order_delivery_deadline": "2021-09-01T07:49:29.813Z",
      "material_cost": 10,
      "created_at": "2021-09-01T07:49:29.813Z",
      "updated_at": "2021-10-15T14:05:47.625Z",
      "subassemblies_cost": 10,
      "operations_cost": 10,
      "deleted_at": null,
      "serial_numbers": [
        {
          "id": 1,
          "transaction_id": "eb4da756-0842-4495-9118-f8135f681234",
          "serial_number": "SN1",
          "resource_type": "Production",
          "resource_id": 2,
          "transaction_date": "2023-02-10T10:06:14.435Z"
        }
      ]
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
