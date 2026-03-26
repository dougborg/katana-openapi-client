# Retrieve the current factory

**GET** `https://api.katanamrp.com/v1/factory`

Retrieve the current factory

## API Specification Details

**Summary:** Retrieve the current factory **Description:** Returns the general
information about the factory.

### Response Examples

#### 200 Response

Factory

```json
{
  "legal_address": {
    "line_1": "Peetri 7",
    "line_2": "Apartment 1",
    "city": "Tallinn",
    "state": "State",
    "zip": "10411",
    "country": "Estonia"
  },
  "legal_name": "Legal name",
  "display_name": "Display name",
  "base_currency_code": "USD",
  "default_so_delivery_time": "2021-10-13T15:31:48.490Z",
  "default_po_lead_time": "2021-10-13T15:31:48.490Z",
  "default_manufacturing_location_id": 1,
  "default_purchases_location_id": 1,
  "default_sales_location_id": 1,
  "inventory_closing_date": "2022-01-28T23:59:59.000Z"
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
