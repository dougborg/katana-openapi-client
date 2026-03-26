# List all purchase order rows

**GET** `https://api.katanamrp.com/v1/purchase_order_rows`

List all purchase order rows

## API Specification Details

**Summary:** List all purchase order rows **Description:** Returns a list of purchase
order rows you’ve previously created. The purchase order rows are returned in sorted
order, with the most recent rows appearing first.

### Parameters

- **ids** (query): Filters purchase order rows by an array of IDs
- **purchase_order_id** (query): Filters purchase order rows by purchase order id
- **variant_id** (query): Filters purchase order rows by variant id
- **tax_rate_id** (query): Filters purchase order rows by tax rate id
- **group_id** (query): Filters purchase order rows by group id
- **purchase_uom** (query): Filters purchase order rows by purchase_uom
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

List of purchase order rows

```json
{
  "data": [
    {
      "id": 1,
      "quantity": 1,
      "variant_id": 1,
      "tax_rate_id": 1,
      "price_per_unit": 1.5,
      "price_per_unit_in_base_currency": 1.5,
      "purchase_uom_conversion_rate": 1.1,
      "purchase_uom": "cm",
      "total": 1,
      "total_in_base_currency": 1,
      "created_at": "2020-10-23T10:37:05.085Z",
      "updated_at": "2020-10-23T10:37:05.085Z",
      "deleted_at": null,
      "currency": "USD",
      "conversion_rate": 1.1,
      "conversion_date": "2022-06-20T10:37:05.085Z",
      "received_date": "2022-06-20T10:37:05.085Z",
      "arrival_date": "2022-06-19T10:37:05.085Z",
      "purchase_order_id": 1,
      "landed_cost": 45.5,
      "group_id": 11,
      "batch_transactions": [
        {
          "batch_id": 1,
          "quantity": 10
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
