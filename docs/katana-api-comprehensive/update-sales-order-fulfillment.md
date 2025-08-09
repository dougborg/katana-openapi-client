# Update a sales order fulfillment

**PATCH** `https://api.katanamrp.com/v1/sales_order_fulfillments/{id}`

Update a sales order fulfillment

## API Specification Details

**Summary:** Update a sales order fulfillment **Description:** Updates the specified
sales order fulfillment by setting the values of the parameters passed. Any parameters
not provided will be left unchanged.

### Parameters

- **id** (path) *required*: Sales order fulfillment id

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "picked_date": {
      "type": "string"
    },
    "status": {
      "type": "string",
      "enum": [
        "DELIVERED",
        "PACKED"
      ]
    },
    "conversion_rate": {
      "type": "number",
      "maximum": 1000000000000,
      "nullable": true
    },
    "packer_id": {
      "type": "number",
      "description": "id of the operator who packed this sales order.\n      It is only shown if the factory has Warehouse Management add-on and Pick & Pack feature has been enabled in the settings."
    },
    "conversion_date": {
      "type": "string",
      "nullable": true
    },
    "tracking_number": {
      "type": "string",
      "maxLength": 256,
      "nullable": true
    },
    "tracking_url": {
      "type": "string",
      "maxLength": 2048,
      "nullable": true
    },
    "tracking_carrier": {
      "type": "string",
      "maxLength": 256,
      "nullable": true
    },
    "tracking_method": {
      "type": "string",
      "maxLength": 2048,
      "nullable": true
    }
  }
}
```

### Response Examples

#### 200 Response

Sales order fulfillment updated

```json
{
  "id": 1,
  "sales_order_id": 1,
  "picked_date": "2020-10-23T10:37:05.085Z",
  "status": "DELIVERED",
  "conversion_rate": 2,
  "conversion_date": "2020-10-23T10:37:05.085Z",
  "tracking_number": "12345678",
  "tracking_url": "https://tracking-number-url",
  "tracking_carrier": "UPS",
  "tracking_method": "ground",
  "packer_id": 1,
  "sales_order_fulfillment_rows": [
    {
      "sales_order_row_id": 1,
      "quantity": 2,
      "batch_transactions": [
        {
          "batch_id": 1,
          "quantity": 2
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
