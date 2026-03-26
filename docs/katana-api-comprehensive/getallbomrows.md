# List all BOM rows

**GET** `https://api.katanamrp.com/v1/bom_rows`

## API Specification Details

**Summary:** List all BOM rows **Description:** Returns a list of BOM (Bill of
Materials) rows you've previously created. Product variant BOM consists of ingredient
variants and their quantities.

### Parameters

- **id** (query): Filters BOM rows by ID
- **product_item_id** (query): Filters BOM rows by product item ID
- **product_variant_id** (query): Filters BOM rows by product variant ID
- **ingredient_variant_id** (query): Filters BOM rows by ingredient variant ID
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

List all BOM rows

```json
{
  "data": [
    {
      "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
      "product_item_id": 1,
      "product_variant_id": 1,
      "ingredient_variant_id": 1,
      "quantity": 2,
      "notes": "some notes",
      "rank": 10000,
      "created_at": "2021-04-05T12:00:00.000Z",
      "updated_at": "2021-04-05T12:00:00.000Z"
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
