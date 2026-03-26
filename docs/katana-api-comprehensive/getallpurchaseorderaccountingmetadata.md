# List all purchase order accounting metadata

**GET** `https://api.katanamrp.com/v1/purchase_order_accounting_metadata`

List all purchase order accounting metadata

## API Specification Details

**Summary:** List all purchase order accounting metadata **Description:** Returns a list
of purchase order accounting metadata entries.

### Parameters

- **purchase_order_id** (query): Filters purchase order accounting metadata by purchase
  order id
- **received_items_group_id** (query): Filters purchase order accounting metadata by
  received items group id
- **limit** (query): Used for pagination (default is 50)
- **page** (query): Used for pagination (default is 1)

### Response Examples

#### 200 Response

List all purchase order accounting metadata entries

```json
{
  "data": [
    {
      "createdAt": "2023-04-17T13:38:07.024Z",
      "id": 35,
      "integrationType": "quickBooks",
      "purchaseOrderId": 311,
      "porReceivedGroupId": 2000037,
      "billId": "1082"
    },
    {
      "createdAt": "2023-04-17T13:38:07.024Z",
      "id": 36,
      "integrationType": "quickBooks",
      "purchaseOrderId": 312,
      "porReceivedGroupId": 2000038,
      "billId": "1083"
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
