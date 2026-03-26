# Create a BOM row

**POST** `https://api.katanamrp.com/v1/bom_rows/batch/create`

## API Specification Details

**Summary:** Create many BOM rows **Description:** Create BOM rows for a product.

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "rows"
  ],
  "properties": {
    "data": {
      "type": "array",
      "minItems": 1,
      "maxItems": 250,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "product_item_id",
          "product_variant_id",
          "ingredient_variant_id"
        ],
        "properties": {
          "product_item_id": {
            "type": "number",
            "minimum": 1,
            "maximum": 2147483647
          },
          "product_variant_id": {
            "type": "number",
            "minimum": 1,
            "maximum": 2147483647
          },
          "ingredient_variant_id": {
            "type": "integer",
            "minimum": 1,
            "maximum": 2147483647
          },
          "quantity": {
            "type": "number",
            "minimum": 0,
            "maximum": 100000000000000000,
            "nullable": true
          },
          "notes": {
            "type": "string",
            "minLength": 0,
            "maxLength": 255,
            "nullable": true
          }
        }
      }
    }
  }
}
```

### Response Examples

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
