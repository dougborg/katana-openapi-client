# Create price list customers

**POST** `https://api.katanamrp.com/v1/price_list_customers`

Create price list customers

## API Specification Details

**Summary:** Create price list customers **Description:** Add customers to a price list.

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "price_list_id",
    "price_list_customers"
  ],
  "properties": {
    "price_list_id": {
      "type": "number",
      "description": "ID of the price list where the customers will be added",
      "example": 2
    },
    "price_list_customers": {
      "type": "array",
      "description": "List of price list customers to be added",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "customer_id"
        ],
        "properties": {
          "customer_id": {
            "type": "number",
            "description": "ID of the customer"
          }
        }
      }
    }
  },
  "example": {
    "price_list_id": 2,
    "price_list_customers": [
      {
        "customer_id": 223
      },
      {
        "customer_id": 224
      }
    ]
  }
}
```

### Response Examples

#### 200 Response

New price list customer created

```json
[
  {
    "id": 6,
    "price_list_id": 2,
    "customer_id": 223,
    "created_at": "2024-06-25T08:53:38.864Z",
    "updated_at": "2024-06-25T08:53:38.864Z"
  },
  {
    "id": 7,
    "price_list_id": 2,
    "customer_id": 224,
    "created_at": "2024-06-25T08:53:38.864Z",
    "updated_at": "2024-06-25T08:53:38.864Z"
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
