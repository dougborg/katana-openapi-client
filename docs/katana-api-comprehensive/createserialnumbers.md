# Assign serial numbers to a resource

**POST** `https://api.katanamrp.com/v1/serial_numbers`

Assign serial numbers to a resource

## API Specification Details

**Summary:** Assign serial numbers to a resource **Description:** Assigns the provided
list of serial numbers to the specified resource.

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "resource_type",
    "resource_id",
    "serial_numbers"
  ],
  "properties": {
    "resource_type": {
      "type": "string",
      "enum": [
        "ManufacturingOrder",
        "Production",
        "StockAdjustmentRow",
        "StockTransferRow",
        "PurchaseOrderRow",
        "SalesOrderRow"
      ]
    },
    "resource_id": {
      "type": "integer"
    },
    "serial_numbers": {
      "type": "array",
      "items": {
        "type": "string",
        "additionalProperties": false
      }
    }
  }
}
```

### Response Examples

#### 200 Response

Assigned serial numbers

```json
{
  "failed": [
    {
      "reason": "NOT_IN_STOCK",
      "serial_number": "SN2"
    }
  ],
  "successful": [
    {
      "id": 1,
      "transaction_id": "eb4da756-0842-4495-9118-f8135f681234",
      "serial_number": "SN1",
      "resource_type": "ManufacturingOrder",
      "resource_id": 2,
      "transaction_date": "2020-10-23T10:37:05.085Z",
      "quantity_change": 1
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

#### 404 Response

Make sure data is correct

```json
{
  "statusCode": 404,
  "name": "NotFoundError",
  "message": "Not found"
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
