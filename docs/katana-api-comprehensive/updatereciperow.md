# Update a recipe row

**PATCH** `https://api.katanamrp.com/v1/recipe_rows/{id}`

## API Specification Details

**Summary:** Update a recipe row **Description:** (This endpoint is deprecated in favor
of BOM rows) Updates the specified recipe row by setting the values of the parameters
passed. Any parameters not provided will be left unchanged. Since one recipe row can
apply to multiple product variants, updating the row will apply to all objects with the
same recipe_row_id.

### Parameters

- **id** (path) *required*: Recipe row id

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "quantity": {
      "type": "number",
      "minimum": 0,
      "description": "Ingredient quantity"
    },
    "notes": {
      "type": "string",
      "minLength": 255,
      "description": "Notes about recipe row"
    },
    "ingredient_variant_id": {
      "description": "Ingredient variant id",
      "type": "integer"
    }
  }
}
```

### Response Examples

#### 200 Response

Recipe row updated

```json
{
  "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
  "recipe_row_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
  "product_id": 1,
  "product_item_id": 1,
  "product_variant_id": 1,
  "ingredient_variant_id": 1,
  "quantity": 1,
  "notes": "Important recipe row",
  "rank": 10000,
  "created_at": "2021-06-22T10:00:00.000Z",
  "updated_at": "2021-06-22T10:00:00.000Z"
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
