# Create a manufacturing order production

**POST** `https://api.katanamrp.com/v1/manufacturing_order_productions`

Create a manufacturing order production

## API Specification Details

**Summary:** Create a manufacturing order production **Description:** Creates a new
manufacturing order production object.

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "manufacturing_order_id",
    "completed_quantity"
  ],
  "properties": {
    "manufacturing_order_id": {
      "type": "number"
    },
    "completed_quantity": {
      "type": "number",
      "maximum": 1000000000000000
    },
    "completed_date": {
      "type": "string"
    },
    "is_final": {
      "type": "boolean"
    },
    "ingredients": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "manufacturing_order_recipe_row_id",
          "quantity"
        ],
        "properties": {
          "manufacturing_order_recipe_row_id": {
            "type": "number"
          },
          "quantity": {
            "type": "number"
          },
          "batch_transactions": {
            "type": "array",
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "quantity",
                "batch_id"
              ],
              "properties": {
                "quantity": {
                  "maximum": 1000000000000000,
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
    },
    "operations": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "manufacturing_order_operation_id",
          "time"
        ],
        "properties": {
          "manufacturing_order_operation_id": {
            "type": "number"
          },
          "time": {
            "type": "number"
          },
          "batch_transactions": {
            "type": "array",
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "quantity",
                "batch_id"
              ],
              "properties": {
                "quantity": {
                  "maximum": 1000000000000000,
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
    },
    "serial_numbers": {
      "type": "array",
      "items": {
        "type": "number",
        "additionalProperties": false
      }
    }
  }
}
```

### Response Examples

#### 200 Response

New manufacturing order production

```json
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
