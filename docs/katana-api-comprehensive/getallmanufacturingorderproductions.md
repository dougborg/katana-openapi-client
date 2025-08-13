# List all manufacturing orders

**GET** `https://api.katanamrp.com/v1/manufacturing_order_productions`

List all manufacturing orders

## API Specification Details

**Summary:** List all manufacturing orders **Description:** Returns a list of
manufacturing orders you’ve previously created. The manufacturing orders are returned in
sorted order, with the most recent manufacturing orders appearing first.

### Parameters

- **ids** (query): Filters manufacturing order productions by an array of IDs
- **manufacturing_order_ids** (query): Filters manufacturing order productions by
  manufacturing order ids.
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

List all manufacturing order productions

```json
{
  "data": [
    {
      "id": 21300,
      "manufacturing_order_id": 21400,
      "quantity": 2,
      "production_date": "2023-02-10T10:06:13.047Z",
      "created_at": "2023-02-10T10:06:14.425Z",
      "updated_at": "2023-02-10T10:06:15.094Z",
      "deleted_at": null,
      "ingredients": [
        {
          "id": 252,
          "location_id": 321,
          "variant_id": 24764,
          "manufacturing_order_id": 21400,
          "manufacturing_order_recipe_row_id": 20300,
          "production_id": 21300,
          "quantity": 4,
          "production_date": "2023-02-10T10:06:13.047Z",
          "cost": 1,
          "created_at": "2023-02-10T10:06:14.435Z",
          "updated_at": "2023-02-10T10:06:15.070Z",
          "deleted_at": null
        }
      ],
      "operations": [
        {
          "id": 61,
          "location_id": 321,
          "manufacturing_order_id": 21300,
          "manufacturing_order_operation_id": 20400,
          "production_id": 21300,
          "time": 18000,
          "production_date": "2023-02-10T10:06:13.047Z",
          "cost": 50,
          "created_at": "2023-02-10T10:06:14.435Z",
          "updated_at": "2023-02-10T10:06:14.435Z",
          "deleted_at": null
        }
      ],
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
