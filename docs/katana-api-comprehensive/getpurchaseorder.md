# Retrieve a purchase order

**GET** `https://api.katanamrp.com/v1/purchase_orders/{id}`

Retrieve a purchase order

## API Specification Details

**Summary:** Retrieve a purchase order **Description:** Retrieves the details of an
existing purchase order based on ID

### Parameters

- **id** (path) *required*: Purchase order id
- **extend** (query): Array of objects that need to be added to the response

### Response Examples

#### 200 Response

Purchase order

```json
{
  "id": 1,
  "status": "NOT_RECEIVED",
  "order_no": "PO-1",
  "entity_type": "regular",
  "default_group_id": 9,
  "supplier_id": 1,
  "currency": "USD",
  "expected_arrival_date": "2021-10-13T15:31:48.490Z",
  "order_created_date": "2021-10-13T15:31:48.490Z",
  "additional_info": "Please unpack",
  "location_id": 1,
  "ingredient_availability": null,
  "ingredient_expected_date": null,
  "tracking_location_id": null,
  "total": 1,
  "total_in_base_currency": 1,
  "created_at": "2021-10-13T15:31:48.490Z",
  "updated_at": "2021-10-13T15:31:48.490Z",
  "deleted_at": null,
  "billing_status": "BILLED",
  "last_document_status": "SENDING",
  "purchase_order_rows": [
    {
      "id": 1,
      "quantity": 1,
      "variant_id": 1,
      "tax_rate_id": 1,
      "price_per_unit": 1.5,
      "purchase_uom": "cm",
      "created_at": "2021-10-13T15:31:48.490Z",
      "updated_at": "2021-10-13T15:31:48.490Z",
      "deleted_at": null,
      "currency": "USD",
      "conversion_rate": 1,
      "total": 1,
      "total_in_base_currency": 1,
      "conversion_date": "2021-10-13T15:31:48.490Z",
      "received_date": "2021-10-13T15:31:48.490Z",
      "batch_transactions": [
        {
          "quantity": 1,
          "batch_id": 1
        }
      ],
      "purchase_order_id": 1,
      "purchase_uom_conversion_rate": 1.1,
      "landed_cost": "45.0000000000",
      "group_id": 11
    }
  ],
  "supplier": {
    "id": 1,
    "name": "Luke Skywalker",
    "email": "luke.skywalker@example.com",
    "comment": "Luke Skywalker was a Tatooine farmboy who rose from humble beginnings to become one of the\n              greatest Jedi the galaxy has ever known.",
    "currency": "UAH",
    "created_at": "2020-10-23T10:37:05.085Z",
    "updated_at": "2020-10-23T10:37:05.085Z",
    "deleted_at": null
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
