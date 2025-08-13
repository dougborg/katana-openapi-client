# List current batch stock

**GET** `https://api.katanamrp.com/v1/batch_stocks`

List current batch stock

## API Specification Details

**Summary:** List current batch stock **Description:** Returns a list for current batch
stock. The inventory is returned in sorted order, base on location_id ASC, variant_id
ASC, batch_id DESC.

### Parameters

- **batch_id** (query): Filters stock by a valid batch id
- **batch_number** (query): Filters stock by a valid batch number
- **location_id** (query): Filters stock by a valid location id
- **variant_id** (query): Filters stock by a valid variant id
- **batch_barcode** (query): Filter stock by batch barcode
- **batch_created_at_max** (query): Maximum value for batch_created_at range. Must be
  compatible with ISO 8601 format
- **batch_created_at_min** (query): Minimum value for batch_created_at range. Must be
  compatible with ISO 8601 format
- **include_empty** (query): Include empty batches in result
- **limit** (query): Used for pagination (default is 50)
- **page** (query): Used for pagination (default is 1)

### Response Examples

#### 200 Response

List batch stock

```json
{
  "data": [
    {
      "batch_id": 1109,
      "batch_number": "B2",
      "batch_created_date": "2020-09-29T11:40:29.628Z",
      "expiration_date": "2021-04-30T10:35:00.000Z",
      "location_id": 1433,
      "variant_id": 350880,
      "quantity_in_stock": "10.00000",
      "batch_barcode": "0317"
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
