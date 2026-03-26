# List all manufacturing order recipe rows

**GET** `https://api.katanamrp.com/v1/manufacturing_order_recipe_rows`

List all manufacturing order recipe rows

## API Specification Details

**Summary:** List all manufacturing order recipe rows **Description:** Returns a list of
manufacturing order recipe rows you’ve previously created. The manufacturing order
recipe rows are returned in sorted order, with the most recent manufacturing order
recipe rows appearing first.

### Parameters

- **ids** (query): Filters manufacturing order recipe rows by an array of IDs
- **manufacturing_order_id** (query): Filters manufacturing orders recipe rows by
  manufacturing order id.
- **variant_id** (query): Filters manufacturing orders recipe rows by variant id.
- **ingredient_availability** (query): Filters manufacturing orders by an ingredient
  availability.
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

List all manufacturing order recipe rows

```json
{
  "data": [
    {
      "id": 1,
      "manufacturing_order_id": 1,
      "variant_id": 1,
      "notes": "Pay close attention to this",
      "planned_quantity_per_unit": 1.2,
      "total_actual_quantity": 12,
      "ingredient_availability": "IN_STOCK",
      "ingredient_expected_date": "2021-03-18T12:33:39.957Z",
      "batch_transactions": [
        {
          "batch_id": 11,
          "quantity": 7.4
        },
        {
          "batch_id": 12,
          "quantity": 4.6
        }
      ],
      "cost": 50.4,
      "created_at": "2021-02-18T12:33:39.957Z",
      "updated_at": "2021-02-18T12:33:39.957Z",
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
