# Retrieve a sales order row

**GET** `https://api.katanamrp.com/v1/sales_order_rows/{id}`

Retrieve a sales order row

## API Specification Details

**Summary:** Retrieve a sales order row **Description:** Retrieves the details of an
existing sales order row.

### Parameters

- **id** (path) *required*: Sales order row id
- **extend** (query): Array of objects that need to be added to the response

### Response Examples

#### 200 Response

Sales order row

```json
{
  "sales_order_id": 1,
  "id": 1,
  "quantity": 1,
  "variant_id": 1,
  "tax_rate_id": 1,
  "location_id": 1,
  "price_per_unit": 150,
  "total_discount": "10.00",
  "price_per_unit_in_base_currency": 330,
  "conversion_rate": 2,
  "conversion_date": "2020-10-23T10:37:05.085Z",
  "product_availability": "EXPECTED",
  "product_expected_date": "2020-10-23T10:37:05.085Z",
  "created_at": "2020-10-23T10:37:05.085Z",
  "updated_at": "2020-10-23T10:37:05.085Z",
  "deleted_at": null,
  "total": 165,
  "total_in_base_currency": 330,
  "linked_manufacturing_order_id": 1,
  "attributes": [
    {
      "key": "key",
      "value": "value"
    }
  ],
  "batch_transactions": [
    {
      "batch_id": 1,
      "quantity": 10
    }
  ],
  "serial_numbers": [
    1
  ],
  "variant": {
    "id": 1,
    "sku": "EM",
    "sales_price": 40,
    "product_id": 1,
    "purchase_price": 0,
    "type": "product",
    "created_at": "2020-10-23T10:37:05.085Z",
    "updated_at": "2020-10-23T10:37:05.085Z",
    "internal_barcode": "0316",
    "registered_barcode": "0785223088",
    "supplier_item_codes": [
      "978-0785223085",
      "0785223088"
    ],
    "config_attributes": [
      {
        "config_name": "Type",
        "config_value": "Standard"
      }
    ]
  }
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
