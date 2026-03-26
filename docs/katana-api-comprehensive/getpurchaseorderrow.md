# Retrieve a purchase order row

**GET** `https://api.katanamrp.com/v1/purchase_order_rows/{id}`

Retrieve a purchase order row

## API Specification Details

**Summary:** Retrieve a purchase order row **Description:** Retrieves the details of an
existing purchase order row based on ID

### Parameters

- **id** (path) *required*: Purchase order row id

### Response Examples

#### 200 Response

A purchase order row

```json
{
  "id": 1,
  "quantity": 1,
  "variant_id": 1,
  "tax_rate_id": 1,
  "price_per_unit": 1.5,
  "price_per_unit_in_base_currency": 1.5,
  "purchase_uom_conversion_rate": 1.1,
  "purchase_uom": "cm",
  "total": 1,
  "total_in_base_currency": 1,
  "created_at": "2020-10-23T10:37:05.085Z",
  "updated_at": "2020-10-23T10:37:05.085Z",
  "deleted_at": null,
  "currency": "USD",
  "conversion_rate": 1,
  "conversion_date": "2022-06-20T10:37:05.085Z",
  "received_date": "2022-06-20T10:37:05.085Z",
  "arrival_date": "2022-06-19T10:37:05.085Z",
  "purchase_order_id": 1,
  "landed_cost": 45.5,
  "group_id": 11,
  "batch_transactions": [
    {
      "batch_id": 1,
      "quantity": 10
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
