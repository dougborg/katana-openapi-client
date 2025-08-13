# Retrieve a sales order fulfillment

**GET** `https://api.katanamrp.com/v1/sales_order_fulfillments/{id}`

Retrieve a sales order fulfillment

## API Specification Details

**Summary:** Retrieve a sales order fulfillment **Description:** Retrieves the details
of an existing sales order fulfillment based on ID

### Parameters

- **id** (path) *required*: Sales order fulfillment id

### Response Examples

#### 200 Response

Sales order fulfillment

```json
{
  "id": 1,
  "sales_order_id": 1,
  "picked_date": "2020-10-23T10:37:05.085Z",
  "status": "DELIVERED",
  "invoice_status": "NOT_INVOICED",
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
      ],
      "serial_numbers": [
        1
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
