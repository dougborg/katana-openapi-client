# Update a manufacturing order recipe row

**PATCH** `https://api.katanamrp.com/v1/manufacturing_order_recipe_rows/{id}`

Update a manufacturing order recipe row

## API Specification Details

**Summary:** Update a manufacturing order recipe row **Description:** Updates the
specified manufacturing order recipe row by setting the values of the parameters passed.
Any parameters not provided will be left unchanged. Recipe rows cannot be updated when
the manufacturing order status is DONE.

### Parameters

- **id** (path) *required*: manufacturing order recipe id

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "variant_id": {
      "type": "number"
    },
    "notes": {
      "type": "string"
    },
    "planned_quantity_per_unit": {
      "type": "number"
    },
    "total_actual_quantity": {
      "type": "number"
    },
    "batch_transactions": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "batch_id": {
            "type": "number"
          },
          "quantity": {
            "type": "number"
          }
        }
      }
    }
  }
}
```

### Response Examples

#### 200 Response

New manufacturin order operation row

```json
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
