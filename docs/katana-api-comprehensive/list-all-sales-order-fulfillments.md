# List all sales order fulfillments

**GET** `https://api.katanamrp.com/v1/sales_order_fulfillments`

List all sales order fulfillments

## API Specification Details

**Summary:** List all sales order fulfillments **Description:** Returns a list of sales
order fulfillments you’ve previously created. The sales order fulfillments are returned
in a sorted order, with the most recent sales order fulfillments appearing first.

### Parameters

- **sales_order_id** (query): Filters sales order fulfillments by a sales order id
- **picked_date_min** (query): Filters sales order fulfillments by a picked date min
- **tracking_number** (query): Filters sales order fulfillments by a tracking number
- **tracking_url** (query): Filters sales order fulfillments by a tracking url
- **tracking_carrier** (query): Filters sales order fulfillments by a tracking carrier
- **tracking_method** (query): Filters sales order fulfillments by a tracking method
- **status** (query): Filters sales order fulfillments by a status
- **include_deleted** (query): Soft-deleted data is excluded from result set by default.
  Set to true to include it.
- **limit** (query): Used for pagination (default is 50)
- **page** (query): Used for pagination (default is 1)
- **created_at_min** (query): Minimum value for created_at range. Must be compatible
  with ISO 8601 format
- **created_at_max** (query): Maximum value for created_at range. Must be compatible
  with ISO 8601 format
- **updated_at_min** (query): Minimum value for updated_at range. Must be compatible
  with ISO 8601 format
- **updated_at_max** (query): Maximum value for updated_at range. Must be compatible
  with ISO 8601 format

### Response Examples

#### 200 Response

List all sales orders

```json
{
  "data": [
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
