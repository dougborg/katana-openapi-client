# Update a manufacturing order production

**PATCH** `https://api.katanamrp.com/v1/manufacturing_order_productions/{id}`

Update a manufacturing order production

## API Specification Details

**Summary:** Update a manufacturing order production **Description:** Updates the
specified manufacturing order production by setting the values of the parameters passed.
Any parameters not provided will be left unchanged.

### Parameters

- **id** (path) *required*: manufacturing order production id

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "production_date": {
      "type": "string"
    }
  }
}
```

### Response Examples

#### 200 Response

Updated manufacturing order production

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
