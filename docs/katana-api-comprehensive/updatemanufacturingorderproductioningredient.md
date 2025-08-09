# Update a manufacturing order production ingredient

**PATCH** `https://api.katanamrp.com/v1/manufacturing_order_production_ingredients/{id}`

Update a manufacturing order production ingredient

## API Specification Details

**Summary:** Update a manufacturing order production ingredient **Description:** Updates
the specified manufacturing order production ingredient by setting the values of the
parameters passed. Any parameters not provided will be left unchanged. Manufacturing
order production ingredient cannot be updated when the manufacturing order status is
DONE.

### Parameters

- **id** (path) *required*: manufacturing order production ingredient id

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "batch_transactions": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "batch_id",
          "quantity"
        ],
        "properties": {
          "quantity": {
            "type": "number"
          },
          "batch_id": {
            "type": "integer"
          }
        }
      }
    }
  }
}
```

### Response Examples

#### 200 Response

Updated manufacturing order production ingredient

```json
{
  "id": 252,
  "location_id": 321,
  "variant_id": 24001,
  "manufacturing_order_id": 21400,
  "manufacturing_order_recipe_row_id": 20300,
  "production_id": 21300,
  "quantity": 4,
  "production_date": "2023-02-10T10:06:13.047Z",
  "cost": 1
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
