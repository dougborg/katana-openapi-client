# Get returnable items

**GET** `https://api.katanamrp.com/v1/sales_orders/{id}/returnable_items`

## API Specification Details

**Summary:** Get returnable items **Description:** Get returnable items for a sales
order

### Parameters

- **id** (path) *required*: Sales order id

### Response Examples

#### 200 Response

Returnable items

```json
[
  {
    "variant_id": 20064030,
    "fulfillment_row_id": 30049219,
    "available_for_return_quantity": "2",
    "net_price_per_unit": "25.0000000000",
    "location_id": 26331,
    "quantity_sold": "2.00000000000000000000"
  },
  {
    "variant_id": 20064030,
    "fulfillment_row_id": 30049245,
    "available_for_return_quantity": "2",
    "net_price_per_unit": "25.0000000000",
    "location_id": 26331,
    "quantity_sold": "2.00000000000000000000"
  }
]
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

#### 500 Response

The server encountered an error. If this persists, please contact support

```json
{
  "statusCode": 500,
  "name": "InternalServerError",
  "message": "Internal Server Error"
}
```
